"""
PDF Processor with OCR support for Hebrew and English.
Handles both text-based PDFs and scanned/image-based documents.
"""
import io
import os
import re
from typing import Optional

import fitz  # PyMuPDF
import pdfplumber

from api.processors.base import Processor, PageContent, ProcessedPage
from api.config.schemas import OCRConfig


# Hebrew-capable font paths (in order of preference)
HEBREW_FONT_PATHS = [
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def _find_hebrew_font() -> Optional[str]:
    """Find a system font that supports Hebrew characters."""
    for font_path in HEBREW_FONT_PATHS:
        if os.path.exists(font_path):
            return font_path
    return None


def _prepare_text_for_pdf(text: str) -> str:
    """
    Prepare text for PDF output by converting to visual order for RTL display.

    PyMuPDF's TextWriter reverses Hebrew character sequences during rendering.
    To counteract this and achieve correct RTL visual display, we need to:
    1. Pre-reverse Hebrew character sequences (TextWriter will reverse them back)
    2. Reverse word order in lines containing Hebrew (for RTL visual order)

    Args:
        text: Text in logical order

    Returns:
        Text converted to visual-order for PDF rendering
    """
    def reverse_hebrew_chars(s: str) -> str:
        """Reverse Hebrew character sequences in a string."""
        result = []
        i = 0
        while i < len(s):
            if '\u0590' <= s[i] <= '\u05FF':
                # Collect Hebrew sequence
                hebrew_seq = []
                while i < len(s) and '\u0590' <= s[i] <= '\u05FF':
                    hebrew_seq.append(s[i])
                    i += 1
                # Pre-reverse so TextWriter's reversal gives correct order
                result.append(''.join(reversed(hebrew_seq)))
            else:
                result.append(s[i])
                i += 1
        return ''.join(result)

    def process_line(line: str) -> str:
        # Check if line contains Hebrew - if so, treat as RTL line
        if not re.search(r'[\u0590-\u05FF]', line):
            return line  # No Hebrew, return as-is

        # For RTL lines:
        # 1. Pre-reverse Hebrew characters (counteracts TextWriter's reversal)
        # 2. Reverse word order (for visual RTL display)

        # Split on whitespace, preserving the whitespace
        tokens = re.split(r'(\s+)', line)

        # Pre-reverse Hebrew chars in each token
        processed_tokens = [reverse_hebrew_chars(token) for token in tokens]

        # Reverse token order for RTL visual display
        reversed_tokens = list(reversed(processed_tokens))
        return ''.join(reversed_tokens)

    # Process each line
    lines = text.split('\n')
    return '\n'.join(process_line(line) for line in lines)


class PDFProcessor(Processor):
    """PDF processor using PyMuPDF, pdfplumber, and optional OCR."""

    supported_mimes = ["application/pdf"]

    def __init__(self, ocr_config: Optional[OCRConfig] = None):
        """
        Initialize processor with OCR configuration.

        Args:
            ocr_config: OCR settings (languages, DPI, etc.)
        """
        self.ocr_config = ocr_config or OCRConfig()
        self._ocr_reader = None  # Lazy loaded

    @staticmethod
    def _fix_rtl_visual_order(text: str) -> str:
        """
        Fix Hebrew text stored in visual order (reversed letters).

        Some PDFs store RTL text in visual order where each Hebrew word
        has its letters reversed. This function detects and fixes this.

        Args:
            text: Text that may have reversed Hebrew words

        Returns:
            Text with Hebrew words corrected to logical order
        """
        # Pattern matches sequences of Hebrew characters (including apostrophe for names like סז'ין)
        hebrew_pattern = r"([\u0590-\u05FF]['\u0590-\u05FF]*)"

        def reverse_match(match: re.Match) -> str:
            return match.group(1)[::-1]

        return re.sub(hebrew_pattern, reverse_match, text)

    @staticmethod
    def combine_pages_with_markers(pages: list[PageContent]) -> str:
        """
        Combine extracted pages into single text with page markers.

        Adds visual page separators to maintain page structure for
        downstream processing and PDF reassembly.

        Args:
            pages: List of extracted page content

        Returns:
            Combined text with page markers
        """
        total_pages = len(pages)
        result_parts = []

        for page in pages:
            # Add page marker
            marker = f"\n{'=' * 60}\nעמוד {page.page_number} מתוך {total_pages}\n{'=' * 60}\n"
            result_parts.append(marker)
            result_parts.append(page.text)

        return "\n".join(result_parts)

    def extract_text(
        self,
        file: bytes,
        force_ocr: bool = False,
    ) -> list[PageContent]:
        """
        Extract text from PDF.

        Automatically detects if PDF has text layer or needs OCR.

        Args:
            file: PDF file bytes
            force_ocr: Force OCR even if text layer exists

        Returns:
            List of PageContent with extracted text per page
        """
        if force_ocr and self.ocr_config.enabled:
            pages = self._extract_with_ocr(file)
            # Mark as forced OCR
            for page in pages:
                if page.metadata:
                    page.metadata["is_image_based"] = True
            return pages

        # Check if PDF has extractable text
        has_text = self._has_text_layer(file)
        if has_text:
            return self._extract_with_pymupdf(file)
        elif self.ocr_config.enabled:
            pages = self._extract_with_ocr(file)
            # Mark as image-based PDF
            for page in pages:
                if page.metadata:
                    page.metadata["is_image_based"] = True
            return pages
        else:
            # OCR disabled but no text layer - return empty with warning
            pages = self._extract_with_pymupdf(file)
            for page in pages:
                if page.metadata is None:
                    page.metadata = {}
                page.metadata["is_image_based"] = True
                page.metadata["warning"] = "PDF appears to be image-based but OCR is disabled"
            return pages

    def _has_text_layer(self, file: bytes) -> bool:
        """
        Check if PDF has extractable text or is image-based.

        Args:
            file: PDF file bytes

        Returns:
            True if text layer exists, False if OCR needed
        """
        doc = fitz.open(stream=file, filetype="pdf")
        total_text = ""

        try:
            for page in doc:
                total_text += page.get_text().strip()
        finally:
            doc.close()

        return len(total_text) > self.ocr_config.min_text_threshold

    def _extract_with_pymupdf(self, file: bytes) -> list[PageContent]:
        """
        Extract text using PyMuPDF (for PDFs with text layer).

        Automatically fixes RTL visual-order text where Hebrew letters
        are stored in reversed order.
        """
        pages = []
        doc = fitz.open(stream=file, filetype="pdf")

        try:
            for page_num, page in enumerate(doc):
                raw_text = page.get_text()
                # Fix RTL visual-order text (Hebrew letters may be reversed)
                text = self._fix_rtl_visual_order(raw_text)
                blocks = page.get_text("blocks")

                pages.append(PageContent(
                    page_number=page_num + 1,
                    text=text,
                    metadata={
                        "blocks": blocks,
                        "width": page.rect.width,
                        "height": page.rect.height,
                        "extraction_method": "pymupdf",
                    }
                ))
        finally:
            doc.close()

        # Enhance with table extraction from pdfplumber
        self._add_tables(file, pages)

        return pages

    def _extract_with_ocr(self, file: bytes) -> list[PageContent]:
        """
        Extract text using OCR (for scanned/image-based PDFs).

        Uses Tesseract with Hebrew and English support.
        Falls back gracefully if OCR dependencies are not installed.
        """
        try:
            import pytesseract
            from pdf2image import convert_from_bytes
        except ImportError as e:
            # OCR not available - return empty pages with warning
            doc = fitz.open(stream=file, filetype="pdf")
            pages = []
            try:
                for page_num in range(len(doc)):
                    pages.append(PageContent(
                        page_number=page_num + 1,
                        text="",
                        metadata={
                            "extraction_method": "ocr_unavailable",
                            "warning": f"OCR dependencies not installed: {e}. "
                                       "Install with: pip install pytesseract pdf2image && "
                                       "apt-get install tesseract-ocr tesseract-ocr-heb",
                        }
                    ))
            finally:
                doc.close()
            return pages

        # Convert PDF pages to images
        images = convert_from_bytes(file, dpi=self.ocr_config.dpi)

        # Map language codes to Tesseract format
        lang_map = {"he": "heb", "en": "eng"}
        tesseract_langs = "+".join(
            lang_map.get(lang, lang) for lang in self.ocr_config.languages
        )

        pages = []
        for page_num, image in enumerate(images):
            # Run OCR with Tesseract
            page_text = pytesseract.image_to_string(
                image,
                lang=tesseract_langs,
            )

            pages.append(PageContent(
                page_number=page_num + 1,
                text=page_text,
                metadata={
                    "extraction_method": "ocr_tesseract",
                    "languages": tesseract_langs,
                    "width": image.width,
                    "height": image.height,
                }
            ))

        return pages

    def _add_tables(self, file: bytes, pages: list[PageContent]) -> None:
        """Add table data to pages using pdfplumber."""
        try:
            with pdfplumber.open(io.BytesIO(file)) as pdf:
                for i, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    if tables and i < len(pages):
                        if pages[i].metadata is None:
                            pages[i].metadata = {}
                        pages[i].metadata["tables"] = tables
        except Exception:
            # pdfplumber table extraction is optional
            pass

    def reassemble(self, pages: list[ProcessedPage]) -> bytes:
        """
        Reassemble PDF with processed text.

        Creates a text-based PDF with the processed content.
        Uses a Hebrew-capable font for proper rendering of Hebrew text.
        Handles long text by creating continuation pages as needed.
        """
        doc = fitz.open()

        # Find a Hebrew-capable font and create Font object
        font_path = _find_hebrew_font()
        if font_path:
            font = fitz.Font(fontfile=font_path)
        else:
            font = fitz.Font("helv")

        # Page layout constants
        PAGE_WIDTH = 612  # Letter size
        PAGE_HEIGHT = 792
        MARGIN_LEFT = 50
        MARGIN_TOP = 50
        MARGIN_BOTTOM = 50
        FONTSIZE = 10
        LINE_HEIGHT = FONTSIZE * 1.2  # Standard line spacing

        max_y = PAGE_HEIGHT - MARGIN_BOTTOM

        for page_data in pages:
            text = page_data.processed_text
            if not text.strip():
                # Create empty page for empty text
                doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
                continue

            lines = text.split('\n')
            line_idx = 0

            while line_idx < len(lines):
                # Create a new PDF page
                new_page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)

                # Use TextWriter for better text control
                tw = fitz.TextWriter(new_page.rect)

                y = MARGIN_TOP + FONTSIZE  # Start position

                while line_idx < len(lines) and y < max_y:
                    line = lines[line_idx]

                    # Prepare text for PDF (reverse Hebrew for proper RTL display)
                    pdf_line = _prepare_text_for_pdf(line)

                    # Insert text at position using Font object
                    tw.append(
                        (MARGIN_LEFT, y),
                        pdf_line,
                        fontsize=FONTSIZE,
                        font=font,
                    )

                    y += LINE_HEIGHT
                    line_idx += 1

                # Write all text to page
                tw.write_text(new_page)

        # Save to bytes
        output = io.BytesIO()
        doc.save(output)
        doc.close()

        return output.getvalue()


def create_processor(ocr_config: Optional[OCRConfig] = None) -> PDFProcessor:
    """Factory function to create PDF processor."""
    return PDFProcessor(ocr_config=ocr_config)
