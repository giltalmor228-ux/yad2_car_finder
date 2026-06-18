from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from yad2_car_bot.models import DetailListing, ListingImage
from yad2_car_bot.parsers.html_utils import parse_html, safe_text

# Hebrew label → English field name mapping
_LABEL_MAP: dict[str, str] = {
    "קילומטראז׳": "km",
    "קילומטרז": "km",      # alternate without geresh
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
        # Pair consecutive dd (label) with dt (value)
        i = 0
        while i < len(children):
            tag = children[i]
            testid = tag.get("data-testid", "")
            if testid.endswith("-label"):
                label_text = tag.get_text(strip=True)
                # Look for the next sibling that is a value
                value_text: Optional[str] = None
                if i + 1 < len(children):
                    next_tag = children[i + 1]
                    next_testid = next_tag.get("data-testid", "")
                    if next_testid.endswith("-value"):
                        value_text = next_tag.get_text(strip=True) or None
                        i += 1  # skip the value in next iteration

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

    # Phone: only detect presence, never store the number
    phone_link_div = soup.find("div", attrs={"data-testid": "phone-number-link"})
    phone_available = False
    if phone_link_div:
        tel_anchor = phone_link_div.find("a", href=lambda h: h and h.startswith("tel:"))
        phone_available = tel_anchor is not None

    # Detail image
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
