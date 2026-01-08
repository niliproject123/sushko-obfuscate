from typing import Optional

from api.obfuscators.base import Obfuscator
from api.detectors.base import PIIMatch
from api.replacements.mapper import ReplacementMapper


class TextObfuscator(Obfuscator):
    """Replaces PII with fake values or placeholder text."""

    def __init__(
        self,
        mapper: Optional[ReplacementMapper] = None,
        placeholder_map: Optional[dict[str, str]] = None,
    ):
        """
        Initialize with replacement mapper and/or placeholder map.

        Args:
            mapper: ReplacementMapper for consistent fake value replacements
            placeholder_map: Fallback mapping of PII types to placeholders.
                            e.g., {"NAME": "[NAME]", "ID": "[ID]"}
        """
        self.mapper = mapper
        self.placeholder_map = placeholder_map or {
            "NAME": "[NAME]",
            "ID": "[ID]",
            "PHONE": "[PHONE]",
            "EMAIL": "[EMAIL]",
            "ADDRESS": "[ADDRESS]",
            "USER_DEFINED": "[REDACTED]",
            "DEFAULT": "[REDACTED]",
        }

    def obfuscate(self, text: str, matches: list[PIIMatch]) -> str:
        """
        Replace PII with fake values or placeholders.
        Processes matches in reverse order to maintain position accuracy.

        Args:
            text: Original text
            matches: List of PII matches to replace

        Returns:
            Text with PII replaced
        """
        if not matches:
            return text

        # Sort by start position descending to replace from end to start
        sorted_matches = sorted(matches, key=lambda m: m.start, reverse=True)

        result = text
        for match in sorted_matches:
            replacement = self._get_replacement(match)
            result = result[:match.start] + replacement + result[match.end:]

        return result

    def _get_replacement(self, match: PIIMatch) -> str:
        """Get replacement value for a match."""
        # If mapper is available, use it for consistent fake values
        if self.mapper is not None:
            return self.mapper.get_replacement(
                original=match.text,
                pii_type=match.type,
                pattern_name=match.pattern_name,
            )

        # Fallback to placeholder map
        return self.placeholder_map.get(
            match.type,
            self.placeholder_map.get("DEFAULT", "[REDACTED]")
        )
