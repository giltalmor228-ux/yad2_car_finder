"""Tests for parsers/detail_parser.py — uses real HTML fixtures."""
import pytest

from yad2_car_bot.parsers.detail_parser import (
    parse_technical_section,
    parse_description_location,
    merge_detail,
)


def test_km_extracted(technical_html):
    result = parse_technical_section(technical_html)
    assert "km" in result
    assert result["km"] is not None
    assert "77" in result["km"] or "320" in result["km"]


def test_color_extracted(technical_html):
    result = parse_technical_section(technical_html)
    assert result.get("color") == "לבן"


def test_current_ownership_extracted(technical_html):
    result = parse_technical_section(technical_html)
    assert result.get("current_ownership") is not None
    assert "פרטי" in result["current_ownership"]


def test_test_valid_until_extracted(technical_html):
    result = parse_technical_section(technical_html)
    assert result.get("test_valid_until") is not None
    assert "2027" in result["test_valid_until"]


def test_gearbox_extracted(technical_html):
    result = parse_technical_section(technical_html)
    assert result.get("gearbox") is not None
    assert "אוטומ" in result["gearbox"]


def test_date_on_road_extracted(technical_html):
    result = parse_technical_section(technical_html)
    assert result.get("date_on_road") is not None
    assert "2016" in result["date_on_road"]


def test_engine_type_extracted(technical_html):
    result = parse_technical_section(technical_html)
    assert result.get("engine_type") == "בנזין"


def test_body_type_extracted(technical_html):
    result = parse_technical_section(technical_html)
    assert result.get("body_type") is not None


def test_seats_extracted(technical_html):
    result = parse_technical_section(technical_html)
    assert result.get("seats") == "5"


def test_horse_power_extracted(technical_html):
    result = parse_technical_section(technical_html)
    assert result.get("horse_power") == "100"


def test_engine_cc_extracted(technical_html):
    result = parse_technical_section(technical_html)
    assert result.get("engine_cc") is not None
    assert "1" in result["engine_cc"]  # e.g. "1,368"


def test_fuel_consumption_extracted(technical_html):
    result = parse_technical_section(technical_html)
    assert result.get("combined_fuel_consumption") is not None


def test_location_extracted(description_html):
    result = parse_description_location(description_html)
    assert result["location"] is not None
    assert "פתח תקווה" in result["location"]


def test_description_extracted(description_html):
    result = parse_description_location(description_html)
    assert result["description"] is not None
    assert len(result["description"]) > 20


def test_phone_available_is_true(description_html):
    result = parse_description_location(description_html)
    assert result["phone_available"] is True


def test_phone_number_not_stored(description_html):
    result = parse_description_location(description_html)
    assert "phone_number" not in result
    assert "tel:" not in str(result.get("description", ""))


def test_image_url_extracted_from_description(description_html):
    result = parse_description_location(description_html)
    assert result["image_url"] is not None
    assert result["image_url"].startswith("http")


def test_merge_detail_produces_detail_listing(technical_html, description_html):
    tech = parse_technical_section(technical_html)
    desc = parse_description_location(description_html)
    detail = merge_detail(tech, desc)
    assert detail.km is not None
    assert detail.location is not None
    assert detail.phone_available is True
    assert len(detail.images) >= 1
