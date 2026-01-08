from abc import ABC, abstractmethod
from app.detectors.base import PIIMatch


class Obfuscator(ABC):
    """Base class for text obfuscators."""

    placeholder_map: dict[str, str] = {}  # {"NAME": "[NAME]", "ID": "[ID]"}

    @abstractmethod
    def obfuscate(self, text: str, matches: list[PIIMatch]) -> str:
        """Replace PII with placeholders."""
        pass
