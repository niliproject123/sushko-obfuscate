import re
from api.detectors.base import Detector, PIIMatch


class HebrewNameDetector(Detector):
    """Detector for Hebrew names following common patterns."""

    name = "hebrew_name"
    pii_type = "NAME"

    # Patterns for Hebrew name fields
    PATTERNS = [
        # שם: followed by Hebrew text
        re.compile(r'שם\s*[:\-]?\s*([\u0590-\u05FF\s]+)', re.UNICODE),
        # שם פרטי: (first name)
        re.compile(r'שם\s+פרטי\s*[:\-]?\s*([\u0590-\u05FF\s]+)', re.UNICODE),
        # שם משפחה: (family name)
        re.compile(r'שם\s+משפחה\s*[:\-]?\s*([\u0590-\u05FF\s]+)', re.UNICODE),
    ]

    def detect(self, text: str) -> list[PIIMatch]:
        """Find all Hebrew names in text."""
        matches = []
        seen_positions = set()

        for pattern in self.PATTERNS:
            for match in pattern.finditer(text):
                # Extract the name part (group 1)
                name_text = match.group(1).strip()
                if not name_text:
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
