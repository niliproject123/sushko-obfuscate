from pydantic import BaseModel, Field
from typing import Callable


class PIIPatternConfig(BaseModel):
    """Configuration for a single PII detection pattern."""
    name: str
    pii_type: str  # "NAME", "ID", "PHONE", "EMAIL", "ADDRESS", etc.
    regex: str
    capture_group: int = 0  # Which regex group contains the PII value
    enabled: bool = True
    validator: str | None = None  # Name of validator function (e.g., "israeli_id_checksum")


class ReplacementPoolsConfig(BaseModel):
    """Pools of fake values for automatic replacement."""
    name_hebrew_first: list[str] = Field(default_factory=list)
    name_hebrew_last: list[str] = Field(default_factory=list)
    name_english_first: list[str] = Field(default_factory=list)
    name_english_last: list[str] = Field(default_factory=list)
    city: list[str] = Field(default_factory=list)
    street: list[str] = Field(default_factory=list)
    age: list[str] = Field(default_factory=list)
    military_unit: list[str] = Field(default_factory=list)


class OCRConfig(BaseModel):
    """OCR processing configuration."""
    enabled: bool = True
    languages: list[str] = Field(default_factory=lambda: ["he", "en"])
    dpi: int = 300
    min_text_threshold: int = 50  # Minimum chars to consider PDF has text layer


class ServerConfig(BaseModel):
    """Server-side configuration (admin-controlled, persisted)."""
    patterns: list[PIIPatternConfig] = Field(default_factory=list)
    replacement_pools: ReplacementPoolsConfig = Field(default_factory=ReplacementPoolsConfig)
    ocr: OCRConfig = Field(default_factory=OCRConfig)
    placeholders: dict[str, str] = Field(default_factory=lambda: {
        "NAME": "[NAME]",
        "ID": "[ID]",
        "PHONE": "[PHONE]",
        "EMAIL": "[EMAIL]",
        "ADDRESS": "[ADDRESS]",
        "DEFAULT": "[REDACTED]",
    })
    default_replacements: dict[str, str] = Field(default_factory=dict)  # Global default replacements
    categories: dict[str, list[str]] = Field(default_factory=dict)  # Category -> words for detection


class RequestConfig(BaseModel):
    """Per-request configuration (user-controlled, passed in API call)."""
    user_replacements: dict[str, str] = Field(default_factory=dict)  # {"מיכאל": "דוד"}
    disabled_detectors: list[str] = Field(default_factory=list)  # ["email", "phone"]
    force_ocr: bool = False
    custom_patterns: list[PIIPatternConfig] = Field(default_factory=list)  # Additional patterns


class MergedConfig(BaseModel):
    """Merged configuration (server defaults + request overrides)."""
    patterns: list[PIIPatternConfig]
    replacement_pools: ReplacementPoolsConfig
    ocr: OCRConfig
    placeholders: dict[str, str]
    user_replacements: dict[str, str]  # Merged: default_replacements + request user_replacements
    force_ocr: bool
    categories: dict[str, list[str]] = Field(default_factory=dict)  # Category -> words
