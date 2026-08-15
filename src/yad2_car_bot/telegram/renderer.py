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
            body_lines = lines[i + 1 :]
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


def _gearbox_from_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    if "אוט" in text:
        return "אוטומט"
    if "ידנ" in text:
        return "ידני"
    return None


def _display(value: Optional[str], fallback: str = "—") -> str:
    text = (value or "").strip()
    return text if text else fallback


def _format_engine(engine_type: Optional[str], engine_cc: Optional[str]) -> str:
    parts = [p for p in (_display(engine_type, ""), _display(engine_cc, "")) if p]
    return ", ".join(parts) if parts else "—"


def _format_ownership_lines(
    hand: Optional[int],
    current: Optional[str],
    original: Optional[str],
) -> tuple[str, str]:
    """Return (current_ownership display, original_ownership display).

    Yad2 exposes current owner + original owner only (not every intermediate hand).
    For first-hand cars, original is omitted in the message via "— / לא רלוונטי".
    """
    current_disp = _display(current)
    if hand is None:
        return current_disp, _display(original)
    if hand <= 1:
        # First hand: original is the same idea as current.
        return current_disp, "יד ראשונה"
    return current_disp, _display(original)


def render_message(
    scored: ScoredListing,
    card: SearchCardListing,
    detail: DetailListing,
    template_raw: str,
) -> TelegramPayload:
    """Render a Telegram payload from the template and listing data."""
    template = _extract_template(template_raw)

    image_count = len(detail.images) + (1 if card.image_url and not detail.images else 0)

    gearbox = detail.gearbox or _gearbox_from_text(card.subtitle)
    engine = _format_engine(detail.engine_type, detail.engine_cc)
    current_own, original_own = _format_ownership_lines(
        card.hand, detail.current_ownership, detail.original_ownership
    )

    def build_text(positive_list, flags_list, include_subtitle=True) -> str:
        subtitle = card.subtitle if include_subtitle else ""
        pos = "\n".join(f"• {r}" for r in positive_list) or "—"
        fls = "\n".join(f"• {f}" for f in flags_list) or "—"
        return template.format(
            title=card.title or "—",
            subtitle=subtitle or "",
            price=card.price or "לא צוין",
            year=str(card.year) if card.year else "—",
            km=_display(detail.km),
            hand=str(card.hand) if card.hand is not None else "—",
            gearbox=_display(gearbox),
            engine_type=detail.engine_type or "—",
            engine_cc=detail.engine_cc or "—",
            engine=engine,
            location=_display(detail.location),
            current_ownership=current_own,
            original_ownership=original_own,
            test_valid_until=_display(detail.test_valid_until),
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
