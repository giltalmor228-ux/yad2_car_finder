"""Tests for url_builder.py"""
from copy import deepcopy
from urllib.parse import urlparse, parse_qs

from yad2_car_bot.models import SearchGroup
from yad2_car_bot.url_builder import (
    MAX_MANUFACTURERS_PER_GROUP,
    MAX_MODELS_PER_GROUP,
    build_search_url,
    build_search_urls,
)


def test_build_url_returns_valid_url(app_config):
    url = build_search_url(app_config.search_profile)
    parsed = urlparse(url)
    assert parsed.scheme == "https"
    assert "yad2.co.il" in parsed.netloc
    assert parsed.path == "/vehicles/cars"


def test_manufacturer_ids_present(app_config):
    url = build_search_url(app_config.search_profile)
    params = parse_qs(urlparse(url).query)
    assert "manufacturer" in params
    ids = set(params["manufacturer"][0].split(","))
    # Profile has Toyota=19, Suzuki=36, Hyundai=21, Mazda=27
    assert "19" in ids
    assert "36" in ids
    assert "21" in ids
    assert "27" in ids


def test_year_range_format(app_config):
    url = build_search_url(app_config.search_profile)
    params = parse_qs(urlparse(url).query)
    assert params["year"][0] == "2016-2026"


def test_price_range_format(app_config):
    url = build_search_url(app_config.search_profile)
    params = parse_qs(urlparse(url).query)
    assert params["price"][0] == "28000-55000"


def test_no_model_param(app_config):
    url = build_search_url(app_config.search_profile)
    params = parse_qs(urlparse(url).query)
    assert "model" not in params


def test_no_yad2_source_param(app_config):
    url = build_search_url(app_config.search_profile)
    params = parse_qs(urlparse(url).query)
    assert "yad2_source" not in params


def test_boolean_flags_present(app_config):
    url = build_search_url(app_config.search_profile)
    params = parse_qs(urlparse(url).query)
    assert params["priceOnly"][0] == "1"
    assert params["imgOnly"][0] == "1"


def test_gearbox_and_owner_type(app_config):
    url = build_search_url(app_config.search_profile)
    params = parse_qs(urlparse(url).query)
    assert params["gearBox"][0] == "102"
    assert params["ownerID"][0] == "1"


def test_url_matches_expected_params(app_config):
    # expected_yad2_query_params describes the fallback cars-only URL
    profile = deepcopy(app_config.search_profile)
    profile.search_groups = []
    url = build_search_url(profile)
    params = parse_qs(urlparse(url).query)
    expected = profile.expected_yad2_query_params
    for key, val in expected.items():
        assert key in params, f"Missing param: {key}"
        assert params[key][0] == val, f"Mismatch for {key}: {params[key][0]!r} != {val!r}"


def test_empty_search_groups_returns_single_url_without_model(app_config):
    profile = deepcopy(app_config.search_profile)
    profile.search_groups = []
    urls = build_search_urls(profile, app_config.model_catalog)
    assert len(urls) == 1
    params = parse_qs(urlparse(urls[0]).query)
    assert "model" not in params
    assert urls[0] == build_search_url(profile)


def test_two_search_groups_produce_two_urls(app_config):
    profile = deepcopy(app_config.search_profile)
    profile.search_groups = [
        SearchGroup(manufacturers=[19, 21, 27, 36], models=[10247, 10226, 10238, 10225]),
        SearchGroup(manufacturers=[19, 21], models=[11228, 11150]),
    ]

    urls = build_search_urls(profile, app_config.model_catalog)
    assert len(urls) == 2

    for url in urls:
        params = parse_qs(urlparse(url).query)
        mfr_ids = params["manufacturer"][0].split(",")
        model_ids = params["model"][0].split(",")
        assert len(mfr_ids) <= MAX_MANUFACTURERS_PER_GROUP
        assert len(model_ids) <= MAX_MODELS_PER_GROUP
        assert "yad2_source" not in params

    assert parse_qs(urlparse(urls[0]).query)["manufacturer"][0] == "19,21,27,36"
    assert parse_qs(urlparse(urls[0]).query)["model"][0] == "10247,10226,10238,10225"
    assert parse_qs(urlparse(urls[1]).query)["manufacturer"][0] == "19,21"
    assert parse_qs(urlparse(urls[1]).query)["model"][0] == "11228,11150"
