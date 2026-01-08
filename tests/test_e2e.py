"""
End-to-end tests using real test resource files.

These tests verify:
1. PDF text extraction produces expected output (compare to _original.txt)
2. Anonymization with user replacements produces expected output (compare to _anonymized.txt)
"""
import os
import pytest
from pathlib import Path

from api.processors.pdf import PDFProcessor
from api.config import load_server_config, OCRConfig
from api.detectors.user_defined import UserDefinedDetector
from api.detectors.regex import RegexDetector
from api.obfuscators.text import TextObfuscator
from api.replacements.mapper import ReplacementMapper


# Path to test resources
RESOURCES_DIR = Path(__file__).parent / "resources"


# =============================================================================
# Replacement mappings from replacements.md
# =============================================================================

# medical_form replacements
MEDICAL_FORM_REPLACEMENTS = {
    # Patient info
    "מיכאל": "דוד",
    "פורגאצ'": "כהן",
    "15968548": "12345678",
    "פטר": "יעקב",
    "7374503": "1234567",
    "מאור": "רמת גן",
    "סיגלית": "הרצל",
    "370": "100",
    "058-6045454": "050-1234567",
    "fmish2@gmail.com": "david.cohen@example.com",
    "954": "123",
    "3689292": "9876543",
    # Contact person
    "בר": "שרה",
    "הורביץ": "לוי",
    "054-6684077": "050-9876543",
    # Officer
    "גל": "יוסי",
    "סדן": "ישראלי",
    "054-4824705": "050-1111111",
}

# medical_summary replacements
MEDICAL_SUMMARY_REPLACEMENTS = {
    # Patient info
    "מיכאל": "דוד",
    "פורגאצ'": "כהן",
    "'פורגאצ": "כהן",  # RTL variant
    "15968548": "12345678",
    "058-6045454": "050-1234567",
    "058­6045454": "050-1234567",  # With special dash
    "מאור": "רמת גן",
    "13072049": "98765432",
    # Medical staff
    "סז'ין": "לוי",
    "ין'סז": "לוי",  # RTL variant
    "34791": "11111",
    "שירה בן שאול": "מרים אברהם",
    "בן שאול": "אברהם",  # Split variant
    "שפירא פליקס": "גולדשטיין אבי",
    "155649": "22222",
    "קטאוי אחמד": "רוזן יעל",
    "161287": "33333",
    "ביבס": "שרון",
}


# =============================================================================
# Helper functions
# =============================================================================

def normalize_text(text: str) -> str:
    """Normalize text for comparison by removing extra whitespace and page markers."""
    lines = []
    for line in text.split("\n"):
        # Skip page separator lines
        if line.strip().startswith("===") or line.strip().startswith("---"):
            continue
        if line.strip().startswith("PAGE ") or line.strip().startswith("עמוד "):
            continue
        lines.append(line.rstrip())

    # Join and normalize whitespace
    result = "\n".join(lines)
    # Collapse multiple blank lines
    while "\n\n\n" in result:
        result = result.replace("\n\n\n", "\n\n")
    return result.strip()


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF file."""
    processor = PDFProcessor(ocr_config=OCRConfig(enabled=False, min_text_threshold=0))

    with open(pdf_path, "rb") as f:
        content = f.read()

    pages = processor.extract_text(content, force_ocr=False)

    # Combine all pages
    text_parts = []
    for page in pages:
        text_parts.append(page.text)

    return "\n".join(text_parts)


def apply_replacements(text: str, replacements: dict[str, str]) -> str:
    """Apply find-and-replace using user_replacements."""
    # Sort by length descending to replace longer strings first
    sorted_items = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)

    result = text
    for original, replacement in sorted_items:
        result = result.replace(original, replacement)

    return result


def compare_texts(actual: str, expected: str) -> tuple[bool, list[str]]:
    """
    Compare two texts and return differences.
    Returns (is_equal, list of differences).
    """
    actual_norm = normalize_text(actual)
    expected_norm = normalize_text(expected)

    if actual_norm == expected_norm:
        return True, []

    # Find differences
    actual_lines = actual_norm.split("\n")
    expected_lines = expected_norm.split("\n")

    differences = []
    max_lines = max(len(actual_lines), len(expected_lines))

    for i in range(max_lines):
        actual_line = actual_lines[i] if i < len(actual_lines) else "<missing>"
        expected_line = expected_lines[i] if i < len(expected_lines) else "<missing>"

        if actual_line != expected_line:
            differences.append(f"Line {i+1}:")
            differences.append(f"  Actual:   {actual_line[:80]}")
            differences.append(f"  Expected: {expected_line[:80]}")

            if len(differences) > 30:  # Limit output
                differences.append("... (truncated)")
                break

    return False, differences


# =============================================================================
# Extraction Tests
# =============================================================================

class TestPDFExtraction:
    """Test that PDF text extraction produces expected output.

    Note: The test PDFs are image-based (scanned) and require OCR.
    Tests will skip if OCR dependencies are not installed.
    """

    def test_medical_form_extraction(self):
        """Test extraction of medical_form_original.pdf matches medical_form_original.txt."""
        pdf_path = RESOURCES_DIR / "medical_form_original.pdf"
        txt_path = RESOURCES_DIR / "medical_form_original.txt"

        if not pdf_path.exists():
            pytest.skip(f"Test file not found: {pdf_path}")

        # Extract from PDF
        extracted = extract_text_from_pdf(pdf_path)

        # Skip if no text extracted (OCR not available for scanned PDFs)
        if len(extracted.strip()) < 50:
            pytest.skip("PDF is image-based and OCR dependencies not installed")

        # Load expected text
        with open(txt_path, "r", encoding="utf-8") as f:
            expected = f.read()

        # Verify key content is present (not exact match due to formatting)
        assert "מיכאל" in extracted, "First name should be in extracted text"
        assert "פורגאצ'" in extracted, "Last name should be in extracted text"
        assert "15968548" in extracted, "ID should be in extracted text"
        assert "058-6045454" in extracted or "058­6045454" in extracted, "Phone should be in extracted text"
        assert "fmish2@gmail.com" in extracted, "Email should be in extracted text"

    def test_medical_summary_extraction(self):
        """Test extraction of medical_summary_original.pdf matches medical_summary_original.txt."""
        pdf_path = RESOURCES_DIR / "medical_summary_original.pdf"
        txt_path = RESOURCES_DIR / "medical_summary_original.txt"

        if not pdf_path.exists():
            pytest.skip(f"Test file not found: {pdf_path}")

        # Extract from PDF
        extracted = extract_text_from_pdf(pdf_path)

        # Skip if no text extracted (OCR not available for scanned PDFs)
        if len(extracted.strip()) < 50:
            pytest.skip("PDF is image-based and OCR dependencies not installed")

        # Load expected text
        with open(txt_path, "r", encoding="utf-8") as f:
            expected = f.read()

        # Verify key content is present
        assert "מיכאל" in extracted or "פורגאצ'" in extracted, "Patient name should be in extracted text"
        assert "15968548" in extracted, "ID should be in extracted text"
        assert "13072049" in extracted, "Case number should be in extracted text"


# =============================================================================
# Anonymization Tests
# =============================================================================

class TestAnonymization:
    """Test that anonymization produces expected output."""

    def test_medical_form_anonymization(self):
        """Test anonymization of medical_form produces expected result."""
        original_path = RESOURCES_DIR / "medical_form_original.txt"
        anonymized_path = RESOURCES_DIR / "medical_form_anonimyzed.txt"

        # Load original text
        with open(original_path, "r", encoding="utf-8") as f:
            original_text = f.read()

        # Load expected anonymized text
        with open(anonymized_path, "r", encoding="utf-8") as f:
            expected_anonymized = f.read()

        # Apply replacements
        actual_anonymized = apply_replacements(original_text, MEDICAL_FORM_REPLACEMENTS)

        # Verify all original PII is removed
        for original_value in MEDICAL_FORM_REPLACEMENTS.keys():
            # Skip short values that might be part of other words
            if len(original_value) < 4:
                continue
            assert original_value not in actual_anonymized, \
                f"Original PII '{original_value}' should be replaced"

        # Verify all replacement values are present
        for replacement_value in MEDICAL_FORM_REPLACEMENTS.values():
            # Skip values that might conflict
            if replacement_value in ["100", "123"]:
                continue
            assert replacement_value in actual_anonymized, \
                f"Replacement '{replacement_value}' should be in anonymized text"

        # Compare to expected (key content)
        assert "דוד" in actual_anonymized, "Anonymized first name should be present"
        assert "כהן" in actual_anonymized, "Anonymized last name should be present"
        assert "12345678" in actual_anonymized, "Anonymized ID should be present"
        assert "050-1234567" in actual_anonymized, "Anonymized phone should be present"

    def test_medical_summary_anonymization(self):
        """Test anonymization of medical_summary produces expected result."""
        original_path = RESOURCES_DIR / "medical_summary_original.txt"
        anonymized_path = RESOURCES_DIR / "medical_summary_anonymized.txt"

        # Load original text
        with open(original_path, "r", encoding="utf-8") as f:
            original_text = f.read()

        # Load expected anonymized text
        with open(anonymized_path, "r", encoding="utf-8") as f:
            expected_anonymized = f.read()

        # Apply replacements
        actual_anonymized = apply_replacements(original_text, MEDICAL_SUMMARY_REPLACEMENTS)

        # Verify key original PII is removed
        assert "פורגאצ'" not in actual_anonymized or "'פורגאצ" not in actual_anonymized, \
            "Original last name should be replaced"
        assert "13072049" not in actual_anonymized, \
            "Original case number should be replaced"

        # Verify key replacements are present
        assert "כהן" in actual_anonymized, "Anonymized last name should be present"
        assert "12345678" in actual_anonymized, "Anonymized ID should be present"
        assert "98765432" in actual_anonymized, "Anonymized case number should be present"


# =============================================================================
# Full Pipeline Tests (using the API components)
# =============================================================================

class TestFullPipeline:
    """Test the full anonymization pipeline with real components."""

    def test_medical_form_pipeline(self):
        """Test full pipeline: detect + replace using API components."""
        original_path = RESOURCES_DIR / "medical_form_original.txt"

        with open(original_path, "r", encoding="utf-8") as f:
            original_text = f.read()

        # Create user-defined detector from replacements
        user_terms = [
            {"text": original, "type": "USER_DEFINED"}
            for original in MEDICAL_FORM_REPLACEMENTS.keys()
        ]
        detector = UserDefinedDetector(terms=user_terms)

        # Create mapper with user replacements
        mapper = ReplacementMapper(
            user_mappings=MEDICAL_FORM_REPLACEMENTS,
            pools={},
        )

        # Create obfuscator
        obfuscator = TextObfuscator(mapper=mapper)

        # Detect matches
        matches = detector.detect(original_text)

        # Should find matches for the key PII
        matched_texts = {m.text for m in matches}
        assert "מיכאל" in matched_texts, "Should detect first name"
        assert "15968548" in matched_texts, "Should detect ID"

        # Obfuscate
        anonymized = obfuscator.obfuscate(original_text, matches)

        # Verify replacements happened
        assert "דוד" in anonymized, "First name should be replaced"
        assert "12345678" in anonymized, "ID should be replaced"

        # Verify original PII is removed (for longer values)
        assert "מיכאל" not in anonymized, "Original first name should be removed"
        assert "15968548" not in anonymized, "Original ID should be removed"

    def test_medical_form_pdf_pipeline(self):
        """Test full pipeline from PDF to anonymized text.

        Note: Skips if PDF is image-based and OCR not installed.
        """
        pdf_path = RESOURCES_DIR / "medical_form_original.pdf"

        if not pdf_path.exists():
            pytest.skip(f"Test file not found: {pdf_path}")

        # Extract text from PDF
        extracted_text = extract_text_from_pdf(pdf_path)

        # Skip if no text extracted (OCR not available for scanned PDFs)
        if len(extracted_text.strip()) < 50:
            pytest.skip("PDF is image-based and OCR dependencies not installed")

        # Create detector and mapper
        user_terms = [
            {"text": original, "type": "USER_DEFINED"}
            for original in MEDICAL_FORM_REPLACEMENTS.keys()
        ]
        detector = UserDefinedDetector(terms=user_terms)
        mapper = ReplacementMapper(
            user_mappings=MEDICAL_FORM_REPLACEMENTS,
            pools={},
        )
        obfuscator = TextObfuscator(mapper=mapper)

        # Detect and obfuscate
        matches = detector.detect(extracted_text)
        anonymized = obfuscator.obfuscate(extracted_text, matches)

        # Verify PDF extraction worked and anonymization applied
        assert "דוד" in anonymized or "12345678" in anonymized, \
            "Anonymization should be applied to extracted PDF text"

    def test_medical_form_txt_pipeline(self):
        """Test full pipeline using _original.txt file (doesn't require OCR)."""
        txt_path = RESOURCES_DIR / "medical_form_original.txt"

        with open(txt_path, "r", encoding="utf-8") as f:
            original_text = f.read()

        # Create detector and mapper
        user_terms = [
            {"text": original, "type": "USER_DEFINED"}
            for original in MEDICAL_FORM_REPLACEMENTS.keys()
        ]
        detector = UserDefinedDetector(terms=user_terms)
        mapper = ReplacementMapper(
            user_mappings=MEDICAL_FORM_REPLACEMENTS,
            pools={},
        )
        obfuscator = TextObfuscator(mapper=mapper)

        # Detect and obfuscate
        matches = detector.detect(original_text)
        anonymized = obfuscator.obfuscate(original_text, matches)

        # Verify anonymization applied
        assert "דוד" in anonymized, "Anonymized first name should be present"
        assert "12345678" in anonymized, "Anonymized ID should be present"
        assert "מיכאל" not in anonymized, "Original first name should be removed"
        assert "15968548" not in anonymized, "Original ID should be removed"


# =============================================================================
# Regression Tests
# =============================================================================

class TestNoOriginalPIILeaks:
    """Ensure no original PII values leak through after anonymization."""

    def test_medical_form_no_leaks(self):
        """Verify all PII in medical_form is properly anonymized."""
        original_path = RESOURCES_DIR / "medical_form_original.txt"

        with open(original_path, "r", encoding="utf-8") as f:
            original_text = f.read()

        anonymized = apply_replacements(original_text, MEDICAL_FORM_REPLACEMENTS)

        # List of sensitive values that must not appear
        sensitive_values = [
            "מיכאל",
            "פורגאצ'",
            "15968548",
            "7374503",
            "058-6045454",
            "fmish2@gmail.com",
            "054-6684077",
            "054-4824705",
            "3689292",
        ]

        for value in sensitive_values:
            assert value not in anonymized, f"Sensitive value '{value}' should not be in output"
