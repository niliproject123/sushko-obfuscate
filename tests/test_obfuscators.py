import pytest
from api.obfuscators.text import TextObfuscator
from api.detectors.base import PIIMatch


class TestTextObfuscator:
    def setup_method(self):
        self.obfuscator = TextObfuscator()

    def test_obfuscate_name(self):
        text = "Hello John"
        matches = [PIIMatch(text="John", type="NAME", start=6, end=10)]
        result = self.obfuscator.obfuscate(text, matches)
        assert result == "Hello [NAME]"

    def test_obfuscate_id(self):
        text = "ID: 123456789"
        matches = [PIIMatch(text="123456789", type="ID", start=4, end=13)]
        result = self.obfuscator.obfuscate(text, matches)
        assert result == "ID: [ID]"

    def test_obfuscate_multiple(self):
        text = "Name: John ID: 123456789"
        matches = [
            PIIMatch(text="John", type="NAME", start=6, end=10),
            PIIMatch(text="123456789", type="ID", start=15, end=24)
        ]
        result = self.obfuscator.obfuscate(text, matches)
        assert result == "Name: [NAME] ID: [ID]"

    def test_obfuscate_overlapping_positions(self):
        text = "Start John Smith End"
        matches = [
            PIIMatch(text="John Smith", type="NAME", start=6, end=16)
        ]
        result = self.obfuscator.obfuscate(text, matches)
        assert result == "Start [NAME] End"

    def test_no_matches(self):
        text = "No PII here"
        result = self.obfuscator.obfuscate(text, [])
        assert result == "No PII here"

    def test_custom_placeholder(self):
        custom_map = {"NAME": "***", "ID": "###"}
        obfuscator = TextObfuscator(placeholder_map=custom_map)
        text = "Name: John"
        matches = [PIIMatch(text="John", type="NAME", start=6, end=10)]
        result = obfuscator.obfuscate(text, matches)
        assert result == "Name: ***"

    def test_default_placeholder_for_unknown_type(self):
        text = "Secret: xyz"
        matches = [PIIMatch(text="xyz", type="UNKNOWN", start=8, end=11)]
        result = self.obfuscator.obfuscate(text, matches)
        assert result == "Secret: [REDACTED]"
