from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Optional

from yad2_car_bot.models import DetailListing, ListingImage
from yad2_car_bot.parsers.html_utils import parse_html, safe_text

# Hebrew label → English field name mapping
_LABEL_MAP: dict[str, str] = {
    "קילומטראז׳": "km",
    "קילומטרז": "km",  # alternate without geresh
    "צבע": "color",
    "בעלות נוכחית": "current_ownership",
    "טסט עד": "test_valid_until",
    "תיבת הילוכים": "gearbox",
    "תאריך עליה לכביש": "date_on_road",
    "סוג מנוע": "engine_type",
    "מרכב": "body_type",
    "מושבים": "seats",
    "כוח סוס": "horse_power",
    "נפח מנוע": "engine_cc",
    "צריכת דלק משולבת": "combined_fuel_consumption",
}

_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>',
    re.DOTALL,
)


def parse_technical_section(html: str) -> dict[str, Optional[str]]:
    """Parse label/value pairs from the technical info section.

    Returns a dict mapping English field names to their string values.
    """
    soup = parse_html(html)
    section = soup.find("section", attrs={"data-testid": "additional-info"})
    if not section:
        return {}

    result: dict[str, Optional[str]] = {}

    for dl in section.find_all("dl"):
        children = dl.find_all(["dd", "dt"], recursive=False)
        i = 0
        while i < len(children):
            tag = children[i]
            testid = tag.get("data-testid", "")
            if testid.endswith("-label"):
                label_text = tag.get_text(strip=True)
                value_text: Optional[str] = None
                if i + 1 < len(children):
                    next_tag = children[i + 1]
                    next_testid = next_tag.get("data-testid", "")
                    if next_testid.endswith("-value"):
                        value_text = next_tag.get_text(strip=True) or None
                        i += 1

                field = _LABEL_MAP.get(label_text)
                if field:
                    result[field] = value_text
            i += 1

    return result


def parse_description_location(html: str) -> dict:
    """Parse location, description, phone availability, and image from a listing page."""
    soup = parse_html(html)

    location = safe_text(soup.find("span", attrs={"data-testid": "location"}))
    description = safe_text(soup.find("p", attrs={"data-testid": "vehicle-description"}))

    phone_link_div = soup.find("div", attrs={"data-testid": "phone-number-link"})
    phone_available = False
    if phone_link_div:
        tel_anchor = phone_link_div.find("a", href=lambda h: h and h.startswith("tel:"))
        phone_available = tel_anchor is not None

    image_box = soup.find("div", attrs={"data-testid": "image-box"})
    image_url: Optional[str] = None
    if image_box:
        img = image_box.find("img", attrs={"data-testid": "image"})
        if img:
            image_url = img.get("src") or img.get("data-src")

    return {
        "location": location,
        "description": description,
        "phone_available": phone_available,
        "image_url": image_url,
    }


def _format_km(value) -> Optional[str]:
    if value is None or value == "":
        return None
    try:
        n = int(value)
        return f"{n:,}"
    except (TypeError, ValueError):
        text = str(value).strip()
        return text or None


def _format_test_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(value))
    if m:
        return f"{m.group(3)}/{m.group(2)}/{m.group(1)}"
    return str(value)


def parse_detail_next_data(html: str) -> dict:
    """Extract listing fields from detail-page ``__NEXT_DATA__`` (includes km)."""
    m = _NEXT_DATA_RE.search(html)
    if not m:
        return {}
    try:
        data = json.loads(m.group(1))
        item = data["props"]["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]
        if not isinstance(item, dict):
            return {}
    except (KeyError, IndexError, ValueError, TypeError):
        return {}

    address = item.get("address") or {}
    area = (address.get("area") or {}).get("text")
    city = (address.get("city") or {}).get("text")
    location = area or city

    vehicle_dates = item.get("vehicleDates") or {}
    meta = item.get("metaData") or {}
    cover = meta.get("coverImage")
    img_list: list[str] = meta.get("images") or ([cover] if cover else [])
    images = [ListingImage(url=url, index=i) for i, url in enumerate(img_list) if url]

    engine_vol = item.get("engineVolume")
    color = item.get("color")
    color_text = color.get("text") if isinstance(color, dict) else color

    return {
        "km": _format_km(item.get("km")),
        "color": color_text,
        "current_ownership": (item.get("owner") or {}).get("text"),
        "original_ownership": (item.get("originalOwner") or {}).get("text"),
        "test_valid_until": _format_test_date(vehicle_dates.get("testDate")),
        "gearbox": (item.get("gearBox") or {}).get("text"),
        "engine_type": (item.get("engineType") or {}).get("text"),
        "engine_cc": str(engine_vol) if engine_vol is not None else None,
        "location": location,
        "description": meta.get("description") or item.get("description"),
        "images": images,
        "token": item.get("token"),
    }


def merge_detail(
    technical: dict,
    description: dict,
    *,
    extra_images: Optional[list[str]] = None,
) -> DetailListing:
    """Merge outputs of parse_technical_section and parse_description_location."""
    images: list[ListingImage] = []
    if description.get("image_url"):
        images.append(ListingImage(url=description["image_url"], index=0))
    for idx, url in enumerate(extra_images or [], start=1):
        images.append(ListingImage(url=url, index=idx))

    return DetailListing(
        km=technical.get("km"),
        color=technical.get("color"),
        current_ownership=technical.get("current_ownership"),
        test_valid_until=technical.get("test_valid_until"),
        gearbox=technical.get("gearbox"),
        date_on_road=technical.get("date_on_road"),
        engine_type=technical.get("engine_type"),
        body_type=technical.get("body_type"),
        seats=technical.get("seats"),
        horse_power=technical.get("horse_power"),
        engine_cc=technical.get("engine_cc"),
        combined_fuel_consumption=technical.get("combined_fuel_consumption"),
        location=description.get("location"),
        description=description.get("description"),
        phone_available=description.get("phone_available", False),
        images=images,
        parsed_at=datetime.now(tz=timezone.utc),
    )


def enrich_detail_from_html(html: str, base: Optional[DetailListing] = None) -> DetailListing:
    """Build / merge a DetailListing from a detail-page HTML snapshot.

    Prefers ``__NEXT_DATA__`` (has km / test / ownership), then falls back to
    the technical + description DOM parsers.
    """
    next_data = parse_detail_next_data(html)
    technical = parse_technical_section(html)
    description = parse_description_location(html)

    def pick(*values):
        for value in values:
            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue
            if isinstance(value, list) and not value:
                continue
            return value
        return None

    images = pick(next_data.get("images"), base.images if base else None) or []
    if not images and description.get("image_url"):
        images = [ListingImage(url=description["image_url"], index=0)]

    return DetailListing(
        km=pick(next_data.get("km"), technical.get("km"), base.km if base else None),
        color=pick(next_data.get("color"), technical.get("color"), base.color if base else None),
        current_ownership=pick(
            next_data.get("current_ownership"),
            technical.get("current_ownership"),
            base.current_ownership if base else None,
        ),
        original_ownership=pick(
            next_data.get("original_ownership"),
            base.original_ownership if base else None,
        ),
        test_valid_until=pick(
            next_data.get("test_valid_until"),
            technical.get("test_valid_until"),
            base.test_valid_until if base else None,
        ),
        gearbox=pick(
            next_data.get("gearbox"),
            technical.get("gearbox"),
            base.gearbox if base else None,
        ),
        date_on_road=pick(technical.get("date_on_road"), base.date_on_road if base else None),
        engine_type=pick(
            next_data.get("engine_type"),
            technical.get("engine_type"),
            base.engine_type if base else None,
        ),
        body_type=pick(technical.get("body_type"), base.body_type if base else None),
        seats=pick(technical.get("seats"), base.seats if base else None),
        horse_power=pick(technical.get("horse_power"), base.horse_power if base else None),
        engine_cc=pick(
            next_data.get("engine_cc"),
            technical.get("engine_cc"),
            base.engine_cc if base else None,
        ),
        combined_fuel_consumption=pick(
            technical.get("combined_fuel_consumption"),
            base.combined_fuel_consumption if base else None,
        ),
        location=pick(
            next_data.get("location"),
            description.get("location"),
            base.location if base else None,
        ),
        description=pick(
            description.get("description"),
            next_data.get("description"),
            base.description if base else None,
        ),
        phone_available=bool(
            description.get("phone_available")
            or (base.phone_available if base else False)
        ),
        images=list(images),
        parsed_at=datetime.now(tz=timezone.utc),
        parser_provenance="detail_next_data+dom",
    )
