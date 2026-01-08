"""
RegexDetector - configurable pattern-based PII detector.
Handles all regex-based detection with optional validation.
"""
import re
from typing import Optional

from api.detectors.base import Detector, PIIMatch
from api.detectors.validators import get_validator
from api.config.schemas import PIIPatternConfig


class RegexDetector(Detector):
    """
    Detector that uses configurable regex patterns.
    Supports multiple patterns with optional validators.
    """

    name = "regex"
    pii_type = "VARIOUS"

    def __init__(self, patterns: Optional[list[PIIPatternConfig]] = None):
        """
        Initialize with list of pattern configurations.

        Args:
            patterns: List of PIIPatternConfig objects
        """
        self.patterns = patterns or []
        self._compiled_patterns: list[tuple[PIIPatternConfig, re.Pattern]] = []
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        self._compiled_patterns = []
        for pattern_config in self.patterns:
            if not pattern_config.enabled:
                continue
            try:
                compiled = re.compile(pattern_config.regex, re.UNICODE)
                self._compiled_patterns.append((pattern_config, compiled))
            except re.error as e:
                # Log warning but continue with other patterns
                print(f"Warning: Invalid regex pattern '{pattern_config.name}': {e}")

    def detect(self, text: str) -> list[PIIMatch]:
        """
        Find all PII matches in text using configured patterns.

        Args:
            text: The text to search for PII

        Returns:
            List of PIIMatch objects
        """
        matches: list[PIIMatch] = []
        seen_positions: set[tuple[int, int]] = set()

        for pattern_config, compiled_regex in self._compiled_patterns:
            # Get validator function if specified
            validator = get_validator(pattern_config.validator)

            for match in compiled_regex.finditer(text):
                # Get the captured group or full match
                if pattern_config.capture_group > 0:
                    try:
                        matched_text = match.group(pattern_config.capture_group)
                        if matched_text is None:
                            continue
                        start = match.start(pattern_config.capture_group)
                        end = match.end(pattern_config.capture_group)
                    except IndexError:
                        # Group doesn't exist, use full match
                        matched_text = match.group(0)
                        start = match.start()
                        end = match.end()
                else:
                    matched_text = match.group(0)
                    start = match.start()
                    end = match.end()

                # Strip whitespace from matched text
                matched_text = matched_text.strip()
                if not matched_text:
                    continue

                # Adjust positions for stripped text
                original_start = text.find(matched_text, start)
                if original_start >= 0:
                    start = original_start
                    end = start + len(matched_text)

                # Skip if position already matched (avoid duplicates)
                pos_key = (start, end)
                if pos_key in seen_positions:
                    continue

                # Apply validator if specified
                if validator and not validator(matched_text):
                    continue

                seen_positions.add(pos_key)
                matches.append(PIIMatch(
                    text=matched_text,
                    type=pattern_config.pii_type,
                    start=start,
                    end=end,
                    pattern_name=pattern_config.name,
                ))

        # Sort by position (start, then end)
        matches.sort(key=lambda m: (m.start, m.end))

        return matches

    def add_pattern(self, pattern: PIIPatternConfig) -> None:
        """Add a pattern to the detector."""
        self.patterns.append(pattern)
        if pattern.enabled:
            try:
                compiled = re.compile(pattern.regex, re.UNICODE)
                self._compiled_patterns.append((pattern, compiled))
            except re.error as e:
                print(f"Warning: Invalid regex pattern '{pattern.name}': {e}")

    def remove_pattern(self, name: str) -> None:
        """Remove a pattern by name."""
        self.patterns = [p for p in self.patterns if p.name != name]
        self._compiled_patterns = [
            (p, r) for p, r in self._compiled_patterns if p.name != name
        ]

    def set_patterns(self, patterns: list[PIIPatternConfig]) -> None:
        """Replace all patterns."""
        self.patterns = patterns
        self._compile_patterns()


def create_detector_from_config(patterns: list[PIIPatternConfig]) -> RegexDetector:
    """Factory function to create detector from config patterns."""
    return RegexDetector(patterns=patterns)
