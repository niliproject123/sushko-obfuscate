import io
import fitz  # PyMuPDF
import pdfplumber
from api.processors.base import Processor, PageContent, ProcessedPage


class PDFProcessor(Processor):
    """PDF processor using PyMuPDF and pdfplumber for text extraction."""

    supported_mimes = ["application/pdf"]

    def extract_text(self, file: bytes) -> list[PageContent]:
        """
        Extract text from PDF using PyMuPDF.
        Falls back to pdfplumber for better table handling if needed.
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
                    }
                ))
        finally:
            doc.close()

        # Enhance with table extraction from pdfplumber
        self._add_tables(file, pages)

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
        For v1, returns a simple text-based PDF with the processed content.
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
