"""
Shared text processing logic for detection and obfuscation.
"""
from typing import Optional

from api.config import (
    load_server_config,
    merge_config,
    RequestConfig,
    MergedConfig,
)
from api.detectors.regex import RegexDetector
from api.detectors.user_defined import UserDefinedDetector
from api.detectors.base import PIIMatch
from api.obfuscators.text import TextObfuscator
from api.replacements.mapper import ReplacementMapper

from api.routes.models import ExtractRequestConfig


# Load server config at startup
_server_config = load_server_config()


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


def create_detectors(merged_config: MergedConfig) -> tuple[RegexDetector, Optional[UserDefinedDetector]]:
    """Create detection components from config."""
    regex_detector = RegexDetector(patterns=merged_config.patterns)

    user_detector = None
    if merged_config.user_replacements:
        user_terms = [
            {"text": original, "type": "USER_DEFINED"}
            for original in merged_config.user_replacements.keys()
        ]
        user_detector = UserDefinedDetector(terms=user_terms)

    return regex_detector, user_detector


def create_obfuscation_components(merged_config: MergedConfig) -> tuple[ReplacementMapper, TextObfuscator]:
    """Create obfuscation components from config."""
    mapper = ReplacementMapper(
        user_mappings=merged_config.user_replacements,
        pools=merged_config.replacement_pools,
    )
    obfuscator = TextObfuscator(mapper=mapper)
    return mapper, obfuscator


def detect_pii(
    text: str,
    regex_detector: RegexDetector,
    user_detector: Optional[UserDefinedDetector],
) -> list[PIIMatch]:
    """Detect PII in text using available detectors."""
    all_matches: list[PIIMatch] = []

    # User-defined matches first (take priority)
    if user_detector:
        user_matches = user_detector.detect(text)
        all_matches.extend(user_matches)

    # Pattern-based detection
    pattern_matches = regex_detector.detect(text)

    # Filter out matches that overlap with existing matches
    for new_match in pattern_matches:
        overlaps = any(
            (new_match.start < existing.end and new_match.end > existing.start)
            for existing in all_matches
        )
        if not overlaps:
            all_matches.append(new_match)

    return all_matches
