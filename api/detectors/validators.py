"""
Validator functions for PII patterns.
These validate that matched text is actually valid PII (e.g., checksum validation).
"""
from typing import Callable, Optional


def israeli_id_checksum(id_number: str) -> bool:
    """
    Validate Israeli ID using the official checksum algorithm.
    Israeli IDs are 9 digits with a Luhn-like checksum.

    Args:
        id_number: String of 9 digits

    Returns:
        True if checksum is valid
    """
    # Remove any non-digit characters
    digits = "".join(c for c in id_number if c.isdigit())

    if len(digits) != 9:
        return False

    total = 0
    for i, digit in enumerate(digits):
        num = int(digit)
        if i % 2 == 1:
            num *= 2
        if num > 9:
            num = num // 10 + num % 10
        total += num

    return total % 10 == 0


def is_not_all_same_digit(value: str) -> bool:
    """
    Validate that value is not all the same digit (e.g., 000000000, 111111111).
    These are likely not real IDs.
    """
    digits = "".join(c for c in value if c.isdigit())
    if not digits:
        return False
    return len(set(digits)) > 1


def is_valid_phone_prefix(phone: str) -> bool:
    """
    Validate that phone has a valid Israeli prefix.
    Mobile: 050, 052, 053, 054, 055, 058
    """
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 10:
        return False

    valid_prefixes = ["050", "052", "053", "054", "055", "058"]
    return digits[:3] in valid_prefixes


# Registry of validators by name (used in config)
VALIDATORS: dict[str, Callable[[str], bool]] = {
    "israeli_id_checksum": israeli_id_checksum,
    "not_all_same_digit": is_not_all_same_digit,
    "valid_phone_prefix": is_valid_phone_prefix,
}


def get_validator(name: Optional[str]) -> Optional[Callable[[str], bool]]:
    """Get validator function by name."""
    if name is None:
        return None
    return VALIDATORS.get(name)
