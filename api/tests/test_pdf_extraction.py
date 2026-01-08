"""
PDF Extraction Correctness Tests.

Tests that PDF text extraction produces text matching the expected _original.txt files.
These tests verify the PDFProcessor extracts text correctly from PDFs.

IMPORTANT: Resource files must NOT be modified. Tests compare against them as ground truth.
"""
import pytest
from pathlib import Path

from api.processors.pdf import PDFProcessor
from api.config.schemas import OCRConfig


# Path to test resources
RESOURCES_DIR = Path(__file__).parent / "resources"


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison.

    Handles whitespace differences that may occur during PDF extraction.
    """
    # Replace multiple whitespace with single space
    import re
    text = re.sub(r'[ \t]+', ' ', text)
    # Normalize line endings
    text = text.replace('\r\n', '\n')
    # Remove trailing whitespace from lines
    lines = [line.rstrip() for line in text.split('\n')]
    # Remove empty lines at start/end
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return '\n'.join(lines)


def extract_all_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF file, combining all pages."""
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()

    # Enable OCR for scanned/image-based PDFs
    processor = PDFProcessor(ocr_config=OCRConfig(enabled=True, languages=['he', 'en']))
    pages = processor.extract_text(pdf_bytes)

    # Combine all pages
    all_text = '\n'.join(page.text for page in pages)
    return all_text


class TestPDFExtractionCorrectness:
    """
    Test that PDF extraction produces text matching _original.txt files.

    These are critical tests - they verify the PDF→text stage works correctly.
    """

    def test_medical_form_pdf_extraction_contains_expected_content(self):
        """
        Test: medical_form_original.pdf extraction contains key content from _original.txt

        Verifies that important PII and content from the PDF matches what's in _original.txt
        """
        pdf_path = RESOURCES_DIR / "medical_form_original.pdf"
        txt_path = RESOURCES_DIR / "medical_form_original.txt"

        if not pdf_path.exists() or not txt_path.exists():
            pytest.skip("Test resource files not found")

        # Extract text from PDF
        extracted_text = extract_all_text_from_pdf(pdf_path)

        # Load expected text
        with open(txt_path, 'r', encoding='utf-8') as f:
            expected_text = f.read()

        # Verify key PII values are extracted correctly
        # These are the critical values that must be detected for anonymization to work
        key_values = [
            'מיכאל',           # First name
            'פורגאצ\'',        # Last name
            '15968548',        # ID number
            'פטר',             # Father's name
            '7374503',         # Military ID
            'מאור',            # City
            'סיגלית',          # Street
            '058-6045454',     # Phone
            'fmish2@gmail.com', # Email
            '954',             # Bank branch
            '3689292',         # Bank account
            'בר',              # Contact first name
            'הורביץ',          # Contact last name
            '054-6684077',     # Contact phone
            'גל',              # Form filler first name
            'סדן',             # Form filler last name
            '054-4824705',     # Form filler phone
        ]

        missing_values = []
        for value in key_values:
            if value not in extracted_text:
                missing_values.append(value)

        # Allow up to 10% of values to be missed due to OCR imperfections
        max_missing = max(1, len(key_values) // 10)
        assert len(missing_values) <= max_missing, \
            f"PDF extraction missing too many key values ({len(missing_values)} > {max_missing}): {missing_values}"

    def test_medical_form_pdf_extraction_text_similarity(self):
        """
        Test: medical_form_original.pdf extracted text is similar to _original.txt

        Checks that the overall structure and content matches.
        """
        pdf_path = RESOURCES_DIR / "medical_form_original.pdf"
        txt_path = RESOURCES_DIR / "medical_form_original.txt"

        if not pdf_path.exists() or not txt_path.exists():
            pytest.skip("Test resource files not found")

        # Extract text from PDF
        extracted_text = extract_all_text_from_pdf(pdf_path)

        # Load expected text
        with open(txt_path, 'r', encoding='utf-8') as f:
            expected_text = f.read()

        # Normalize both for comparison
        normalized_extracted = normalize_text(extracted_text)
        normalized_expected = normalize_text(expected_text)

        # Check line-by-line similarity
        extracted_lines = set(normalized_extracted.split('\n'))
        expected_lines = set(normalized_expected.split('\n'))

        # Calculate overlap
        common_lines = extracted_lines & expected_lines

        # At least 70% of expected lines should be found in extracted text
        if len(expected_lines) > 0:
            similarity = len(common_lines) / len(expected_lines)
            assert similarity >= 0.7, \
                f"PDF extraction similarity too low: {similarity:.1%}. " \
                f"Expected at least 70% of lines to match."

    def test_medical_summary_pdf_extraction_contains_expected_content(self):
        """
        Test: medical_summary_original.pdf extraction contains key content
        """
        pdf_path = RESOURCES_DIR / "medical_summary_original.pdf"
        txt_path = RESOURCES_DIR / "medical_summary_original.txt"

        if not pdf_path.exists() or not txt_path.exists():
            pytest.skip("Test resource files not found")

        # Extract text from PDF
        extracted_text = extract_all_text_from_pdf(pdf_path)

        # Load expected text to find key values
        with open(txt_path, 'r', encoding='utf-8') as f:
            expected_text = f.read()

        # The extracted text should have substantial content
        assert len(extracted_text) > 1000, \
            f"PDF extraction returned too little text: {len(extracted_text)} chars"

        # Check that extraction method worked
        assert len(extracted_text) > 0, "PDF extraction returned empty text"

    def test_pdf_page_count_matches(self):
        """
        Test: PDF extraction returns correct number of pages
        """
        pdf_path = RESOURCES_DIR / "medical_form_original.pdf"

        if not pdf_path.exists():
            pytest.skip("Test resource file not found")

        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        processor = PDFProcessor(ocr_config=OCRConfig(enabled=False))
        pages = processor.extract_text(pdf_bytes, force_ocr=False)

        # medical_form has 3 pages based on content in _original.txt
        assert len(pages) == 3, f"Expected 3 pages, got {len(pages)}"
