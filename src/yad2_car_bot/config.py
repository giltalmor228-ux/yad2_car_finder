from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from yad2_car_bot.models import SearchProfile


@dataclass
class AppConfig:
    search_profile: SearchProfile
    filter_metadata: dict
    keyword_rules: dict
    scoring_rules: dict
    telegram_template: str
    base_dir: Path


def load_config(base_dir: Path | None = None) -> AppConfig:
    """Load all config/data files relative to *base_dir* (project root).

    If *base_dir* is None, auto-detect by walking up from this file looking
    for ``configs/search_profile_primary.json``.
    """
    if base_dir is None:
        base_dir = _find_project_root()

    base_dir = Path(base_dir).resolve()

    search_profile = SearchProfile.model_validate(
        _load_json(base_dir / "configs" / "search_profile_primary.json")
    )
    filter_metadata = _load_json(base_dir / "data" / "yad2_filter_metadata.json")
    keyword_rules = _load_json(base_dir / "configs" / "listing_keyword_rules.json")
    scoring_rules = _load_json(base_dir / "configs" / "scoring_rules.json")
    telegram_template = (base_dir / "docs" / "telegram_message_template.md").read_text(
        encoding="utf-8"
    )

    return AppConfig(
        search_profile=search_profile,
        filter_metadata=filter_metadata,
        keyword_rules=keyword_rules,
        scoring_rules=scoring_rules,
        telegram_template=telegram_template,
        base_dir=base_dir,
    )


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {path}")


def _find_project_root() -> Path:
    """Walk up from this module until we find configs/search_profile_primary.json."""
    candidate = Path(__file__).resolve().parent
    for _ in range(10):
        if (candidate / "configs" / "search_profile_primary.json").exists():
            return candidate
        candidate = candidate.parent
    raise RuntimeError(
        "Could not auto-detect project root. "
        "Pass base_dir explicitly to load_config()."
    )
