import re
from api.detectors.base import Detector, PIIMatch


class IsraeliIdDetector(Detector):
    """Detector for Israeli ID numbers (9 digits)."""

    name = "israeli_id"
    pii_type = "ID"

    # Israeli ID: exactly 9 digits, may have leading zeros
    PATTERN = re.compile(r'\b\d{9}\b')

    def detect(self, text: str) -> list[PIIMatch]:
        """Find all Israeli ID numbers in text."""
        matches = []

        for match in self.PATTERN.finditer(text):
            # Validate using Luhn-like checksum for Israeli IDs
            if self._validate_israeli_id(match.group()):
                matches.append(PIIMatch(
                    text=match.group(),
                    type=self.pii_type,
                    start=match.start(),
                    end=match.end()
                ))

        return matches

    def _validate_israeli_id(self, id_number: str) -> bool:
        """
        Validate Israeli ID using the official checksum algorithm.
        """
        if len(id_number) != 9:
            return False

        total = 0
        for i, digit in enumerate(id_number):
            num = int(digit)
            if i % 2 == 1:
                num *= 2
            if num > 9:
                num = num // 10 + num % 10
            total += num

        return total % 10 == 0
