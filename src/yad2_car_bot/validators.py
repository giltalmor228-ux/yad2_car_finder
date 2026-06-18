from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yad2_car_bot.config import AppConfig

logger = logging.getLogger(__name__)

# Severity constants
ERROR = "ERROR"
WARNING = "WARNING"


def validate_config(config: "AppConfig") -> list[tuple[str, str]]:
    """Validate the loaded config.

    Returns a list of (severity, message) tuples.
    Severity is "ERROR" or "WARNING".
    Callers should treat any ERROR as a fatal startup failure.
    """
    issues: list[tuple[str, str]] = []

    profile = config.search_profile
    metadata = config.filter_metadata.get("manufacturers", {})

    # Collect active manufacturer IDs from the search profile
    active: dict[str, int | None] = {}
    for name, entry in profile.cars.items():
        active[name] = entry.manufacturer_id

    # FAIL: any active manufacturer with no ID
    for name, mfr_id in active.items():
        if mfr_id is None:
            issues.append(
                (ERROR, f"Manufacturer '{name}' has no ID in the search profile.")
            )

    # FAIL: duplicate IDs among active manufacturers
    seen_ids: dict[int, str] = {}
    for name, mfr_id in active.items():
        if mfr_id is None:
            continue
        if mfr_id in seen_ids:
            issues.append(
                (
                    ERROR,
                    f"Duplicate manufacturer ID {mfr_id} used by both "
                    f"'{seen_ids[mfr_id]}' and '{name}'.",
                )
            )
        else:
            seen_ids[mfr_id] = name

    # WARN: manual_verify_once manufacturers
    for str_id, meta in metadata.items():
        if meta.get("verification_status") == "manual_verify_once":
            name_en = meta.get("name_en", str_id)
            issues.append(
                (
                    WARNING,
                    f"Manufacturer '{name_en}' (ID {str_id}) has status "
                    f"'manual_verify_once'. Verify this ID manually before relying on it.",
                )
            )

    return issues


def assert_valid_config(config: "AppConfig") -> None:
    """Raise RuntimeError if there are any ERROR-level config issues.

    Logs warnings but does not raise for them.
    """
    issues = validate_config(config)
    errors = [msg for sev, msg in issues if sev == ERROR]
    warnings = [msg for sev, msg in issues if sev == WARNING]

    for msg in warnings:
        logger.warning("CONFIG WARNING: %s", msg)

    if errors:
        combined = "\n".join(f"  - {e}" for e in errors)
        raise RuntimeError(f"Config validation failed:\n{combined}")
