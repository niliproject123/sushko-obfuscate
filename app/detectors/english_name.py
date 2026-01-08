import re
from app.detectors.base import Detector, PIIMatch


class EnglishNameDetector(Detector):
    """Detector for English names following common patterns."""

    name = "english_name"
    pii_type = "NAME"

    # Patterns for English name fields
    PATTERNS = [
        # Name: followed by text
        re.compile(r'\bName\s*[:\-]?\s*([A-Za-z][A-Za-z\s\-\']+)', re.IGNORECASE),
        # First Name: followed by text
        re.compile(r'\bFirst\s+Name\s*[:\-]?\s*([A-Za-z][A-Za-z\s\-\']+)', re.IGNORECASE),
        # Last Name: followed by text
        re.compile(r'\bLast\s+Name\s*[:\-]?\s*([A-Za-z][A-Za-z\s\-\']+)', re.IGNORECASE),
        # Surname: followed by text
        re.compile(r'\bSurname\s*[:\-]?\s*([A-Za-z][A-Za-z\s\-\']+)', re.IGNORECASE),
        # Full Name: followed by text
        re.compile(r'\bFull\s+Name\s*[:\-]?\s*([A-Za-z][A-Za-z\s\-\']+)', re.IGNORECASE),
    ]

    def detect(self, text: str) -> list[PIIMatch]:
        """Find all English names in text."""
        matches = []
        seen_positions = set()

        for pattern in self.PATTERNS:
            for match in pattern.finditer(text):
                # Extract the name part (group 1)
                name_text = match.group(1).strip()
                if not name_text:
                    continue

                # Skip very short matches (likely false positives)
                if len(name_text) < 2:
                    continue

                # Calculate actual position of the name
                name_start = match.start(1)
                name_end = match.end(1)

                # Avoid duplicates
                pos_key = (name_start, name_end)
                if pos_key in seen_positions:
                    continue
                seen_positions.add(pos_key)

                matches.append(PIIMatch(
                    text=name_text,
                    type=self.pii_type,
                    start=name_start,
                    end=name_end
                ))

        return matches
