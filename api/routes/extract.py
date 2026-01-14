"""
PDF extraction and anonymization endpoint.
"""
import json

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import Response

from api.processors.pdf import PDFProcessor
from api.processors.base import ProcessedPage
from api.storage.temp import storage

from api.routes.models import (
    ExtractRequestConfig,
    ExtractResponse,
    PlainTextRequest,
    PlainTextResponse,
    PIIMatchResponse,
    PageSummary,
)
from api.routes.processing import (
    get_merged_config,
    create_detectors,
    create_obfuscation_components,
    detect_pii,
)


router = APIRouter()

# Max file size (20MB)
MAX_FILE_SIZE = 20 * 1024 * 1024


@router.post("/extract", response_model=ExtractResponse)
async def extract_and_obfuscate(
    file: UploadFile = File(...),
    config: str = Form(default="{}"),
):
    """Extract text from PDF and obfuscate PII."""
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

    # Create components
    processor = PDFProcessor(ocr_config=merged_config.ocr)
    regex_detector, user_detector = create_detectors(merged_config)
    mapper, obfuscator = create_obfuscation_components(merged_config)

    # Extract text from PDF
    pages = processor.extract_text(content, force_ocr=merged_config.force_ocr)

    # Collect warnings
    warnings = _collect_warnings(pages)

    # Process each page
    processed_pages = []
    page_summaries = []
    total_matches = 0

    for page in pages:
        all_matches = detect_pii(page.text, regex_detector, user_detector)

        # Obfuscate text
        processed_text = obfuscator.obfuscate(page.text, all_matches)

        # Build processed page
        processed_pages.append(ProcessedPage(
            page_number=page.page_number,
            original_text=page.text,
            processed_text=processed_text,
            metadata=page.metadata,
        ))

        # Build page summary
        match_responses = [
            PIIMatchResponse(
                text=match.text,
                type=match.type,
                start=match.start,
                end=match.end,
                pattern_name=match.pattern_name,
                replacement=mapper.get_replacement(
                    original=match.text,
                    pii_type=match.type,
                    pattern_name=match.pattern_name,
                ),
            )
            for match in all_matches
        ]

        page_summaries.append(PageSummary(
            page_number=page.page_number,
            matches_found=len(all_matches),
            matches=match_responses,
        ))

        total_matches += len(all_matches)

    # Collect obfuscated text and reassemble PDF
    full_obfuscated_text = "\n\n".join(page.processed_text for page in processed_pages)
    output_content = processor.reassemble(processed_pages)
    file_id = storage.save(output_content)

    return ExtractResponse(
        file_id=file_id,
        page_count=len(pages),
        total_matches=total_matches,
        pages=page_summaries,
        mappings_used=mapper.get_all_mappings(),
        warnings=warnings,
        obfuscated_text=full_obfuscated_text,
    )


def _collect_warnings(pages) -> list[str]:
    """Collect warnings from processed pages."""
    warnings = []
    is_image_based = False

    for page in pages:
        if page.metadata:
            if page.metadata.get("is_image_based"):
                is_image_based = True
            if "warning" in page.metadata:
                page_warning = page.metadata["warning"]
                if page_warning not in warnings:
                    warnings.append(page_warning)

    if is_image_based:
        ocr_method = any(
            page.metadata and page.metadata.get("extraction_method") == "ocr"
            for page in pages
        )
        if ocr_method:
            warnings.insert(0, "This PDF is image-based and was processed using OCR. Text extraction accuracy may vary.")
        elif "PDF appears to be image-based but OCR is disabled" not in warnings:
            warnings.insert(0, "This PDF appears to be image-based. OCR was used for text extraction.")

    return warnings


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
    """Extract and anonymize text, returning text instead of PDF."""
    return await extract_and_obfuscate(file=file, config=config)


@router.post("/extract/plain", response_model=PlainTextResponse)
async def extract_plain_text(request: PlainTextRequest):
    """Process plain text and obfuscate PII."""
    merged_config = get_merged_config(request.config)

    regex_detector, user_detector = create_detectors(merged_config)
    mapper, obfuscator = create_obfuscation_components(merged_config)

    all_matches = detect_pii(request.text, regex_detector, user_detector)
    obfuscated_text = obfuscator.obfuscate(request.text, all_matches)

    return PlainTextResponse(
        total_matches=len(all_matches),
        mappings_used=mapper.get_all_mappings(),
        obfuscated_text=obfuscated_text,
        warnings=[],
    )
