"""
Configuration management endpoints.
Allows admin to view and update server configuration.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from api.config import (
    PIIPatternConfig,
    ReplacementPoolsConfig,
    OCRConfig,
    load_server_config,
    save_server_config,
    reload_server_config,
)
from api.routes.config_helpers import require_category, config_transaction


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
    disabled_categories: list[str] = Field(default_factory=list)


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
        disabled_categories=config.disabled_categories,
    )


@router.put("/config", response_model=ConfigResponse)
async def update_config(request: UpdateConfigRequest):
    """
    Update server configuration.

    Only provided fields will be updated; others remain unchanged.
    """
    with config_transaction() as current:
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

        response = ConfigResponse(
            patterns=current.patterns,
            replacement_pools=current.replacement_pools,
            ocr=current.ocr,
            placeholders=current.placeholders,
            categories=current.categories,
            disabled_categories=current.disabled_categories,
        )

    return response


@router.get("/config/patterns", response_model=list[PIIPatternConfig])
async def get_patterns():
    """Get all PII detection patterns."""
    config = load_server_config()
    return config.patterns


@router.post("/config/patterns", response_model=PIIPatternConfig)
async def add_pattern(request: PatternUpdateRequest):
    """Add a new PII detection pattern."""
    with config_transaction() as config:
        if any(p.name == request.pattern.name for p in config.patterns):
            raise HTTPException(
                status_code=400,
                detail=f"Pattern with name '{request.pattern.name}' already exists"
            )
        config.patterns.append(request.pattern)

    return request.pattern


@router.put("/config/patterns/{pattern_name}", response_model=PIIPatternConfig)
async def update_pattern(pattern_name: str, request: PatternUpdateRequest):
    """Update an existing PII detection pattern."""
    with config_transaction() as config:
        for i, pattern in enumerate(config.patterns):
            if pattern.name == pattern_name:
                config.patterns[i] = request.pattern
                return request.pattern

        raise HTTPException(status_code=404, detail=f"Pattern '{pattern_name}' not found")


@router.delete("/config/patterns/{pattern_name}")
async def delete_pattern(pattern_name: str):
    """Delete a PII detection pattern."""
    with config_transaction() as config:
        original_count = len(config.patterns)
        config.patterns = [p for p in config.patterns if p.name != pattern_name]

        if len(config.patterns) == original_count:
            raise HTTPException(status_code=404, detail=f"Pattern '{pattern_name}' not found")

    return {"message": f"Pattern '{pattern_name}' deleted"}


@router.get("/config/pools", response_model=ReplacementPoolsConfig)
async def get_replacement_pools():
    """Get all replacement pools."""
    config = load_server_config()
    return config.replacement_pools


@router.put("/config/pools/{pool_name}")
async def update_replacement_pool(pool_name: str, request: PoolUpdateRequest):
    """Update a specific replacement pool."""
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

    with config_transaction() as config:
        setattr(config.replacement_pools, pool_name, request.values)

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
    with config_transaction() as config:
        if category_name in config.categories:
            raise HTTPException(
                status_code=400,
                detail=f"Category '{category_name}' already exists"
            )
        config.categories[category_name] = request.words

    return {"message": f"Category '{category_name}' created", "words": request.words}


@router.put("/config/categories/{category_name}")
async def update_category(category_name: str, request: CategoryRequest):
    """Update all words in a category."""
    with config_transaction() as config:
        require_category(config, category_name)
        config.categories[category_name] = request.words

    return {"message": f"Category '{category_name}' updated", "words": request.words}


@router.delete("/config/categories/{category_name}")
async def delete_category(category_name: str):
    """Delete a category."""
    with config_transaction() as config:
        require_category(config, category_name)
        del config.categories[category_name]

    return {"message": f"Category '{category_name}' deleted"}


@router.get("/config/categories/{category_name}/words")
async def get_category_words(category_name: str):
    """Get all words in a category."""
    config = load_server_config()
    words = require_category(config, category_name)
    return {"category": category_name, "words": words}


@router.post("/config/categories/{category_name}/words")
async def add_word_to_category(category_name: str, request: WordRequest):
    """Add a word to a category."""
    with config_transaction() as config:
        words = require_category(config, category_name)

        if request.word in words:
            raise HTTPException(
                status_code=400,
                detail=f"Word '{request.word}' already exists in category"
            )

        words.append(request.word)

    return {"message": f"Word '{request.word}' added to '{category_name}'"}


@router.delete("/config/categories/{category_name}/words/{word}")
async def remove_word_from_category(category_name: str, word: str):
    """Remove a word from a category."""
    with config_transaction() as config:
        words = require_category(config, category_name)

        if word not in words:
            raise HTTPException(
                status_code=404,
                detail=f"Word '{word}' not found in category"
            )

        words.remove(word)

    return {"message": f"Word '{word}' removed from '{category_name}'"}


@router.put("/config/categories/{category_name}/toggle")
async def toggle_category(category_name: str):
    """Toggle a category's enabled/disabled state."""
    with config_transaction() as config:
        require_category(config, category_name)

        if category_name in config.disabled_categories:
            config.disabled_categories.remove(category_name)
            enabled = True
        else:
            config.disabled_categories.append(category_name)
            enabled = False

    return {"category": category_name, "enabled": enabled}
