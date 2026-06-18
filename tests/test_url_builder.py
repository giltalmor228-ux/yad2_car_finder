"""Tests for url_builder.py"""
from urllib.parse import urlparse, parse_qs

from yad2_car_bot.url_builder import build_search_url


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
    url = build_search_url(app_config.search_profile)
    params = parse_qs(urlparse(url).query)
    expected = app_config.search_profile.expected_yad2_query_params
    for key, val in expected.items():
        assert key in params, f"Missing param: {key}"
        assert params[key][0] == val, f"Mismatch for {key}: {params[key][0]!r} != {val!r}"
