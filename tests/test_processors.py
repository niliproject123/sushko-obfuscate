import pytest
import fitz
from api.processors.pdf import PDFProcessor
from api.processors.base import ProcessedPage


def create_test_pdf(text: str) -> bytes:
    """Create a simple PDF with the given text."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), text)
    output = doc.tobytes()
    doc.close()
    return output


class TestPDFProcessor:
    def setup_method(self):
        self.processor = PDFProcessor()

    def test_supported_mimes(self):
        assert "application/pdf" in self.processor.supported_mimes

    def test_extract_text(self):
        pdf_bytes = create_test_pdf("Hello World")
        pages = self.processor.extract_text(pdf_bytes)
        assert len(pages) == 1
        assert "Hello World" in pages[0].text
        assert pages[0].page_number == 1

    def test_extract_text_multiple_pages(self):
        doc = fitz.open()
        doc.new_page().insert_text((50, 100), "Page 1")
        doc.new_page().insert_text((50, 100), "Page 2")
        pdf_bytes = doc.tobytes()
        doc.close()

        pages = self.processor.extract_text(pdf_bytes)
        assert len(pages) == 2
        assert "Page 1" in pages[0].text
        assert "Page 2" in pages[1].text

    def test_extract_text_metadata(self):
        pdf_bytes = create_test_pdf("Test")
        pages = self.processor.extract_text(pdf_bytes)
        assert pages[0].metadata is not None
        assert "width" in pages[0].metadata
        assert "height" in pages[0].metadata

    def test_reassemble(self):
        processed_pages = [
            ProcessedPage(
                page_number=1,
                original_text="Original",
                processed_text="Processed text here",
                metadata=None
            )
        ]
        result = self.processor.reassemble(processed_pages)
        assert isinstance(result, bytes)
        assert len(result) > 0

        # Verify it's a valid PDF
        doc = fitz.open(stream=result, filetype="pdf")
        assert len(doc) == 1
        assert "Processed text here" in doc[0].get_text()
        doc.close()

    def test_reassemble_multiple_pages(self):
        processed_pages = [
            ProcessedPage(
                page_number=1,
                original_text="Original 1",
                processed_text="Page 1 content",
                metadata=None
            ),
            ProcessedPage(
                page_number=2,
                original_text="Original 2",
                processed_text="Page 2 content",
                metadata=None
            )
        ]
        result = self.processor.reassemble(processed_pages)
        doc = fitz.open(stream=result, filetype="pdf")
        assert len(doc) == 2
        doc.close()
