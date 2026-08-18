from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from yad2_car_bot.models import SearchGroup, SearchProfile

_BASE_URL = "https://www.yad2.co.il/vehicles/cars"

# Yad2 allows at most this many manufacturers or models in one search URL.
MAX_MANUFACTURERS_PER_GROUP = 4
MAX_MODELS_PER_GROUP = 4


def _common_params(profile: SearchProfile) -> dict[str, str]:
    """Shared range/single-value/boolean params, independent of manufacturer/model."""
    f = profile.filters
    params: dict[str, str] = {}

    params["year"] = f"{f.year.min}-{f.year.max}"
    params["price"] = f"{f.price.min}-{f.price.max}"
    params["km"] = f"{f.km.min}-{f.km.max}"
    params["engineval"] = f"{f.engine_cc.min}-{f.engine_cc.max}"
    params["hand"] = f"{f.hand.min}-{f.hand.max}"

    if f.engine_types:
        params["engineType"] = str(f.engine_types[0].id)
    params["gearBox"] = str(f.gearbox.id)
    params["ownerID"] = str(f.owner_type.id)

    if f.price_only:
        params["priceOnly"] = "1"
    if f.image_only:
        params["imgOnly"] = "1"

    return params


def build_search_url(profile: SearchProfile) -> str:
    """Build a single Yad2 search URL from *profile*.cars* (no model filter).

    Never adds ``model`` or ``yad2_source``. Prefer :func:`build_search_urls`
    when ``search_groups`` is configured.
    """
    manufacturer_ids = [
        str(entry.manufacturer_id)
        for entry in profile.cars.values()
        if entry.manufacturer_id is not None
    ]

    params: dict[str, str] = {}
    if manufacturer_ids:
        params["manufacturer"] = ",".join(manufacturer_ids)
    params.update(_common_params(profile))

    return f"{_BASE_URL}?{urlencode(params)}"


def _build_group_url(profile: SearchProfile, group: SearchGroup) -> str:
    params: dict[str, str] = {}
    params["manufacturer"] = ",".join(str(mfr_id) for mfr_id in group.manufacturers)
    if group.models:
        params["model"] = ",".join(str(model_id) for model_id in group.models)
    params.update(_common_params(profile))
    return f"{_BASE_URL}?{urlencode(params)}"


def build_search_urls(
    profile: SearchProfile, model_catalog: list[dict] | None = None
) -> list[str]:
    """Build one Yad2 search URL per ``search_groups`` entry.

    Each group may include up to :data:`MAX_MANUFACTURERS_PER_GROUP` manufacturer
    IDs and up to :data:`MAX_MODELS_PER_GROUP` model IDs (total for that group).

    If ``search_groups`` is empty, returns a single URL from :func:`build_search_url`.

    *model_catalog* is accepted for call-site compatibility; manufacturer IDs
    come from each group explicitly.
    """
    del model_catalog  # manufacturers are listed explicitly on each group
    if not profile.search_groups:
        return [build_search_url(profile)]

    return [_build_group_url(profile, group) for group in profile.search_groups]


def with_page(url: str, page: int) -> str:
    """Return *url* with ``page`` query param set (omit for page 1)."""
    if page < 1:
        raise ValueError("page must be >= 1")
    parts = urlparse(url)
    params = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != "page"]
    if page > 1:
        params.append(("page", str(page)))
    return urlunparse(parts._replace(query=urlencode(params)))
