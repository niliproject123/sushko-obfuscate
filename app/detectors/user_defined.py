from app.detectors.base import Detector, PIIMatch


class UserDefinedDetector(Detector):
    """Detector for user-provided exact match strings."""

    name = "user_defined"
    pii_type = "USER_DEFINED"

    def __init__(self, terms: list[dict[str, str]] | None = None):
        """
        Initialize with user-defined terms.

        Args:
            terms: List of dicts with 'text' and optional 'type' keys.
                   e.g., [{"text": "John Doe", "type": "NAME"}]
        """
        self.terms = terms or []

    def detect(self, text: str) -> list[PIIMatch]:
        """Find all user-defined terms in text using exact match."""
        matches = []

        for term in self.terms:
            search_text = term.get("text", "")
            pii_type = term.get("type", "USER_DEFINED")

            if not search_text:
                continue

            # Find all occurrences
            start = 0
            while True:
                pos = text.find(search_text, start)
                if pos == -1:
                    break

                matches.append(PIIMatch(
                    text=search_text,
                    type=pii_type,
                    start=pos,
                    end=pos + len(search_text)
                ))
                start = pos + 1

        return matches
