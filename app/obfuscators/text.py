from app.obfuscators.base import Obfuscator
from app.detectors.base import PIIMatch


class TextObfuscator(Obfuscator):
    """Replaces PII with placeholder text."""

    def __init__(self, placeholder_map: dict[str, str] | None = None):
        """
        Initialize with custom placeholder map.

        Args:
            placeholder_map: Mapping of PII types to placeholders.
                            e.g., {"NAME": "[NAME]", "ID": "[ID]"}
        """
        self.placeholder_map = placeholder_map or {
            "NAME": "[NAME]",
            "ID": "[ID]",
            "USER_DEFINED": "[REDACTED]",
            "DEFAULT": "[REDACTED]",
        }

    def obfuscate(self, text: str, matches: list[PIIMatch]) -> str:
        """
        Replace PII with placeholders.
        Processes matches in reverse order to maintain position accuracy.
        """
        if not matches:
            return text

        # Sort by start position descending to replace from end to start
        sorted_matches = sorted(matches, key=lambda m: m.start, reverse=True)

        result = text
        for match in sorted_matches:
            placeholder = self.placeholder_map.get(
                match.type,
                self.placeholder_map.get("DEFAULT", "[REDACTED]")
            )
            result = result[:match.start] + placeholder + result[match.end:]

        return result
