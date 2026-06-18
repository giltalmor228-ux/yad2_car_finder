from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone

from yad2_car_bot.models import ListingImage, SearchCardListing
from yad2_car_bot.parsers.html_utils import parse_html, safe_text

_BASE_URL = "https://www.yad2.co.il"

# Regex to extract listing ID from href  e.g. item/xsstyghm  or /item/xsstyghm
_ITEM_ID_RE = re.compile(r"(?:^|/)item/([^/?&]+)")

# Regex to extract year • hand from display text  e.g. "2016   •   יד 1"
_YEAR_HAND_RE = re.compile(r"(\d{4})\s*[•·]\s*יד\s*(\d+)")

# Regex to find __NEXT_DATA__ JSON embedded in the search page
_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>',
    re.DOTALL,
)


def _canonicalize_url(listing_type: str, listing_id: str) -> str:
    """Build the canonical detail page URL from listing type and ID."""
    return f"{_BASE_URL}/vehicles/{listing_type}/item/{listing_id}"


def parse_search_page(html: str) -> list[SearchCardListing]:
    """Parse all listing cards from a Yad2 search results page (or card fragment)."""
    soup = parse_html(html)
    cards = soup.select('a[data-nagish="private-item-link"][data-listing-type]')

    results: list[SearchCardListing] = []
    for card in cards:
        try:
            listing = _parse_card(card)
            if listing:
                results.append(listing)
        except Exception:
            pass  # skip malformed cards silently; caller can inspect raw HTML

    return results


def parse_next_data(html: str) -> dict[str, dict]:
    """Extract per-listing enrichment data from the __NEXT_DATA__ JSON embedded in the page.

    Returns a dict mapping listing token → enrichment dict with keys:
      images, engine_type, engine_cc, location, current_ownership.

    Returns {} on any parse error so the caller can fall back gracefully.
    """
    m = _NEXT_DATA_RE.search(html)
    if not m:
        return {}

    try:
        data = json.loads(m.group(1))
        queries = data["props"]["pageProps"]["dehydratedState"]["queries"]
        listings: list[dict] = queries[0]["state"]["data"].get("private", [])
    except (KeyError, IndexError, ValueError, TypeError):
        return {}

    result: dict[str, dict] = {}
    for item in listings:
        token = item.get("token")
        if not token:
            continue

        # Images
        meta = item.get("metaData") or {}
        cover: str | None = meta.get("coverImage")
        img_list: list[str] = meta.get("images") or ([cover] if cover else [])
        images = [ListingImage(url=url, index=i) for i, url in enumerate(img_list) if url]

        # Engine
        engine_type: str | None = (item.get("engineType") or {}).get("text")
        engine_vol = item.get("engineVolume")
        engine_cc: str | None = str(engine_vol) if engine_vol else None

        # Location (area-level)
        location: str | None = (
            (item.get("address") or {}).get("area", {}) or {}
        ).get("text")

        result[token] = {
            "images": images,
            "engine_type": engine_type,
            "engine_cc": engine_cc,
            "location": location,
            "current_ownership": "פרטית",  # ownerID=1 filter guarantees private ownership
        }

    return result


def _parse_card(card) -> SearchCardListing | None:
    """Extract a single SearchCardListing from a BS4 Tag."""
    href = card.get("href", "")

    # listing_id: prefer data-testid, fall back to href
    listing_id = card.get("data-testid", "")
    if not listing_id:
        m = _ITEM_ID_RE.search(href)
        if m:
            listing_id = m.group(1)
    if not listing_id:
        return None

    listing_url_relative = href
    listing_type = card.get("data-listing-type", "")
    listing_url = _canonicalize_url(listing_type, listing_id)

    # Title and subtitle from h2[data-nagish="feed-item-section-title"]
    title: str | None = None
    subtitle: str | None = None
    h2 = card.find("h2", attrs={"data-nagish": "feed-item-section-title"})
    if h2:
        spans = h2.find_all("span", recursive=False)
        if spans:
            title = safe_text(spans[0])
        if len(spans) > 1:
            subtitle = safe_text(spans[1])

    # Year and hand: look for the "2016 • יד 1" pattern in any span text
    year: int | None = None
    hand: int | None = None
    for span in card.find_all("span"):
        text = span.get_text(strip=True)
        m = _YEAR_HAND_RE.search(text)
        if m:
            year = int(m.group(1))
            hand = int(m.group(2))
            break

    # Price
    price_tag = card.find("span", attrs={"data-testid": "price"})
    price = safe_text(price_tag)

    # Image
    img_tag = card.find("img", attrs={"data-testid": "image"})
    image_url = img_tag.get("src") if img_tag else None

    # Tags / flags
    tags = [
        t.get_text(strip=True)
        for t in card.find_all("span", attrs={"data-testid": "listing-item-flag"})
        if t.get_text(strip=True)
    ]

    # Content hash
    raw_card_html_hash = hashlib.md5(str(card).encode("utf-8")).hexdigest()

    return SearchCardListing(
        listing_id=listing_id,
        listing_url_relative=listing_url_relative,
        listing_url=listing_url,
        listing_type=listing_type,
        title=title,
        subtitle=subtitle,
        year=year,
        hand=hand,
        price=price,
        image_url=image_url,
        tags=tags,
        raw_card_html_hash=raw_card_html_hash,
        parsed_at=datetime.now(tz=timezone.utc),
    )



def _canonicalize_url(listing_type: str, listing_id: str) -> str:
    """Build the canonical detail page URL from listing type and ID."""
    return f"{_BASE_URL}/vehicles/{listing_type}/item/{listing_id}"


def parse_search_page(html: str) -> list[SearchCardListing]:
    """Parse all listing cards from a Yad2 search results page (or card fragment)."""
    soup = parse_html(html)
    cards = soup.select('a[data-nagish="private-item-link"][data-listing-type]')

    results: list[SearchCardListing] = []
    for card in cards:
        try:
            listing = _parse_card(card)
            if listing:
                results.append(listing)
        except Exception:
            pass  # skip malformed cards silently; caller can inspect raw HTML

    return results


def _parse_card(card) -> SearchCardListing | None:
    """Extract a single SearchCardListing from a BS4 Tag."""
    href = card.get("href", "")

    # listing_id: prefer data-testid, fall back to href
    listing_id = card.get("data-testid", "")
    if not listing_id:
        m = _ITEM_ID_RE.search(href)
        if m:
            listing_id = m.group(1)
    if not listing_id:
        return None

    listing_url_relative = href
    listing_type = card.get("data-listing-type", "")
    listing_url = _canonicalize_url(listing_type, listing_id)

    # Title and subtitle from h2[data-nagish="feed-item-section-title"]
    title: str | None = None
    subtitle: str | None = None
    h2 = card.find("h2", attrs={"data-nagish": "feed-item-section-title"})
    if h2:
        spans = h2.find_all("span", recursive=False)
        if spans:
            title = safe_text(spans[0])
        if len(spans) > 1:
            subtitle = safe_text(spans[1])

    # Year and hand: look for the "2016 • יד 1" pattern in any span text
    year: int | None = None
    hand: int | None = None
    for span in card.find_all("span"):
        text = span.get_text(strip=True)
        m = _YEAR_HAND_RE.search(text)
        if m:
            year = int(m.group(1))
            hand = int(m.group(2))
            break

    # Price
    price_tag = card.find("span", attrs={"data-testid": "price"})
    price = safe_text(price_tag)

    # Image
    img_tag = card.find("img", attrs={"data-testid": "image"})
    image_url = img_tag.get("src") if img_tag else None

    # Tags / flags
    tags = [
        t.get_text(strip=True)
        for t in card.find_all("span", attrs={"data-testid": "listing-item-flag"})
        if t.get_text(strip=True)
    ]

    # Content hash
    raw_card_html_hash = hashlib.md5(str(card).encode("utf-8")).hexdigest()

    return SearchCardListing(
        listing_id=listing_id,
        listing_url_relative=listing_url_relative,
        listing_url=listing_url,
        listing_type=listing_type,
        title=title,
        subtitle=subtitle,
        year=year,
        hand=hand,
        price=price,
        image_url=image_url,
        tags=tags,
        raw_card_html_hash=raw_card_html_hash,
        parsed_at=datetime.now(tz=timezone.utc),
    )
