"""
PDF extraction and anonymization endpoint.
"""
import json
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import Response
from pydantic import BaseModel, Field

from api.config import (
    load_server_config,
    merge_config,
    RequestConfig,
    MergedConfig,
)
from api.processors.pdf import PDFProcessor
from api.processors.base import ProcessedPage
from api.detectors.regex import RegexDetector
from api.detectors.user_defined import UserDefinedDetector
from api.detectors.base import PIIMatch
from api.obfuscators.text import TextObfuscator
from api.replacements.mapper import ReplacementMapper
from api.storage.temp import storage


router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

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
    """Response model for extraction."""
    file_id: str
    page_count: int
    total_matches: int
    pages: list[PageSummary]
    mappings_used: dict[str, str]  # original -> replacement


# ============================================================================
# Configuration
# ============================================================================

# Load server config at startup
_server_config = load_server_config()

# Max file size (20MB)
MAX_FILE_SIZE = 20 * 1024 * 1024


def get_merged_config(request_config: Optional[ExtractRequestConfig] = None) -> MergedConfig:
    """Get merged configuration (server + request)."""
    if request_config is None:
        request_config_obj = RequestConfig()
    else:
        request_config_obj = RequestConfig(
            user_replacements=request_config.user_replacements,
            disabled_detectors=request_config.disabled_detectors,
            force_ocr=request_config.force_ocr,
        )
    return merge_config(_server_config, request_config_obj)


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/extract", response_model=ExtractResponse)
async def extract_and_obfuscate(
    file: UploadFile = File(...),
    config: str = Form(default="{}"),
):
    """
    Extract text from PDF and obfuscate PII.

    Args:
        file: The PDF file to process
        config: JSON string of ExtractRequestConfig

    Returns:
        Summary of processing with file ID for download and mappings used
    """
    # Parse config
    try:
        config_data = json.loads(config)
        request_config = ExtractRequestConfig(**config_data)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid config JSON: {e}")

    # Read and validate file
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // 1024 // 1024}MB"
        )

    # Get merged configuration
    merged_config = get_merged_config(request_config)

    # Create processor with OCR config
    processor = PDFProcessor(ocr_config=merged_config.ocr)

    # Extract text from PDF
    pages = processor.extract_text(content, force_ocr=merged_config.force_ocr)

    # Create detector from patterns
    regex_detector = RegexDetector(patterns=merged_config.patterns)

    # Create user-defined detector if there are user replacements
    user_detector = None
    if merged_config.user_replacements:
        user_terms = [
            {"text": original, "type": "USER_DEFINED"}
            for original in merged_config.user_replacements.keys()
        ]
        user_detector = UserDefinedDetector(terms=user_terms)

    # Create replacement mapper
    mapper = ReplacementMapper(
        user_mappings=merged_config.user_replacements,
        pools=merged_config.replacement_pools,
    )

    # Create obfuscator with mapper
    obfuscator = TextObfuscator(mapper=mapper)

    # Process each page
    processed_pages = []
    page_summaries = []
    total_matches = 0

    for page in pages:
        all_matches: list[PIIMatch] = []

        # User-defined matches first (take priority)
        if user_detector:
            user_matches = user_detector.detect(page.text)
            all_matches.extend(user_matches)

        # Pattern-based detection
        pattern_matches = regex_detector.detect(page.text)

        # Filter out matches that overlap with existing matches
        for new_match in pattern_matches:
            overlaps = any(
                (new_match.start < existing.end and new_match.end > existing.start)
                for existing in all_matches
            )
            if not overlaps:
                all_matches.append(new_match)

        # Obfuscate text
        processed_text = obfuscator.obfuscate(page.text, all_matches)

        # Build processed page
        processed_pages.append(ProcessedPage(
            page_number=page.page_number,
            original_text=page.text,
            processed_text=processed_text,
            metadata=page.metadata,
        ))

        # Build page summary with replacement info
        match_responses = []
        for match in all_matches:
            replacement = mapper.get_replacement(
                original=match.text,
                pii_type=match.type,
                pattern_name=match.pattern_name,
            )
            match_responses.append(PIIMatchResponse(
                text=match.text,
                type=match.type,
                start=match.start,
                end=match.end,
                pattern_name=match.pattern_name,
                replacement=replacement,
            ))

        page_summaries.append(PageSummary(
            page_number=page.page_number,
            matches_found=len(all_matches),
            matches=match_responses,
        ))

        total_matches += len(all_matches)

    # Reassemble PDF and save
    output_content = processor.reassemble(processed_pages)
    file_id = storage.save(output_content)

    return ExtractResponse(
        file_id=file_id,
        page_count=len(pages),
        total_matches=total_matches,
        pages=page_summaries,
        mappings_used=mapper.get_all_mappings(),
    )


@router.get("/download/{file_id}")
async def download_file(file_id: str):
    """Download processed file by ID."""
    content = storage.get(file_id)
    if not content:
        raise HTTPException(status_code=404, detail="File not found or expired")

    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=anonymized_{file_id}.pdf"
        }
    )


@router.post("/extract/text", response_model=ExtractResponse)
async def extract_text_only(
    file: UploadFile = File(...),
    config: str = Form(default="{}"),
):
    """
    Extract and anonymize text, returning text instead of PDF.
    Useful for previewing results before generating final PDF.
    """
    # This is identical to extract_and_obfuscate but could return
    # processed text directly instead of generating PDF
    return await extract_and_obfuscate(file=file, config=config)
