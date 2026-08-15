from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from yad2_car_bot.url_builder import MAX_MANUFACTURERS_PER_GROUP, MAX_MODELS_PER_GROUP

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

    issues.extend(_validate_search_groups(config))
    return issues


def _validate_search_groups(config: "AppConfig") -> list[tuple[str, str]]:
    """Validate ``search_groups``: ≤4 manufacturers and ≤4 models per group."""
    issues: list[tuple[str, str]] = []
    groups = config.search_profile.search_groups
    if not groups:
        return issues

    known_mfr_ids = {
        entry.manufacturer_id
        for entry in config.search_profile.cars.values()
        if entry.manufacturer_id is not None
    }
    # Also accept IDs documented in filter metadata.
    known_mfr_ids.update(int(str_id) for str_id in config.filter_metadata.get("manufacturers", {}))

    catalog_ids = {
        int(row["yad2_model_id"])
        for row in config.model_catalog
        if row.get("yad2_model_id") is not None
    }

    seen_models_across: dict[int, int] = {}
    for group_index, group in enumerate(groups, start=1):
        if not group.manufacturers:
            issues.append(
                (
                    ERROR,
                    f"search_groups[{group_index}].manufacturers is empty. "
                    f"Add 1–{MAX_MANUFACTURERS_PER_GROUP} manufacturer IDs.",
                )
            )
        elif len(group.manufacturers) > MAX_MANUFACTURERS_PER_GROUP:
            issues.append(
                (
                    ERROR,
                    f"search_groups[{group_index}] has {len(group.manufacturers)} "
                    f"manufacturers; Yad2 allows at most {MAX_MANUFACTURERS_PER_GROUP} "
                    "per search.",
                )
            )

        for mfr_id in group.manufacturers:
            if mfr_id not in known_mfr_ids:
                issues.append(
                    (
                        ERROR,
                        f"search_groups[{group_index}] references unknown manufacturer "
                        f"ID {mfr_id}.",
                    )
                )

        if len(group.models) > MAX_MODELS_PER_GROUP:
            issues.append(
                (
                    ERROR,
                    f"search_groups[{group_index}] has {len(group.models)} model IDs; "
                    f"Yad2 allows at most {MAX_MODELS_PER_GROUP} models total per "
                    "search group.",
                )
            )

        for model_id in group.models:
            if model_id not in catalog_ids:
                issues.append(
                    (
                        ERROR,
                        f"search_groups[{group_index}] contains unknown model ID "
                        f"{model_id} (not found in data/yad2_car_models_flat.json).",
                    )
                )
            if model_id in seen_models_across:
                issues.append(
                    (
                        WARNING,
                        f"Model ID {model_id} appears in both "
                        f"search_groups[{seen_models_across[model_id]}] and "
                        f"search_groups[{group_index}].",
                    )
                )
            else:
                seen_models_across[model_id] = group_index

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
