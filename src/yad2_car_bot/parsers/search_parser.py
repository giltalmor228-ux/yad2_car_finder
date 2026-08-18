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

_FEED_BUCKETS = ("private", "commercial", "platinum", "solo", "boost")


def _canonicalize_url(listing_type: str, listing_id: str) -> str:
    """Build the canonical detail page URL from listing type and ID.

    Yad2 serves detail pages at ``/vehicles/item/{id}``. Types like
    ``private-vehicle-no-footer`` are feed-only and produce broken links.
    """
    return f"{_BASE_URL}/vehicles/item/{listing_id}"


def _load_next_data_payload(html: str) -> dict | list | None:
    """Return the search-feed payload from ``__NEXT_DATA__``, or None."""
    m = _NEXT_DATA_RE.search(html)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
        queries = data["props"]["pageProps"]["dehydratedState"]["queries"]
        return queries[0]["state"]["data"]
    except (KeyError, IndexError, ValueError, TypeError):
        return None


def parse_feed_pagination(html: str) -> dict | None:
    """Return ``{pages, perPage, total}`` from feed ``__NEXT_DATA__``, if present."""
    payload = _load_next_data_payload(html)
    if not isinstance(payload, dict):
        return None
    pagination = payload.get("pagination")
    if not isinstance(pagination, dict):
        return None
    pages = pagination.get("pages")
    try:
        pages_int = int(pages) if pages is not None else None
    except (TypeError, ValueError):
        pages_int = None
    if not pages_int or pages_int < 1:
        return None
    return {
        "pages": pages_int,
        "perPage": pagination.get("perPage"),
        "total": pagination.get("total"),
    }


def _iter_feed_items(payload: dict | list) -> list[tuple[str, dict]]:
    """Yield ``(bucket_name, item)`` for every listing in the feed payload."""
    items: list[tuple[str, dict]] = []
    if isinstance(payload, dict):
        for key in _FEED_BUCKETS:
            bucket = payload.get(key) or []
            if isinstance(bucket, list):
                for item in bucket:
                    if isinstance(item, dict):
                        items.append((key, item))
    elif isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                items.append(("list", item))
    return items


def _format_price(price) -> str | None:
    if price is None or price == "":
        return None
    if isinstance(price, str):
        return price
    try:
        value = int(price)
    except (TypeError, ValueError):
        return str(price)
    return f"{value:,} ₪"


def _listing_type_from_item(item: dict, bucket: str) -> str:
    ad_type = (item.get("adType") or "").strip().lower()
    if ad_type == "private":
        return "private-vehicle"
    if bucket in {"platinum", "solo"}:
        return f"vehicle-agency-{bucket}"
    if ad_type == "commercial" or bucket == "commercial":
        return "vehicle-agency"
    return ad_type or bucket or "unknown"


def _card_from_feed_item(item: dict, bucket: str) -> SearchCardListing | None:
    token = item.get("token")
    if not token:
        return None

    manufacturer = ((item.get("manufacturer") or {}).get("text") or "").strip()
    model = ((item.get("model") or {}).get("text") or "").strip()
    title = f"{manufacturer} {model}".strip() or None
    subtitle = ((item.get("subModel") or {}).get("text") or "") or None

    year = (item.get("vehicleDates") or {}).get("yearOfProduction")
    try:
        year_int = int(year) if year is not None else None
    except (TypeError, ValueError):
        year_int = None

    hand_raw = (item.get("hand") or {}).get("id")
    try:
        hand = int(hand_raw) if hand_raw is not None else None
    except (TypeError, ValueError):
        hand = None

    meta = item.get("metaData") or {}
    image_url = meta.get("coverImage")
    if not image_url:
        images = meta.get("images") or []
        image_url = images[0] if images else None

    tags = [
        t.get("name")
        for t in (item.get("tags") or [])
        if isinstance(t, dict) and t.get("name")
    ]

    listing_type = _listing_type_from_item(item, bucket)
    listing_url = _canonicalize_url(listing_type, token)
    fingerprint = json.dumps(
        {"token": token, "bucket": bucket, "price": item.get("price")},
        sort_keys=True,
        ensure_ascii=False,
    )
    raw_hash = hashlib.md5(fingerprint.encode("utf-8")).hexdigest()

    return SearchCardListing(
        listing_id=token,
        listing_url_relative=f"/vehicles/item/{token}",
        listing_url=listing_url,
        listing_type=listing_type,
        title=title,
        subtitle=subtitle,
        year=year_int,
        hand=hand,
        price=_format_price(item.get("price")),
        image_url=image_url,
        tags=tags,
        raw_card_html_hash=raw_hash,
        parsed_at=datetime.now(tz=timezone.utc),
        source_flags=[f"feed:{bucket}", f"adType:{(item.get('adType') or 'unknown')}"],
        parser_provenance="search_parser.parse_search_feed",
    )


def parse_search_feed_cards(html: str) -> list[SearchCardListing]:
    """Build listing cards from all ``__NEXT_DATA__`` feed buckets.

    Yad2 splits the visible feed into private / commercial / platinum / solo.
    DOM parsing only sees private ``private-item-link`` cards; this function
    returns the full page inventory (deduped by token).
    """
    payload = _load_next_data_payload(html)
    if payload is None:
        return []

    results: list[SearchCardListing] = []
    seen: set[str] = set()
    for bucket, item in _iter_feed_items(payload):
        token = item.get("token")
        if not token or token in seen:
            continue
        card = _card_from_feed_item(item, bucket)
        if not card:
            continue
        seen.add(token)
        results.append(card)
    return results


def parse_search_page_dom(html: str) -> list[SearchCardListing]:
    """Parse listing cards from DOM anchors only (private-item-link)."""
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


def parse_search_page(html: str) -> list[SearchCardListing]:
    """Parse all listing cards from a Yad2 search results page.

    Prefers ``__NEXT_DATA__`` feed buckets (private + commercial + platinum +
    solo) so agency/platinum cards the user sees are not dropped. Falls back
    to DOM private-card parsing when feed JSON is missing.
    """
    feed_cards = parse_search_feed_cards(html)
    if feed_cards:
        return feed_cards
    return parse_search_page_dom(html)


def _gearbox_from_text(text: str | None) -> str | None:
    """Infer gearbox label from Yad2 sub-model / subtitle text."""
    if not text:
        return None
    if "אוט" in text:  # אוט׳ / אוטומט / אוטומטי
        return "אוטומט"
    if "ידנ" in text:  # ידני
        return "ידני"
    return None


def parse_next_data(html: str) -> dict[str, dict]:
    """Extract per-listing enrichment data from the __NEXT_DATA__ JSON embedded in the page.

    Returns a dict mapping listing token → enrichment dict with keys:
      images, engine_type, engine_cc, location, current_ownership, gearbox.

    Returns {} on any parse error so the caller can fall back gracefully.
    """
    payload = _load_next_data_payload(html)
    if payload is None:
        return {}

    result: dict[str, dict] = {}
    for bucket, item in _iter_feed_items(payload):
        token = item.get("token")
        if not token:
            continue

        meta = item.get("metaData") or {}
        cover: str | None = meta.get("coverImage")
        img_list: list[str] = meta.get("images") or ([cover] if cover else [])
        images = [ListingImage(url=url, index=i) for i, url in enumerate(img_list) if url]

        engine_type: str | None = (item.get("engineType") or {}).get("text")
        engine_vol = item.get("engineVolume")
        engine_cc: str | None = str(engine_vol) if engine_vol else None

        location: str | None = (
            (item.get("address") or {}).get("area", {}) or {}
        ).get("text")

        sub_model_text = ((item.get("subModel") or {}).get("text") or "") or None
        gearbox = _gearbox_from_text(sub_model_text)

        ad_type = (item.get("adType") or "").strip().lower()
        customer = item.get("customer") or {}
        if customer.get("agencyName"):
            ownership = f"סוכנות ({customer['agencyName']})"
        elif ad_type == "private" or bucket == "private":
            ownership = "פרטית"
        else:
            ownership = None

        result[token] = {
            "images": images,
            "engine_type": engine_type,
            "engine_cc": engine_cc,
            "location": location,
            "current_ownership": ownership,
            "gearbox": gearbox,
            "subtitle": sub_model_text,
            "feed_bucket": bucket,
            "ad_type": ad_type or None,
        }

    return result


def _parse_card(card) -> SearchCardListing | None:
    """Extract a single SearchCardListing from a BS4 Tag."""
    href = card.get("href", "")

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

    title: str | None = None
    subtitle: str | None = None
    h2 = card.find("h2", attrs={"data-nagish": "feed-item-section-title"})
    if h2:
        spans = h2.find_all("span", recursive=False)
        if spans:
            title = safe_text(spans[0])
        if len(spans) > 1:
            subtitle = safe_text(spans[1])

    year: int | None = None
    hand: int | None = None
    for span in card.find_all("span"):
        text = span.get_text(strip=True)
        m = _YEAR_HAND_RE.search(text)
        if m:
            year = int(m.group(1))
            hand = int(m.group(2))
            break

    price_tag = card.find("span", attrs={"data-testid": "price"})
    price = safe_text(price_tag)

    img_tag = card.find("img", attrs={"data-testid": "image"})
    image_url = img_tag.get("src") if img_tag else None

    tags = [
        t.get_text(strip=True)
        for t in card.find_all("span", attrs={"data-testid": "listing-item-flag"})
        if t.get_text(strip=True)
    ]

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
