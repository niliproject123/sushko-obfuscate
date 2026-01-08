"""
PDF Processor with OCR support for Hebrew and English.
Handles both text-based PDFs and scanned/image-based documents.
"""
import io
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
            return self._extract_with_ocr(file)

        # Check if PDF has extractable text
        if self._has_text_layer(file):
            return self._extract_with_pymupdf(file)
        elif self.ocr_config.enabled:
            return self._extract_with_ocr(file)
        else:
            # OCR disabled but no text layer - return empty with warning
            return self._extract_with_pymupdf(file)

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
        """
        pages = []
        doc = fitz.open(stream=file, filetype="pdf")

        try:
            for page_num, page in enumerate(doc):
                text = page.get_text()
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
