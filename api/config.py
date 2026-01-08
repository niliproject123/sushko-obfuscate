from api.detectors.israeli_id import IsraeliIdDetector
from api.detectors.hebrew_name import HebrewNameDetector
from api.detectors.english_name import EnglishNameDetector


class Config:
    """Global application configuration."""

    PORT: int = 8000
    MAX_FILE_SIZE: int = 20 * 1024 * 1024  # 20MB
    FILE_TTL: int = 3600  # 1 hour

    ACTIVE_DETECTORS = [
        IsraeliIdDetector(),
        HebrewNameDetector(),
        EnglishNameDetector(),
    ]

    PLACEHOLDERS: dict[str, str] = {
        "NAME": "[NAME]",
        "ID": "[ID]",
        "USER_DEFINED": "[REDACTED]",
        "DEFAULT": "[REDACTED]",
    }


config = Config()
