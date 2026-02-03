"""
Helper utilities for config endpoints to reduce code duplication.
"""
from contextlib import contextmanager
from typing import Generator

from fastapi import HTTPException

from api.config import (
    ServerConfig,
    load_server_config,
    save_server_config,
    reload_server_config,
)


def require_category(config: ServerConfig, category_name: str) -> list[str]:
    """
    Get category words or raise 404 if category doesn't exist.

    Returns the list of words in the category.
    """
    if category_name not in config.categories:
        raise HTTPException(
            status_code=404,
            detail=f"Category '{category_name}' not found"
        )
    return config.categories[category_name]


@contextmanager
def config_transaction() -> Generator[ServerConfig, None, None]:
    """
    Context manager that loads config, yields it for modification,
    then saves and reloads automatically.

    Usage:
        with config_transaction() as config:
            config.categories["new"] = ["word1", "word2"]
        # Config is automatically saved and reloaded
    """
    config = load_server_config()
    yield config
    save_server_config(config)
    reload_server_config()
