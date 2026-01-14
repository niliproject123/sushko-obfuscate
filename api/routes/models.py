"""
Request and response models for extraction endpoints.
"""
from pydantic import BaseModel, Field


class UserReplacement(BaseModel):
    """User-defined replacement mapping."""
    original: str
    replacement: str


class ExtractRequestConfig(BaseModel):
    """Per-request configuration from client."""
    user_replacements: dict[str, str] = Field(default_factory=dict)
    disabled_detectors: list[str] = Field(default_factory=list)
    force_ocr: bool = False


class PIIMatchResponse(BaseModel):
    """Response model for a PII match."""
    text: str
    type: str
    start: int
    end: int
    pattern_name: str = ""
    replacement: str = ""


class PageSummary(BaseModel):
    """Summary of processing for a single page."""
    page_number: int
    matches_found: int
    matches: list[PIIMatchResponse]


class ExtractResponse(BaseModel):
    """Response model for PDF extraction."""
    file_id: str
    page_count: int
    total_matches: int
    pages: list[PageSummary]
    mappings_used: dict[str, str]  # original -> replacement
    warnings: list[str] = Field(default_factory=list)
    obfuscated_text: str = ""  # Full obfuscated text for copy functionality


class PlainTextRequest(BaseModel):
    """Request model for plain text extraction."""
    text: str
    config: ExtractRequestConfig = Field(default_factory=ExtractRequestConfig)


class PlainTextResponse(BaseModel):
    """Response model for plain text extraction."""
    total_matches: int
    mappings_used: dict[str, str]
    obfuscated_text: str
    warnings: list[str] = Field(default_factory=list)
