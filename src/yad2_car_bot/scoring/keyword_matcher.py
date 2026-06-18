from __future__ import annotations

from yad2_car_bot.models import KeywordMatch
from yad2_car_bot.parsers.html_utils import normalize_hebrew


def match_keywords(
    description: str | None,
    tags: list[str],
    rules: dict,
) -> list[KeywordMatch]:
    """Match all keyword categories against *description* and *tags*.

    Returns a list of KeywordMatch objects.
    Categories are checked in order: hard_reject → soft_flags → positive.
    """
    matches: list[KeywordMatch] = []

    # Build a single normalized description text and normalized tags list
    norm_desc = normalize_hebrew(description or "")
    norm_tags = [normalize_hebrew(t) for t in tags]
    combined_tag_text = " ".join(norm_tags)

    category_order = ["hard_reject", "soft_flags", "positive"]

    for category in category_order:
        subcategories = rules.get(category, {})
        for subcategory, phrases in subcategories.items():
            for phrase in phrases:
                norm_phrase = normalize_hebrew(phrase)
                if not norm_phrase:
                    continue

                # Check description
                if norm_phrase in norm_desc:
                    matches.append(
                        KeywordMatch(
                            term=phrase,
                            category=category,
                            subcategory=subcategory,
                            field_matched="description",
                        )
                    )
                    continue  # found in description, no need to check tags for same term

                # Check tags
                if norm_phrase in combined_tag_text:
                    matches.append(
                        KeywordMatch(
                            term=phrase,
                            category=category,
                            subcategory=subcategory,
                            field_matched="tags",
                        )
                    )

    return matches
