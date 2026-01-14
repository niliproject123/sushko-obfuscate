import json
from pathlib import Path
from typing import Optional

from api.config.schemas import (
    ServerConfig,
    RequestConfig,
    MergedConfig,
    PIIPatternConfig,
)


# Paths to config files
CONFIG_DIR = Path(__file__).parent
SETTINGS_PATH = CONFIG_DIR / "settings.json"
PATTERNS_PATH = CONFIG_DIR / "patterns.json"
POOLS_PATH = CONFIG_DIR / "pools.json"
REPLACEMENTS_PATH = CONFIG_DIR / "replacements.json"
CATEGORIES_PATH = CONFIG_DIR / "categories.json"


def _load_json(path: Path) -> dict | list:
    """Load JSON file if it exists."""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_server_config() -> ServerConfig:
    """Load server configuration from split config files."""
    # Load main settings
    settings = _load_json(SETTINGS_PATH) if SETTINGS_PATH.exists() else {}

    # Load patterns from separate file
    patterns = _load_json(PATTERNS_PATH) if PATTERNS_PATH.exists() else []

    # Load pools from separate file
    pools = _load_json(POOLS_PATH) if POOLS_PATH.exists() else {}

    # Load replacements from separate file
    replacements = _load_json(REPLACEMENTS_PATH) if REPLACEMENTS_PATH.exists() else {}

    # Load categories from separate file
    categories = _load_json(CATEGORIES_PATH) if CATEGORIES_PATH.exists() else {}

    # Merge into single config
    return ServerConfig(
        patterns=patterns,
        replacement_pools=pools,
        default_replacements=replacements,
        ocr=settings.get("ocr", {}),
        placeholders=settings.get("placeholders", {}),
        categories=categories,
        disabled_categories=settings.get("disabled_categories", []),
    )


def save_server_config(config: ServerConfig) -> None:
    """Save server configuration to split config files."""
    # Save patterns
    with open(PATTERNS_PATH, "w", encoding="utf-8") as f:
        patterns_data = [p.model_dump() for p in config.patterns]
        json.dump(patterns_data, f, ensure_ascii=False, indent=2)

    # Save pools
    with open(POOLS_PATH, "w", encoding="utf-8") as f:
        json.dump(config.replacement_pools.model_dump(), f, ensure_ascii=False, indent=2)

    # Save replacements
    with open(REPLACEMENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(config.default_replacements, f, ensure_ascii=False, indent=2)

    # Save categories
    with open(CATEGORIES_PATH, "w", encoding="utf-8") as f:
        json.dump(config.categories, f, ensure_ascii=False, indent=2)

    # Save main settings (ocr + placeholders + disabled_categories)
    settings = {
        "ocr": config.ocr.model_dump(),
        "placeholders": config.placeholders,
        "disabled_categories": config.disabled_categories,
    }
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def merge_config(
    server_config: Optional[ServerConfig] = None,
    request_config: Optional[RequestConfig] = None,
) -> MergedConfig:
    """
    Merge server configuration with request overrides.

    Request config can:
    - Add user_replacements (exact string mappings)
    - Disable specific detectors by name
    - Force OCR processing
    - Add custom patterns
    """
    if server_config is None:
        server_config = load_server_config()

    if request_config is None:
        request_config = RequestConfig()

    # Filter out disabled patterns
    enabled_patterns = [
        p for p in server_config.patterns
        if p.enabled and p.name not in request_config.disabled_detectors
    ]

    # Add custom patterns from request
    all_patterns = enabled_patterns + request_config.custom_patterns

    # Determine OCR setting
    force_ocr = request_config.force_ocr

    # Merge default_replacements with request user_replacements
    # Request overrides take precedence
    merged_replacements = {**server_config.default_replacements, **request_config.user_replacements}

    return MergedConfig(
        patterns=all_patterns,
        replacement_pools=server_config.replacement_pools,
        ocr=server_config.ocr,
        placeholders=server_config.placeholders,
        user_replacements=merged_replacements,
        force_ocr=force_ocr,
        categories=server_config.categories,
        disabled_categories=server_config.disabled_categories,
    )


# Cached server config (reload on demand)
_cached_server_config: Optional[ServerConfig] = None


def get_server_config(reload: bool = False) -> ServerConfig:
    """Get cached server config, optionally reloading from disk."""
    global _cached_server_config
    if _cached_server_config is None or reload:
        _cached_server_config = load_server_config()
    return _cached_server_config


def reload_server_config() -> ServerConfig:
    """Force reload server config from disk."""
    return get_server_config(reload=True)
