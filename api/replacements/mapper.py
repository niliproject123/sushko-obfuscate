"""
ReplacementMapper - maintains consistent mappings between original and fake values.
Ensures the same original value always maps to the same fake value within a session.
"""
from typing import Optional
from api.config.schemas import ReplacementPoolsConfig
from api.replacements import generators


class ReplacementMapper:
    """
    Maps original PII values to fake replacements with consistency.

    Priority:
    1. User-defined mappings (explicit: "מיכאל" -> "דוד")
    2. Previously assigned auto-mappings (consistency within document)
    3. Pool-based assignment (pick next from pool)
    4. Generated values (for IDs, phones, etc.)
    """

    def __init__(
        self,
        user_mappings: Optional[dict[str, str]] = None,
        pools: Optional[ReplacementPoolsConfig] = None,
    ):
        self.user_mappings = user_mappings or {}
        self.pools = pools or ReplacementPoolsConfig()

        # Auto-assigned mappings (original -> fake)
        self._auto_mappings: dict[str, str] = {}

        # Track which user mappings were actually used
        self._used_user_mappings: dict[str, str] = {}

        # Track pool usage indices per type
        self._pool_indices: dict[str, int] = {
            "name_hebrew_first": 0,
            "name_hebrew_last": 0,
            "name_english_first": 0,
            "name_english_last": 0,
            "city": 0,
            "street": 0,
        }

        # Track generated value counters for uniqueness
        self._generated_counters: dict[str, int] = {
            "ID": 0,
            "PHONE": 0,
            "EMAIL": 0,
            "BANK_ACCOUNT": 0,
            "BANK_BRANCH": 0,
            "CASE_NUMBER": 0,
            "LICENSE": 0,
        }

    def get_replacement(self, original: str, pii_type: str, pattern_name: str = "") -> str:
        """
        Get replacement value for an original PII value.

        Args:
            original: The original PII text found in document
            pii_type: Type of PII ("NAME", "ID", "PHONE", etc.)
            pattern_name: Specific pattern name for more granular pool selection

        Returns:
            The fake replacement value
        """
        # Strip whitespace for consistent lookup
        original_clean = original.strip()

        # 1. Check user-defined mappings first
        if original_clean in self.user_mappings:
            replacement = self.user_mappings[original_clean]
            # Track that this user mapping was actually used
            self._used_user_mappings[original_clean] = replacement
            return replacement

        # 2. Check if we already assigned a fake for this original
        if original_clean in self._auto_mappings:
            return self._auto_mappings[original_clean]

        # 3. Generate or pick from pool
        fake = self._get_new_replacement(original_clean, pii_type, pattern_name)
        self._auto_mappings[original_clean] = fake
        return fake

    def _get_new_replacement(self, original: str, pii_type: str, pattern_name: str) -> str:
        """Generate a new replacement value based on PII type."""

        if pii_type == "NAME":
            return self._get_name_replacement(pattern_name)

        elif pii_type == "ID":
            return self._generate_unique("ID", generators.generate_israeli_id)

        elif pii_type == "PHONE":
            return self._generate_unique("PHONE", generators.generate_phone)

        elif pii_type == "EMAIL":
            return self._generate_unique("EMAIL", generators.generate_email)

        elif pii_type == "ADDRESS":
            return self._get_address_replacement(pattern_name)

        elif pii_type == "BANK_ACCOUNT":
            return self._generate_unique("BANK_ACCOUNT", generators.generate_bank_account)

        elif pii_type == "BANK_BRANCH":
            return self._generate_unique("BANK_BRANCH", generators.generate_branch_code)

        elif pii_type == "CASE_NUMBER":
            return self._generate_unique("CASE_NUMBER", generators.generate_case_number)

        elif pii_type == "LICENSE":
            return self._generate_unique("LICENSE", generators.generate_license_number)

        else:
            # Fallback - return generic placeholder
            return "[REDACTED]"

    def _get_name_replacement(self, pattern_name: str) -> str:
        """Get a name replacement from the appropriate pool."""
        # Determine which pool based on pattern name
        if "hebrew" in pattern_name.lower():
            if "last" in pattern_name.lower() or "משפחה" in pattern_name:
                return self._next_from_pool("name_hebrew_last", self.pools.name_hebrew_last)
            else:
                return self._next_from_pool("name_hebrew_first", self.pools.name_hebrew_first)
        elif "english" in pattern_name.lower():
            if "last" in pattern_name.lower():
                return self._next_from_pool("name_english_last", self.pools.name_english_last)
            else:
                return self._next_from_pool("name_english_first", self.pools.name_english_first)
        else:
            # Default to Hebrew first name
            return self._next_from_pool("name_hebrew_first", self.pools.name_hebrew_first)

    def _get_address_replacement(self, pattern_name: str) -> str:
        """Get an address replacement from the appropriate pool."""
        if "city" in pattern_name.lower() or "ישוב" in pattern_name:
            return self._next_from_pool("city", self.pools.city)
        elif "street" in pattern_name.lower() or "רחוב" in pattern_name:
            return self._next_from_pool("street", self.pools.street)
        else:
            return self._next_from_pool("city", self.pools.city)

    def _next_from_pool(self, pool_name: str, pool: list[str]) -> str:
        """Get next value from a pool, cycling if needed."""
        if not pool:
            return "[REDACTED]"

        index = self._pool_indices.get(pool_name, 0)
        value = pool[index % len(pool)]
        self._pool_indices[pool_name] = index + 1
        return value

    def _generate_unique(self, counter_key: str, generator_func) -> str:
        """Generate a unique value using the counter as seed."""
        counter = self._generated_counters.get(counter_key, 0)
        value = generator_func(seed=counter + 1000)  # Offset seed for variety
        self._generated_counters[counter_key] = counter + 1
        return value

    def get_all_mappings(self) -> dict[str, str]:
        """
        Get all mappings that were actually used during processing.
        Returns only user-defined mappings that were looked up + auto-assigned mappings.
        Useful for returning in API response.
        """
        all_mappings = {}
        all_mappings.update(self._auto_mappings)
        all_mappings.update(self._used_user_mappings)  # Only user mappings that were actually used
        return all_mappings

    def get_auto_mappings(self) -> dict[str, str]:
        """Get only auto-assigned mappings."""
        return self._auto_mappings.copy()

    def add_user_mapping(self, original: str, replacement: str) -> None:
        """Add a user-defined mapping."""
        self.user_mappings[original.strip()] = replacement
