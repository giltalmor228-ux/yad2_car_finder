from __future__ import annotations

from urllib.parse import urlencode

from yad2_car_bot.models import SearchProfile

_BASE_URL = "https://www.yad2.co.il/vehicles/cars"


def build_search_url(profile: SearchProfile) -> str:
    """Build a Yad2 search URL from *profile*.

    The URL is built from the structured ``filters`` and ``cars`` sections.
    Never adds ``model`` or ``yad2_source`` parameters.
    """
    f = profile.filters

    # Comma-separated manufacturer IDs in the same order as profile.cars
    manufacturer_ids = [
        str(entry.manufacturer_id)
        for entry in profile.cars.values()
        if entry.manufacturer_id is not None
    ]

    params: dict[str, str] = {}

    # Manufacturer
    if manufacturer_ids:
        params["manufacturer"] = ",".join(manufacturer_ids)

    # Ranges
    params["year"] = f"{f.year.min}-{f.year.max}"
    params["price"] = f"{f.price.min}-{f.price.max}"
    params["km"] = f"{f.km.min}-{f.km.max}"
    params["engineval"] = f"{f.engine_cc.min}-{f.engine_cc.max}"
    params["hand"] = f"{f.hand.min}-{f.hand.max}"

    # Single-value filters
    if f.engine_types:
        params["engineType"] = str(f.engine_types[0].id)
    params["gearBox"] = str(f.gearbox.id)
    params["ownerID"] = str(f.owner_type.id)

    # Boolean flags
    if f.price_only:
        params["priceOnly"] = "1"
    if f.image_only:
        params["imgOnly"] = "1"

    return f"{_BASE_URL}?{urlencode(params)}"
