"""
End-to-end tests using real test resource files.

These tests verify:
1. Anonymization with replacements from config replaces all PII
2. All tests are data-driven - no hardcoded assumptions about content
"""
import pytest
from pathlib import Path

from api.config import load_server_config
from api.detectors.user_defined import UserDefinedDetector
from api.obfuscators.text import TextObfuscator
from api.replacements.mapper import ReplacementMapper


# Path to test resources
RESOURCES_DIR = Path(__file__).parent / "resources"


def get_replacements_from_config() -> dict[str, str]:
    """Load default replacements from server config."""
    config = load_server_config()
    return config.default_replacements


def apply_replacements(text: str, replacements: dict[str, str]) -> str:
    """Apply find-and-replace using replacements dict."""
    # Sort by length descending to replace longer strings first
    sorted_items = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)

    result = text
    for original, replacement in sorted_items:
        result = result.replace(original, replacement)

    return result


class TestAnonymizationE2E:
    """
    End-to-end anonymization tests.

    These tests verify that applying the configured replacements:
    1. Removes all original PII values from text
    2. Replaces them with the configured replacement values
    """

    def test_medical_form_anonymization(self):
        """
        Test: original text + replacements removes all PII

        Verifies all original PII is replaced with configured values.
        """
        original_path = RESOURCES_DIR / "medical_form_original.txt"

        if not original_path.exists():
            pytest.skip("Test resource file not found")

        # Load original text
        with open(original_path, "r", encoding="utf-8") as f:
            original_text = f.read()

        # Get replacements from config
        replacements = get_replacements_from_config()

        # Apply replacements
        anonymized_text = apply_replacements(original_text, replacements)

        # Verify: original PII values should NOT be in output (for significant values)
        for original, replacement in replacements.items():
            # Skip short values that might be substrings of other words
            if len(original) >= 4:
                assert original not in anonymized_text, \
                    f"Original PII '{original}' should be replaced with '{replacement}'"

        # Verify: replacement values SHOULD be in output (for values that existed in original)
        for original, replacement in replacements.items():
            if original in original_text and len(replacement) >= 4:
                assert replacement in anonymized_text, \
                    f"Replacement '{replacement}' should appear in anonymized text"

    def test_medical_summary_anonymization(self):
        """
        Test: original text + replacements removes all PII

        Verifies all original PII is replaced with configured values.
        """
        original_path = RESOURCES_DIR / "medical_summary_original.txt"

        if not original_path.exists():
            pytest.skip("Test resource file not found")

        # Load original text
        with open(original_path, "r", encoding="utf-8") as f:
            original_text = f.read()

        # Get replacements from config
        replacements = get_replacements_from_config()

        # Apply replacements
        anonymized_text = apply_replacements(original_text, replacements)

        # Verify: original PII values should NOT be in output (for significant values)
        for original, replacement in replacements.items():
            # Skip short values that might be substrings of other words
            if len(original) >= 4:
                assert original not in anonymized_text, \
                    f"Original PII '{original}' should be replaced with '{replacement}'"

        # Verify: replacement values SHOULD be in output (for values that existed in original)
        for original, replacement in replacements.items():
            if original in original_text and len(replacement) >= 4:
                assert replacement in anonymized_text, \
                    f"Replacement '{replacement}' should appear in anonymized text"


class TestPipelineE2E:
    """
    Test the full detection + replacement pipeline using API components.
    """

    def test_medical_form_pipeline(self):
        """
        Test full pipeline: detect user-defined terms + replace

        Uses _original.txt file and config replacements.
        """
        original_path = RESOURCES_DIR / "medical_form_original.txt"

        if not original_path.exists():
            pytest.skip("Test resource file not found")

        with open(original_path, "r", encoding="utf-8") as f:
            original_text = f.read()

        # Get replacements from config
        replacements = get_replacements_from_config()

        # Create user-defined detector from replacements
        user_terms = [
            {"text": original, "type": "USER_DEFINED"}
            for original in replacements.keys()
        ]
        detector = UserDefinedDetector(terms=user_terms)

        # Create mapper with replacements
        mapper = ReplacementMapper(
            user_mappings=replacements,
            pools={},
        )

        # Create obfuscator
        obfuscator = TextObfuscator(mapper=mapper)

        # Detect matches
        matches = detector.detect(original_text)

        # Verify matches were found
        assert len(matches) > 0, "Should detect PII matches"

        # Obfuscate
        anonymized = obfuscator.obfuscate(original_text, matches)

        # Verify text was changed
        assert anonymized != original_text, "Text should be modified after obfuscation"

    def test_medical_summary_pipeline(self):
        """
        Test full pipeline: detect user-defined terms + replace

        Uses _original.txt file and config replacements.
        """
        original_path = RESOURCES_DIR / "medical_summary_original.txt"

        if not original_path.exists():
            pytest.skip("Test resource file not found")

        with open(original_path, "r", encoding="utf-8") as f:
            original_text = f.read()

        # Get replacements from config
        replacements = get_replacements_from_config()

        # Create user-defined detector from replacements
        user_terms = [
            {"text": original, "type": "USER_DEFINED"}
            for original in replacements.keys()
        ]
        detector = UserDefinedDetector(terms=user_terms)

        # Create mapper with replacements
        mapper = ReplacementMapper(
            user_mappings=replacements,
            pools={},
        )

        # Create obfuscator
        obfuscator = TextObfuscator(mapper=mapper)

        # Detect matches
        matches = detector.detect(original_text)

        # Verify matches were found
        assert len(matches) > 0, "Should detect PII matches"

        # Obfuscate
        anonymized = obfuscator.obfuscate(original_text, matches)

        # Verify text was changed
        assert anonymized != original_text, "Text should be modified after obfuscation"


class TestConfigReplacements:
    """Verify config has replacements loaded correctly."""

    def test_config_has_default_replacements(self):
        """Config should have default_replacements populated."""
        config = load_server_config()
        assert hasattr(config, 'default_replacements'), "Config should have default_replacements"
        assert len(config.default_replacements) > 0, "default_replacements should not be empty"

    def test_replacements_have_both_keys_and_values(self):
        """Each replacement should have non-empty key and value."""
        replacements = get_replacements_from_config()
        for key, value in replacements.items():
            assert key, "Replacement key should not be empty"
            assert value, "Replacement value should not be empty"
