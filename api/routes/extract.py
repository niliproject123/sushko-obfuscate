from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from api.config import config
from api.processors.pdf import PDFProcessor
from api.processors.base import ProcessedPage
from api.detectors.user_defined import UserDefinedDetector
from api.detectors.base import PIIMatch
from api.obfuscators.text import TextObfuscator
from api.storage.temp import storage


router = APIRouter()


class ObfuscationTerm(BaseModel):
    """User-defined term to obfuscate."""
    text: str
    type: str = "USER_DEFINED"
    replace_with: str | None = None


class ExtractRequest(BaseModel):
    """Request model for extraction with obfuscations."""
    obfuscations: list[ObfuscationTerm] = []


class PIIMatchResponse(BaseModel):
    """Response model for a PII match."""
    text: str
    type: str
    start: int
    end: int


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


# Processor registry by MIME type
PROCESSORS = {
    mime: PDFProcessor()
    for mime in PDFProcessor.supported_mimes
}


def get_processor(mime_type: str):
    """Get processor for the given MIME type."""
    processor = PROCESSORS.get(mime_type)
    if not processor:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {mime_type}"
        )
    return processor


@router.post("/extract", response_model=ExtractResponse)
async def extract_and_obfuscate(
    file: UploadFile = File(...),
    obfuscations: str = "[]"
):
    """
    Extract text from file and obfuscate PII.

    Args:
        file: The file to process (PDF supported)
        obfuscations: JSON string of user-defined obfuscations

    Returns:
        Summary of processing with file ID for download
    """
    import json

    # Validate file size
    content = await file.read()
    if len(content) > config.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {config.MAX_FILE_SIZE // 1024 // 1024}MB"
        )

    # Parse obfuscations
    try:
        user_obfuscations = json.loads(obfuscations)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid obfuscations JSON")

    # Get processor
    mime_type = file.content_type or "application/pdf"
    processor = get_processor(mime_type)

    # Extract text
    pages = processor.extract_text(content)

    # Set up detectors
    user_detector = UserDefinedDetector(terms=user_obfuscations) if user_obfuscations else None

    # Set up obfuscator with custom placeholders for user-defined terms
    placeholder_map = dict(config.PLACEHOLDERS)
    for term in user_obfuscations:
        if term.get("replace_with"):
            placeholder_map[term.get("text")] = term.get("replace_with")

    obfuscator = TextObfuscator(placeholder_map)

    # Process each page
    processed_pages = []
    page_summaries = []
    total_matches = 0

    for page in pages:
        all_matches: list[PIIMatch] = []

        # User-defined obfuscations first (exact match)
        if user_detector:
            user_matches = user_detector.detect(page.text)
            # For user-defined with custom replacement, use text as type
            for match in user_matches:
                term_config = next(
                    (t for t in user_obfuscations if t.get("text") == match.text),
                    None
                )
                if term_config and term_config.get("replace_with"):
                    match.type = match.text  # Use text as key for custom replacement
            all_matches.extend(user_matches)

        # Pattern detectors
        for detector in config.ACTIVE_DETECTORS:
            detector_matches = detector.detect(page.text)
            # Filter out matches that overlap with existing matches
            for new_match in detector_matches:
                overlaps = any(
                    (new_match.start < existing.end and new_match.end > existing.start)
                    for existing in all_matches
                )
                if not overlaps:
                    all_matches.append(new_match)

        # Obfuscate
        processed_text = obfuscator.obfuscate(page.text, all_matches)

        processed_pages.append(ProcessedPage(
            page_number=page.page_number,
            original_text=page.text,
            processed_text=processed_text,
            metadata=page.metadata
        ))

        page_summaries.append(PageSummary(
            page_number=page.page_number,
            matches_found=len(all_matches),
            matches=[
                PIIMatchResponse(
                    text=m.text,
                    type=m.type,
                    start=m.start,
                    end=m.end
                )
                for m in all_matches
            ]
        ))

        total_matches += len(all_matches)

    # Reassemble and save
    output_content = processor.reassemble(processed_pages)
    file_id = storage.save(output_content)

    return ExtractResponse(
        file_id=file_id,
        page_count=len(pages),
        total_matches=total_matches,
        pages=page_summaries
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
            "Content-Disposition": f"attachment; filename=processed_{file_id}.pdf"
        }
    )
