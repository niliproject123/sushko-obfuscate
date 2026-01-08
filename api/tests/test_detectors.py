import pytest
from api.detectors.israeli_id import IsraeliIdDetector
from api.detectors.hebrew_name import HebrewNameDetector
from api.detectors.english_name import EnglishNameDetector
from api.detectors.user_defined import UserDefinedDetector


class TestIsraeliIdDetector:
    def setup_method(self):
        self.detector = IsraeliIdDetector()

    def test_valid_israeli_id(self):
        text = "My ID is 123456782"
        matches = self.detector.detect(text)
        assert len(matches) == 1
        assert matches[0].text == "123456782"
        assert matches[0].type == "ID"

    def test_invalid_israeli_id_checksum(self):
        text = "Invalid ID 123456789"
        matches = self.detector.detect(text)
        assert len(matches) == 0

    def test_multiple_ids(self):
        # Both IDs must have valid checksums
        text = "ID1: 123456782 and ID2: 000000018"
        matches = self.detector.detect(text)
        assert len(matches) == 2

    def test_no_id(self):
        text = "No ID here"
        matches = self.detector.detect(text)
        assert len(matches) == 0


class TestHebrewNameDetector:
    def setup_method(self):
        self.detector = HebrewNameDetector()

    def test_hebrew_name(self):
        text = "שם: ישראל ישראלי"
        matches = self.detector.detect(text)
        assert len(matches) == 1
        assert "ישראל" in matches[0].text
        assert matches[0].type == "NAME"

    def test_first_name_hebrew(self):
        # Pattern matches שם פרטי followed by Hebrew text
        text = "שם פרטי דוד כהן"
        matches = self.detector.detect(text)
        assert len(matches) >= 1
        assert any("דוד" in m.text for m in matches)

    def test_family_name_hebrew(self):
        # Pattern matches שם משפחה followed by Hebrew text
        text = "שם משפחה לוי"
        matches = self.detector.detect(text)
        assert len(matches) >= 1
        assert any("לוי" in m.text for m in matches)

    def test_no_hebrew_name(self):
        text = "Some English text"
        matches = self.detector.detect(text)
        assert len(matches) == 0


class TestEnglishNameDetector:
    def setup_method(self):
        self.detector = EnglishNameDetector()

    def test_english_name(self):
        text = "Name: John Smith"
        matches = self.detector.detect(text)
        assert len(matches) == 1
        assert matches[0].text == "John Smith"
        assert matches[0].type == "NAME"

    def test_first_name(self):
        text = "First Name: John"
        matches = self.detector.detect(text)
        assert len(matches) == 1
        assert matches[0].text == "John"

    def test_last_name(self):
        text = "Last Name: Smith"
        matches = self.detector.detect(text)
        assert len(matches) == 1
        assert matches[0].text == "Smith"

    def test_surname(self):
        text = "Surname: Johnson"
        matches = self.detector.detect(text)
        assert len(matches) == 1
        assert matches[0].text == "Johnson"

    def test_no_name(self):
        text = "Some random text"
        matches = self.detector.detect(text)
        assert len(matches) == 0

    def test_name_stops_at_newline(self):
        text = "Name: John Smith\nID: 12345"
        matches = self.detector.detect(text)
        assert len(matches) == 1
        assert matches[0].text == "John Smith"


class TestUserDefinedDetector:
    def test_single_term(self):
        detector = UserDefinedDetector(terms=[{"text": "secret"}])
        text = "This is a secret message"
        matches = detector.detect(text)
        assert len(matches) == 1
        assert matches[0].text == "secret"

    def test_multiple_terms(self):
        detector = UserDefinedDetector(terms=[
            {"text": "foo"},
            {"text": "bar"}
        ])
        text = "foo and bar"
        matches = detector.detect(text)
        assert len(matches) == 2

    def test_multiple_occurrences(self):
        detector = UserDefinedDetector(terms=[{"text": "test"}])
        text = "test one test two"
        matches = detector.detect(text)
        assert len(matches) == 2

    def test_custom_type(self):
        detector = UserDefinedDetector(terms=[{"text": "secret", "type": "SECRET"}])
        text = "This is secret"
        matches = detector.detect(text)
        assert matches[0].type == "SECRET"

    def test_no_terms(self):
        detector = UserDefinedDetector(terms=[])
        text = "Some text"
        matches = detector.detect(text)
        assert len(matches) == 0
