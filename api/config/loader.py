import json
from pathlib import Path
from typing import Optional

from api.config.schemas import (
    ServerConfig,
    RequestConfig,
    MergedConfig,
    PIIPatternConfig,
)


# Path to the settings file
SETTINGS_PATH = Path(__file__).parent / "settings.json"


def load_server_config() -> ServerConfig:
    """Load server configuration from settings.json."""
    if not SETTINGS_PATH.exists():
        return ServerConfig()

    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return ServerConfig(**data)


def save_server_config(config: ServerConfig) -> None:
    """Save server configuration to settings.json."""
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(config.model_dump(), f, ensure_ascii=False, indent=2)


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
