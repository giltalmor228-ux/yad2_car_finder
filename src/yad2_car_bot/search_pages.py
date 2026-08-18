from __future__ import annotations

import time
from typing import Callable

from yad2_car_bot.parsers.search_parser import (
    parse_feed_pagination,
    parse_next_data,
    parse_search_page,
)
from yad2_car_bot.url_builder import with_page

# Hard ceiling so a broken pager cannot loop forever.
_MAX_SEARCH_PAGES = 30
_PAGE_PAUSE_SECONDS = 2


def fetch_all_search_pages(
    client,
    search_url: str,
    *,
    log: Callable[[str], None] | None = None,
    page_pause_seconds: float = _PAGE_PAUSE_SECONDS,
    max_pages: int = _MAX_SEARCH_PAGES,
) -> tuple[list, dict[str, dict], str | None]:
    """Fetch search results page-by-page until pagination ends or a fetch fails.

    Page 1 uses *search_url* as-is. Later pages append ``page=N``. Stops when:
    - client fetch raises (after page 1)
    - a page yields no listing cards
    - a page yields no *new* listing IDs
    - we reach ``pagination.pages`` from page-1 JSON (when present)
    - we hit *max_pages*

    Returns ``(cards, enrichment_map, page1_html_or_none)``.
    """
    _log = log or (lambda _msg: None)

    all_cards: list = []
    enrichment: dict[str, dict] = {}
    seen_ids: set[str] = set()
    known_pages: int | None = None
    page1_html: str | None = None

    for page_num in range(1, max_pages + 1):
        page_url = with_page(search_url, page_num)
        if page_num > 1:
            _log(f"  page {page_num}: {page_url}")
            if page_pause_seconds > 0:
                time.sleep(page_pause_seconds)

        try:
            html = client.get_page(page_url, require_listings=False)
        except RuntimeError as exc:
            if page_num == 1:
                raise
            _log(f"  page {page_num}: fetch failed ({exc}); stopping pagination.")
            break

        if page_num == 1:
            page1_html = html
            pagination = parse_feed_pagination(html)
            if pagination:
                known_pages = pagination["pages"]
                _log(
                    f"  pagination: {known_pages} page(s), "
                    f"total≈{pagination.get('total')}"
                )

        cards = parse_search_page(html)
        page_enrichment = parse_next_data(html)
        new_cards = [c for c in cards if c.listing_id not in seen_ids]

        _log(
            f"  page {page_num}: {len(cards)} card(s), "
            f"{len(new_cards)} new unique"
        )

        if not cards:
            _log(f"  page {page_num}: empty; stopping pagination.")
            break
        if not new_cards:
            _log(f"  page {page_num}: no new listings; stopping pagination.")
            break

        for card in new_cards:
            seen_ids.add(card.listing_id)
            all_cards.append(card)
        enrichment.update(page_enrichment)

        if known_pages is not None and page_num >= known_pages:
            _log(f"  reached last page ({known_pages}); done.")
            break

    return all_cards, enrichment, page1_html
