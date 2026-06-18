from __future__ import annotations

import re
from typing import Optional

from yad2_car_bot.models import (
    DetailListing,
    SearchCardListing,
    ScoredListing,
    TelegramPayload,
)

_TELEGRAM_CAPTION_LIMIT = 1024
_TELEGRAM_MESSAGE_LIMIT = 4096

# Extracts the template body (everything after the YAML-style header lines)
_TEMPLATE_BODY_RE = re.compile(
    r"^(?:#[^\n]*\n|##[^\n]*\n|\n)*(.+)",
    re.DOTALL,
)


def _extract_template(raw: str) -> str:
    """Return only the message template block from the raw template markdown.

    Looks for the ``## Message caption / text template`` section header and
    returns everything after it, stripping leading blank lines.
    Falls back to the first non-heading, non-blank line if the marker is absent.
    """
    lines = raw.splitlines()

    # Look for the section marker
    marker = "## message caption"
    for i, line in enumerate(lines):
        if line.strip().lower().startswith(marker):
            body_lines = lines[i + 1:]
            # Strip leading blank lines
            while body_lines and not body_lines[0].strip():
                body_lines.pop(0)
            return "\n".join(body_lines).strip()

    # Fallback: first non-heading, non-blank line onwards
    body_lines = []
    in_body = False
    for line in lines:
        if not in_body:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                in_body = True
        if in_body:
            body_lines.append(line)
    return "\n".join(body_lines).strip()


def render_message(
    scored: ScoredListing,
    card: SearchCardListing,
    detail: DetailListing,
    template_raw: str,
) -> TelegramPayload:
    """Render a Telegram payload from the template and listing data."""
    template = _extract_template(template_raw)

    positive_str = "\n".join(f"• {r}" for r in scored.positive_reasons) or "—"
    flags_str = "\n".join(f"• {f}" for f in scored.flags) or "—"
    image_count = len(detail.images) + (1 if card.image_url and not detail.images else 0)

    def build_text(positive_list, flags_list, include_subtitle=True) -> str:
        subtitle = card.subtitle if include_subtitle else ""
        pos = "\n".join(f"• {r}" for r in positive_list) or "—"
        fls = "\n".join(f"• {f}" for f in flags_list) or "—"
        return template.format(
            title=card.title or "—",
            subtitle=subtitle or "",
            price=card.price or "לא צוין",
            year=str(card.year) if card.year else "—",
            km=detail.km or "—",
            hand=str(card.hand) if card.hand is not None else "—",
            gearbox=detail.gearbox or "—",
            engine_type=detail.engine_type or "—",
            engine_cc=detail.engine_cc or "—",
            location=detail.location or "—",
            current_ownership=detail.current_ownership or "—",
            test_valid_until=detail.test_valid_until or "—",
            score=scored.score,
            positive_reasons=pos,
            flags=fls,
            image_count=image_count,
            url=card.listing_url,
        )

    # Try full text; if over caption limit, progressively trim
    positive_list = list(scored.positive_reasons)
    flags_list = list(scored.flags)

    text = build_text(positive_list, flags_list, include_subtitle=True)

    # Step 1: trim flags
    while len(text) > _TELEGRAM_CAPTION_LIMIT and flags_list:
        flags_list.pop()
        text = build_text(positive_list, flags_list, include_subtitle=True)

    # Step 2: trim positives
    while len(text) > _TELEGRAM_CAPTION_LIMIT and positive_list:
        positive_list.pop()
        text = build_text(positive_list, flags_list, include_subtitle=True)

    # Step 3: drop subtitle
    if len(text) > _TELEGRAM_CAPTION_LIMIT:
        text = build_text(positive_list, flags_list, include_subtitle=False)

    # Determine image URLs
    image_url: Optional[str] = card.image_url
    extra_urls: list[str] = []
    if detail.images:
        image_url = detail.images[0].url
        extra_urls = [img.url for img in detail.images[1:]]
    elif card.image_url:
        image_url = card.image_url

    # If still over caption limit, payload carries the full text separately
    # (notifier will handle photo + separate message)
    return TelegramPayload(
        text=text,
        image_url=image_url,
        extra_image_urls=extra_urls,
    )
