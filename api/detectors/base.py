from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PIIMatch:
    """Represents a detected PII match in text."""
    text: str       # original text found
    type: str       # "NAME", "ID", etc.
    start: int      # position in text
    end: int        # end position in text


class Detector(ABC):
    """Base class for PII detectors."""

    name: str = ""
    pii_type: str = ""  # e.g., "NAME", "ID"

    @abstractmethod
    def detect(self, text: str) -> list[PIIMatch]:
        """Find all PII in text."""
        pass
