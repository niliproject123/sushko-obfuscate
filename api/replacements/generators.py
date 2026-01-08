"""
Generators for fake PII values.
These generate realistic-looking but fake values for replacement.
"""
import random
from typing import Optional


def generate_israeli_id(seed: Optional[int] = None) -> str:
    """
    Generate a valid 9-digit Israeli ID with correct checksum.
    Uses seed for reproducibility if provided.
    """
    if seed is not None:
        random.seed(seed)

    # Generate first 8 random digits
    digits = [random.randint(0, 9) for _ in range(8)]

    # Calculate checksum digit (Luhn-like algorithm)
    total = 0
    for i, digit in enumerate(digits):
        num = digit
        if i % 2 == 1:
            num *= 2
        if num > 9:
            num = num // 10 + num % 10
        total += num

    # Checksum digit makes total divisible by 10
    checksum = (10 - (total % 10)) % 10
    digits.append(checksum)

    return "".join(str(d) for d in digits)


def generate_phone(prefix: str = "050", seed: Optional[int] = None) -> str:
    """
    Generate an Israeli mobile phone number.
    Format: 05X-XXXXXXX
    """
    if seed is not None:
        random.seed(seed)

    prefixes = ["050", "052", "053", "054", "055", "058"]
    if prefix not in prefixes:
        prefix = random.choice(prefixes)

    suffix = "".join(str(random.randint(0, 9)) for _ in range(7))
    return f"{prefix}-{suffix}"


def generate_email(name: Optional[str] = None, seed: Optional[int] = None) -> str:
    """
    Generate a fake email address.
    Uses example.com domain (RFC 2606 reserved for documentation).
    """
    if seed is not None:
        random.seed(seed)

    if name:
        # Convert Hebrew/English name to email-safe format
        local = name.lower().replace(" ", ".").replace("'", "")
        # For Hebrew, transliterate or use generic
        if any("\u0590" <= c <= "\u05FF" for c in local):
            local = f"user{random.randint(100, 999)}"
    else:
        local = f"user{random.randint(100, 999)}"

    return f"{local}@example.com"


def generate_bank_account(length: int = 7, seed: Optional[int] = None) -> str:
    """Generate a fake bank account number."""
    if seed is not None:
        random.seed(seed)

    return "".join(str(random.randint(0, 9)) for _ in range(length))


def generate_case_number(length: int = 8, seed: Optional[int] = None) -> str:
    """Generate a fake case/file number."""
    if seed is not None:
        random.seed(seed)

    return "".join(str(random.randint(0, 9)) for _ in range(length))


def generate_license_number(length: int = 5, seed: Optional[int] = None) -> str:
    """Generate a fake medical license number."""
    if seed is not None:
        random.seed(seed)

    return "".join(str(random.randint(0, 9)) for _ in range(length))


def generate_branch_code(seed: Optional[int] = None) -> str:
    """Generate a fake bank branch code (3 digits)."""
    if seed is not None:
        random.seed(seed)

    return str(random.randint(100, 999))
