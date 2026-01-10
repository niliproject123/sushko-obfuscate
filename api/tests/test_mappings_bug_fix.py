"""
Test for the bug fix: get_all_mappings() should only return USED mappings.

Bug description:
When processing a PDF with 0 matches, the UI was showing 34 "replacements"
(all the default_replacements from settings.json) even though none were
actually used. This created confusion where:
- 0 matches found
- But 34 word pairs shown in UI
- And PDF appeared empty

The fix ensures get_all_mappings() only returns mappings that were
actually used during processing.
"""
import pytest
from api.replacements.mapper import ReplacementMapper
from api.config.schemas import ReplacementPoolsConfig


class TestMappingsBugFix:
    """Test that only used mappings are returned."""

    def test_zero_matches_returns_zero_mappings(self):
        """
        When 0 PII matches are found, get_all_mappings() should return empty dict.

        This was the bug: it was returning all 34 default_replacements
        from settings.json even when none were used.
        """
        # Simulate the API setup with default_replacements
        default_replacements = {
            "מיכאל": "דוד",
            "פורגאצ'": "כהן",
            "15968548": "12345678",
            "058-6045454": "050-1234567",
            "fmish2@gmail.com": "david@example.com",
            # ... 29 more mappings like in settings.json
        }

        mapper = ReplacementMapper(
            user_mappings=default_replacements,
            pools=ReplacementPoolsConfig()
        )

        # Simulate processing a PDF with 0 matches
        # (no get_replacement() calls because no PII was detected)

        all_mappings = mapper.get_all_mappings()

        # BEFORE FIX: This would return all 5 mappings (the bug!)
        # AFTER FIX: This returns 0 mappings (correct)
        assert len(all_mappings) == 0, \
            f"Expected 0 mappings when nothing was used, got {len(all_mappings)}"

    def test_only_used_mappings_returned(self):
        """
        When only some PII matches are found, only those mappings should be returned.
        """
        # Simulate 34 default_replacements from settings.json
        default_replacements = {
            "מיכאל": "דוד",
            "פורגאצ'": "כהן",
            "15968548": "12345678",
            "058-6045454": "050-1234567",
            "fmish2@gmail.com": "david@example.com",
            "בר": "שרה",
            "גל": "יוסי",
            # Plus 27 more unused ones...
        }

        mapper = ReplacementMapper(
            user_mappings=default_replacements,
            pools=ReplacementPoolsConfig()
        )

        # Simulate processing PDF where only 2 PII items are found
        mapper.get_replacement("מיכאל", "NAME", "hebrew_first_name")
        mapper.get_replacement("fmish2@gmail.com", "EMAIL", "email")

        all_mappings = mapper.get_all_mappings()

        # BEFORE FIX: This would return all 7 mappings
        # AFTER FIX: This returns only 2 mappings (the ones actually used)
        assert len(all_mappings) == 2, \
            f"Expected 2 mappings (only the used ones), got {len(all_mappings)}"

        assert "מיכאל" in all_mappings
        assert all_mappings["מיכאל"] == "דוד"

        assert "fmish2@gmail.com" in all_mappings
        assert all_mappings["fmish2@gmail.com"] == "david@example.com"

        # The unused mappings should NOT be included
        assert "פורגאצ'" not in all_mappings
        assert "בר" not in all_mappings
        assert "גל" not in all_mappings

    def test_auto_generated_mappings_included(self):
        """
        Auto-generated mappings (from pools or generators) should still be included
        when they are used, even if they weren't in user_mappings.
        """
        mapper = ReplacementMapper(
            user_mappings={"מיכאל": "דוד"},  # Only 1 user mapping
            pools=ReplacementPoolsConfig()
        )

        # Use the user mapping
        mapper.get_replacement("מיכאל", "NAME", "hebrew_first_name")

        # Generate some auto mappings for unknown values
        mapper.get_replacement("שרה", "NAME", "hebrew_first_name")  # From pool
        mapper.get_replacement("123456789", "ID", "israeli_id")     # Generated

        all_mappings = mapper.get_all_mappings()

        # Should have all 3: 1 user + 2 auto
        assert len(all_mappings) == 3

        # User mapping
        assert "מיכאל" in all_mappings
        assert all_mappings["מיכאל"] == "דוד"

        # Auto-generated mappings
        assert "שרה" in all_mappings      # From pool
        assert "123456789" in all_mappings  # Generated ID

    def test_user_experience_scenario(self):
        """
        Simulate the exact user scenario that revealed the bug:

        User uploads image-based PDF
        → 0 matches found (image has no extractable text or OCR failed)
        → But UI shows 34 word pairs from default_replacements
        → User is confused: "Why show replacements if 0 matches?"
        """
        # Load default_replacements like the API does
        from api.config import load_server_config
        config = load_server_config()

        # Create mapper like extract.py does
        mapper = ReplacementMapper(
            user_mappings=config.default_replacements,
            pools=config.replacement_pools
        )

        # Simulate: Image-based PDF with 0 detectable text
        # No get_replacement() calls because no PII was detected

        # What the UI receives
        mappings_shown_to_user = mapper.get_all_mappings()

        # BEFORE FIX: mappings_shown_to_user would have 34+ items (confusing!)
        # AFTER FIX: mappings_shown_to_user has 0 items (correct!)
        assert len(mappings_shown_to_user) == 0, \
            "User should see 0 replacements when 0 matches are found"
