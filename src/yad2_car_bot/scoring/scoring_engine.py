from __future__ import annotations

import re
from typing import Optional

from yad2_car_bot.models import (
    KeywordMatch,
    ScoreBreakdown,
    SearchCardListing,
    DetailListing,
    ScoredListing,
)

# km thresholds for low/high scoring
_LOW_KM_THRESHOLD = 80_000
_HIGH_KM_THRESHOLD = 120_000

# Terms that specifically indicate authorized service center (subset of "maintenance")
_AUTHORIZED_CENTER_TERMS = {"מרכז שירות מורשה"}

# Terms that indicate service history (other maintenance terms)
_SERVICE_HISTORY_TERMS = {"ספר טיפולים", "קבלות", "תיעוד מלא"}


def _parse_km(km_str: Optional[str]) -> Optional[int]:
    """Parse km string like '77,320' → 77320."""
    if not km_str:
        return None
    digits = re.sub(r"[^\d]", "", km_str)
    return int(digits) if digits else None


# Mapping from (category, subcategory) → scoring factor key
_KEYWORD_TO_FACTOR: dict[tuple[str, str], str] = {
    ("soft_flags", "leasing_or_company"): "leasing_or_company",
    ("soft_flags", "paint_or_bodywork"): "paint_or_bodywork",
    ("soft_flags", "value_loss"): "value_loss",
    ("soft_flags", "warning_lights"): "warning_lights",
    ("positive", "condition"): "good_condition_words",
    ("positive", "inspection"): "commits_to_inspection",
    ("positive", "test"): "long_test",
}


def _ownership_matches_any(text: str, terms: list[str]) -> bool:
    return any(term and term in text for term in terms)


def _reject_non_private_original_ownership(
    detail: DetailListing, rules: dict
) -> str | None:
    """Return a reject reason if original ownership fails the configured filter.

    Controlled by ``scoring_rules.original_ownership_filter``:
    - ``enabled`` (default false): turn the filter on
    - ``rejected_substrings``: hard-reject when any term appears in original ownership
    - ``allowed_substrings``: if set and none match a known original ownership, reject
    - ``reject_when_missing``: reject when original ownership was not parsed
    """
    cfg = rules.get("original_ownership_filter") or {}
    if not cfg.get("enabled", False):
        return None

    original = (detail.original_ownership or "").strip()
    if not original:
        if cfg.get("reject_when_missing", False):
            return "original_ownership missing"
        return None

    rejected = list(cfg.get("rejected_substrings") or [])
    if _ownership_matches_any(original, rejected):
        return f"original_ownership non-private: '{original}'"

    allowed = list(cfg.get("allowed_substrings") or [])
    if allowed and not _ownership_matches_any(original, allowed):
        return f"original_ownership not in allow-list: '{original}'"

    return None


def score_listing(
    card: SearchCardListing,
    detail: DetailListing,
    matches: list[KeywordMatch],
    rules: dict,
) -> ScoredListing:
    """Compute a score for the listing based on keyword matches and data factors.

    Returns a ScoredListing with full breakdown.
    """
    base_score: int = rules.get("base_score", 50)
    hard_reject_score: int = rules.get("hard_reject_score", 0)
    min_notify: int = rules.get("minimum_score_to_notify", 70)
    pos_rules: dict = rules.get("positive", {})
    neg_rules: dict = rules.get("negative", {})

    factors: dict[str, int] = {"base": base_score}
    positive_reasons: list[str] = []
    flags: list[str] = []

    # ── Hard reject check ────────────────────────────────────────────────────
    hard_rejects = [m for m in matches if m.category == "hard_reject"]
    ownership_reject = _reject_non_private_original_ownership(detail, rules)
    if hard_rejects or ownership_reject:
        reason_parts: list[str] = []
        if hard_rejects:
            reason_parts.append(
                ", ".join(f"{m.subcategory}: '{m.term}'" for m in hard_rejects)
            )
        if ownership_reject:
            reason_parts.append(ownership_reject)
        reason_str = "; ".join(reason_parts)
        return ScoredListing(
            score=hard_reject_score,
            score_breakdown=ScoreBreakdown(
                factors={"hard_reject": hard_reject_score - base_score}
            ),
            positive_reasons=[],
            flags=[f"HARD REJECT — {reason_str}"],
            decision="rejected",
        )

    # ── Keyword-based factors ─────────────────────────────────────────────────
    applied_factors: set[str] = set()

    for m in matches:
        key = (m.category, m.subcategory)
        factor_name = _KEYWORD_TO_FACTOR.get(key)

        if factor_name and factor_name not in applied_factors:
            if m.category == "soft_flags":
                delta = neg_rules.get(factor_name, 0)
                factors[factor_name] = delta
                if delta:
                    flags.append(f"{m.subcategory}: '{m.term}'")
                applied_factors.add(factor_name)
            elif m.category == "positive":
                delta = pos_rules.get(factor_name, 0)
                factors[factor_name] = delta
                if delta:
                    positive_reasons.append(f"{m.subcategory}: '{m.term}'")
                applied_factors.add(factor_name)

        # Maintenance sub-split: authorized_service_center vs has_service_history
        if key == ("positive", "maintenance"):
            if m.term in _AUTHORIZED_CENTER_TERMS and "authorized_service_center" not in applied_factors:
                delta = pos_rules.get("authorized_service_center", 0)
                factors["authorized_service_center"] = delta
                if delta:
                    positive_reasons.append(f"authorized_service_center: '{m.term}'")
                applied_factors.add("authorized_service_center")
            elif m.term in _SERVICE_HISTORY_TERMS and "has_service_history" not in applied_factors:
                delta = pos_rules.get("has_service_history", 0)
                factors["has_service_history"] = delta
                if delta:
                    positive_reasons.append(f"has_service_history: '{m.term}'")
                applied_factors.add("has_service_history")

    # ── Data-derived factors ──────────────────────────────────────────────────

    # private_ownership
    ownership = (detail.current_ownership or "").strip()
    if ownership and ("פרטי" in ownership or "פרטית" in ownership):
        if "private_ownership" not in applied_factors:
            delta = pos_rules.get("private_ownership", 0)
            factors["private_ownership"] = delta
            if delta:
                positive_reasons.append(f"private_ownership: '{ownership}'")
            applied_factors.add("private_ownership")

    # first_or_second_hand
    if card.hand is not None and 1 <= card.hand <= 2:
        if "first_or_second_hand" not in applied_factors:
            delta = pos_rules.get("first_or_second_hand", 0)
            factors["first_or_second_hand"] = delta
            if delta:
                positive_reasons.append(f"first_or_second_hand: יד {card.hand}")
            applied_factors.add("first_or_second_hand")

    # km scoring
    km_int = _parse_km(detail.km)
    if km_int is not None:
        if km_int < _LOW_KM_THRESHOLD and "low_km" not in applied_factors:
            delta = pos_rules.get("low_km", 0)
            factors["low_km"] = delta
            if delta:
                positive_reasons.append(f"low_km: {detail.km}")
            applied_factors.add("low_km")
        elif km_int > _HIGH_KM_THRESHOLD and "high_km" not in applied_factors:
            delta = neg_rules.get("high_km", 0)
            factors["high_km"] = delta
            if delta:
                flags.append(f"high_km: {detail.km}")
            applied_factors.add("high_km")

    # has_images / missing_images
    if card.image_url:
        if "has_images" not in applied_factors:
            delta = pos_rules.get("has_images", 0)
            factors["has_images"] = delta
            applied_factors.add("has_images")
    else:
        if "missing_images" not in applied_factors:
            delta = neg_rules.get("missing_images", 0)
            factors["missing_images"] = delta
            if delta:
                flags.append("missing_images")
            applied_factors.add("missing_images")

    # missing_price
    if not card.price:
        if "missing_price" not in applied_factors:
            delta = neg_rules.get("missing_price", 0)
            factors["missing_price"] = delta
            if delta:
                flags.append("missing_price")
            applied_factors.add("missing_price")

    # old_test_or_missing_test — only penalise if data was actually fetched from a
    # detail page; when enrichment comes from __NEXT_DATA__ the absence is expected
    if not detail.test_valid_until and detail.parser_provenance != "search_json_enrichment":
        if "old_test_or_missing_test" not in applied_factors:
            delta = neg_rules.get("old_test_or_missing_test", 0)
            factors["old_test_or_missing_test"] = delta
            if delta:
                flags.append("old_test_or_missing_test")
            applied_factors.add("old_test_or_missing_test")

    total = sum(factors.values())
    total = max(0, min(100, total))

    # When notify_all_matches is set, send every non-rejected listing regardless
    # of score (score is still computed for the Telegram message).
    if rules.get("notify_all_matches", False):
        decision = "notify"
    else:
        decision = "notify" if total >= min_notify else "skip"

    return ScoredListing(
        score=total,
        score_breakdown=ScoreBreakdown(factors=factors),
        positive_reasons=positive_reasons,
        flags=flags,
        decision=decision,
    )
