"""
PDF Processor with OCR support for Hebrew and English.
Handles both text-based PDFs and scanned/image-based documents.
"""
import io
import re
from typing import Optional

import fitz  # PyMuPDF
import pdfplumber

from api.processors.base import Processor, PageContent, ProcessedPage
from api.config.schemas import OCRConfig


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

        For v1, creates a simple text-based PDF with the processed content.
        """
        doc = fitz.open()

        for page_data in pages:
            # Create new page
            new_page = doc.new_page(
                width=612,  # Letter size
                height=792
            )

            # Insert processed text
            text_rect = fitz.Rect(50, 50, 562, 742)
            new_page.insert_textbox(
                text_rect,
                page_data.processed_text,
                fontsize=10,
                fontname="helv",
            )

        # Save to bytes
        output = io.BytesIO()
        doc.save(output)
        doc.close()

        return output.getvalue()


def create_processor(ocr_config: Optional[OCRConfig] = None) -> PDFProcessor:
    """Factory function to create PDF processor."""
    return PDFProcessor(ocr_config=ocr_config)
