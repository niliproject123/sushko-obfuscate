"""
Configuration management endpoints.
Allows admin to view and update server configuration.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from api.config import (
    ServerConfig,
    PIIPatternConfig,
    ReplacementPoolsConfig,
    OCRConfig,
    load_server_config,
    save_server_config,
    reload_server_config,
)


router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================

class ConfigResponse(BaseModel):
    """Response model for configuration."""
    patterns: list[PIIPatternConfig]
    replacement_pools: ReplacementPoolsConfig
    ocr: OCRConfig
    placeholders: dict[str, str]
    categories: dict[str, list[str]] = Field(default_factory=dict)


class UpdateConfigRequest(BaseModel):
    """Request model for updating configuration."""
    patterns: Optional[list[PIIPatternConfig]] = None
    replacement_pools: Optional[ReplacementPoolsConfig] = None
    ocr: Optional[OCRConfig] = None
    placeholders: Optional[dict[str, str]] = None
    categories: Optional[dict[str, list[str]]] = None


class PatternUpdateRequest(BaseModel):
    """Request model for updating a single pattern."""
    pattern: PIIPatternConfig


class PoolUpdateRequest(BaseModel):
    """Request model for updating replacement pools."""
    pool_name: str
    values: list[str]


class CategoryRequest(BaseModel):
    """Request model for category operations."""
    words: list[str] = Field(default_factory=list)


class WordRequest(BaseModel):
    """Request model for word operations."""
    word: str


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """
    Get current server configuration.

    Returns all patterns, replacement pools, OCR settings, placeholders, and categories.
    """
    config = load_server_config()
    return ConfigResponse(
        patterns=config.patterns,
        replacement_pools=config.replacement_pools,
        ocr=config.ocr,
        placeholders=config.placeholders,
        categories=config.categories,
    )


@router.put("/config", response_model=ConfigResponse)
async def update_config(request: UpdateConfigRequest):
    """
    Update server configuration.

    Only provided fields will be updated; others remain unchanged.
    """
    current = load_server_config()

    # Update only provided fields
    if request.patterns is not None:
        current.patterns = request.patterns
    if request.replacement_pools is not None:
        current.replacement_pools = request.replacement_pools
    if request.ocr is not None:
        current.ocr = request.ocr
    if request.placeholders is not None:
        current.placeholders = request.placeholders
    if request.categories is not None:
        current.categories = request.categories

    # Save and reload
    save_server_config(current)
    reload_server_config()

    return ConfigResponse(
        patterns=current.patterns,
        replacement_pools=current.replacement_pools,
        ocr=current.ocr,
        placeholders=current.placeholders,
        categories=current.categories,
    )


@router.get("/config/patterns", response_model=list[PIIPatternConfig])
async def get_patterns():
    """Get all PII detection patterns."""
    config = load_server_config()
    return config.patterns


@router.post("/config/patterns", response_model=PIIPatternConfig)
async def add_pattern(request: PatternUpdateRequest):
    """Add a new PII detection pattern."""
    config = load_server_config()

    # Check for duplicate name
    if any(p.name == request.pattern.name for p in config.patterns):
        raise HTTPException(
            status_code=400,
            detail=f"Pattern with name '{request.pattern.name}' already exists"
        )

    config.patterns.append(request.pattern)
    save_server_config(config)
    reload_server_config()

    return request.pattern


@router.put("/config/patterns/{pattern_name}", response_model=PIIPatternConfig)
async def update_pattern(pattern_name: str, request: PatternUpdateRequest):
    """Update an existing PII detection pattern."""
    config = load_server_config()

    # Find and update pattern
    for i, pattern in enumerate(config.patterns):
        if pattern.name == pattern_name:
            config.patterns[i] = request.pattern
            save_server_config(config)
            reload_server_config()
            return request.pattern

    raise HTTPException(status_code=404, detail=f"Pattern '{pattern_name}' not found")


@router.delete("/config/patterns/{pattern_name}")
async def delete_pattern(pattern_name: str):
    """Delete a PII detection pattern."""
    config = load_server_config()

    original_count = len(config.patterns)
    config.patterns = [p for p in config.patterns if p.name != pattern_name]

    if len(config.patterns) == original_count:
        raise HTTPException(status_code=404, detail=f"Pattern '{pattern_name}' not found")

    save_server_config(config)
    reload_server_config()

    return {"message": f"Pattern '{pattern_name}' deleted"}


@router.get("/config/pools", response_model=ReplacementPoolsConfig)
async def get_replacement_pools():
    """Get all replacement pools."""
    config = load_server_config()
    return config.replacement_pools


@router.put("/config/pools/{pool_name}")
async def update_replacement_pool(pool_name: str, request: PoolUpdateRequest):
    """Update a specific replacement pool."""
    config = load_server_config()

    # Valid pool names
    valid_pools = [
        "name_hebrew_first",
        "name_hebrew_last",
        "name_english_first",
        "name_english_last",
        "city",
        "street",
    ]

    if pool_name not in valid_pools:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid pool name. Valid names: {valid_pools}"
        )

    # Update the pool
    setattr(config.replacement_pools, pool_name, request.values)
    save_server_config(config)
    reload_server_config()

    return {"message": f"Pool '{pool_name}' updated", "values": request.values}


@router.post("/config/reload")
async def reload_config():
    """
    Reload configuration from disk.

    Useful if settings.json was modified externally.
    """
    reload_server_config()
    return {"message": "Configuration reloaded"}


# ============================================================================
# Category Endpoints
# ============================================================================

@router.get("/config/categories")
async def get_categories():
    """Get all word categories for PII detection."""
    config = load_server_config()
    return config.categories


@router.post("/config/categories/{category_name}")
async def create_category(category_name: str, request: CategoryRequest):
    """Create a new category with optional initial words."""
    config = load_server_config()

    if category_name in config.categories:
        raise HTTPException(
            status_code=400,
            detail=f"Category '{category_name}' already exists"
        )

    config.categories[category_name] = request.words
    save_server_config(config)
    reload_server_config()

    return {"message": f"Category '{category_name}' created", "words": request.words}


@router.put("/config/categories/{category_name}")
async def update_category(category_name: str, request: CategoryRequest):
    """Update all words in a category."""
    config = load_server_config()

    if category_name not in config.categories:
        raise HTTPException(
            status_code=404,
            detail=f"Category '{category_name}' not found"
        )

    config.categories[category_name] = request.words
    save_server_config(config)
    reload_server_config()

    return {"message": f"Category '{category_name}' updated", "words": request.words}


@router.delete("/config/categories/{category_name}")
async def delete_category(category_name: str):
    """Delete a category."""
    config = load_server_config()

    if category_name not in config.categories:
        raise HTTPException(
            status_code=404,
            detail=f"Category '{category_name}' not found"
        )

    del config.categories[category_name]
    save_server_config(config)
    reload_server_config()

    return {"message": f"Category '{category_name}' deleted"}


@router.get("/config/categories/{category_name}/words")
async def get_category_words(category_name: str):
    """Get all words in a category."""
    config = load_server_config()

    if category_name not in config.categories:
        raise HTTPException(
            status_code=404,
            detail=f"Category '{category_name}' not found"
        )

    return {"category": category_name, "words": config.categories[category_name]}


@router.post("/config/categories/{category_name}/words")
async def add_word_to_category(category_name: str, request: WordRequest):
    """Add a word to a category."""
    config = load_server_config()

    if category_name not in config.categories:
        raise HTTPException(
            status_code=404,
            detail=f"Category '{category_name}' not found"
        )

    if request.word in config.categories[category_name]:
        raise HTTPException(
            status_code=400,
            detail=f"Word '{request.word}' already exists in category"
        )

    config.categories[category_name].append(request.word)
    save_server_config(config)
    reload_server_config()

    return {"message": f"Word '{request.word}' added to '{category_name}'"}


@router.delete("/config/categories/{category_name}/words/{word}")
async def remove_word_from_category(category_name: str, word: str):
    """Remove a word from a category."""
    config = load_server_config()

    if category_name not in config.categories:
        raise HTTPException(
            status_code=404,
            detail=f"Category '{category_name}' not found"
        )

    if word not in config.categories[category_name]:
        raise HTTPException(
            status_code=404,
            detail=f"Word '{word}' not found in category"
        )

    config.categories[category_name].remove(word)
    save_server_config(config)
    reload_server_config()

    return {"message": f"Word '{word}' removed from '{category_name}'"}
