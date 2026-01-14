"""
Category-based word detector.

Detects words from predefined categories (e.g., military units).
Each category maps to a list of words to detect.
"""
import re
from typing import Optional

from api.detectors.base import PIIMatch


class CategoryDetector:
    """Detector that finds words from category-based word lists."""

    def __init__(self, categories: dict[str, list[str]], pii_type: str = "CATEGORY"):
        """
        Initialize the category detector.

        Args:
            categories: Dict mapping category names to word lists
            pii_type: The PII type to assign to matches (default: "CATEGORY")
        """
        self.categories = categories
        self.pii_type = pii_type
        self._build_patterns()

    def _build_patterns(self) -> None:
        """Build regex patterns for each word in categories."""
        self.word_to_category: dict[str, str] = {}
        self.patterns: list[tuple[re.Pattern, str, str]] = []

        for category, words in self.categories.items():
            for word in words:
                # Store word -> category mapping
                self.word_to_category[word] = category

                # Build pattern with word boundaries
                # For Hebrew, use lookbehind/lookahead for Hebrew chars
                # For numbers/English, use \b
                if re.search(r'[\u0590-\u05FF]', word):
                    # Hebrew word - use Hebrew word boundaries
                    pattern = rf'(?<![א-ת]){re.escape(word)}(?![א-ת])'
                else:
                    # Non-Hebrew (numbers, English) - use standard word boundaries
                    pattern = rf'\b{re.escape(word)}\b'

                try:
                    compiled = re.compile(pattern)
                    self.patterns.append((compiled, word, category))
                except re.error:
                    # Skip invalid patterns
                    continue

    def detect(self, text: str) -> list[PIIMatch]:
        """
        Find all category word matches in text.

        Args:
            text: The text to search

        Returns:
            List of PIIMatch objects for each match found
        """
        matches: list[PIIMatch] = []
        seen_positions: set[tuple[int, int]] = set()

        for pattern, word, category in self.patterns:
            for match in pattern.finditer(text):
                start, end = match.start(), match.end()

                # Skip if this position was already matched
                if (start, end) in seen_positions:
                    continue

                seen_positions.add((start, end))
                matches.append(PIIMatch(
                    text=match.group(),
                    type=self.pii_type,
                    start=start,
                    end=end,
                    pattern_name=f"category:{category}",
                ))

        return matches

    def get_categories(self) -> dict[str, list[str]]:
        """Return the current categories."""
        return self.categories

    def add_word(self, category: str, word: str) -> None:
        """Add a word to a category."""
        if category not in self.categories:
            self.categories[category] = []
        if word not in self.categories[category]:
            self.categories[category].append(word)
            self._build_patterns()

    def remove_word(self, category: str, word: str) -> bool:
        """Remove a word from a category. Returns True if removed."""
        if category in self.categories and word in self.categories[category]:
            self.categories[category].remove(word)
            self._build_patterns()
            return True
        return False

    def add_category(self, category: str, words: Optional[list[str]] = None) -> None:
        """Add a new category with optional initial words."""
        if category not in self.categories:
            self.categories[category] = words or []
            self._build_patterns()

    def remove_category(self, category: str) -> bool:
        """Remove a category. Returns True if removed."""
        if category in self.categories:
            del self.categories[category]
            self._build_patterns()
            return True
        return False
