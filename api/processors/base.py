from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PageContent:
    """Content extracted from a single page/segment."""
    page_number: int
    text: str
    metadata: dict | None = None


@dataclass
class ProcessedPage:
    """Page content after obfuscation."""
    page_number: int
    original_text: str
    processed_text: str
    metadata: dict | None = None


class Processor(ABC):
    """Base class for file processors."""

    supported_mimes: list[str] = []

    @abstractmethod
    def extract_text(self, file: bytes) -> list[PageContent]:
        """Extract text from file, per page/segment."""
        pass

    @abstractmethod
    def reassemble(self, pages: list[ProcessedPage]) -> bytes:
        """Rebuild file from processed pages."""
        pass
