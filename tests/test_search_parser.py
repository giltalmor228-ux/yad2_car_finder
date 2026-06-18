"""Tests for parsers/search_parser.py — uses the real search_result_card.html fixture."""
import json
import pytest
from urllib.parse import urlparse, parse_qs

from yad2_car_bot.parsers.search_parser import parse_search_page, _canonicalize_url, parse_next_data


def test_parses_at_least_one_card(search_card_html):
    cards = parse_search_page(search_card_html)
    assert len(cards) >= 1


def test_listing_id_extracted(search_card_html):
    cards = parse_search_page(search_card_html)
    card = cards[0]
    assert card.listing_id, "listing_id should not be empty"
    assert card.listing_id == "xsstyghm"


def test_listing_type(search_card_html):
    cards = parse_search_page(search_card_html)
    assert cards[0].listing_type == "private-vehicle"


def test_title_extracted(search_card_html):
    cards = parse_search_page(search_card_html)
    title = cards[0].title
    assert title is not None
    assert "יונדאי" in title or "I20" in title or "Hyundai" in title.lower() or "i20" in title.lower()


def test_subtitle_extracted(search_card_html):
    cards = parse_search_page(search_card_html)
    subtitle = cards[0].subtitle
    assert subtitle is not None
    assert "1.4" in subtitle or "100" in subtitle


def test_year_extracted(search_card_html):
    cards = parse_search_page(search_card_html)
    assert cards[0].year == 2016


def test_hand_extracted(search_card_html):
    cards = parse_search_page(search_card_html)
    assert cards[0].hand == 1


def test_price_extracted(search_card_html):
    cards = parse_search_page(search_card_html)
    price = cards[0].price
    assert price is not None
    assert "50,000" in price or "50000" in price


def test_image_url_extracted(search_card_html):
    cards = parse_search_page(search_card_html)
    image_url = cards[0].image_url
    assert image_url is not None
    assert image_url.startswith("http")
    assert "yad2" in image_url or "img" in image_url


def test_tags_extracted(search_card_html):
    cards = parse_search_page(search_card_html)
    tags = cards[0].tags
    assert len(tags) >= 1
    # Expected tags from the sample
    assert any("יד ראשונה" in t for t in tags)


def test_content_hash_present(search_card_html):
    cards = parse_search_page(search_card_html)
    assert len(cards[0].raw_card_html_hash) == 32  # MD5 hex


def test_canonicalize_no_tracking_params():
    url = _canonicalize_url("private-vehicle", "abc123")
    assert "opened-from" not in url
    assert "component-type" not in url
    assert "spot" not in url
    assert "pagination" not in url


def test_canonicalize_contains_item_id():
    url = _canonicalize_url("private-vehicle", "xsstyghm")
    assert "xsstyghm" in url
    assert "private-vehicle" in url


def test_canonical_url_is_absolute(search_card_html):
    cards = parse_search_page(search_card_html)
    url = cards[0].listing_url
    assert url.startswith("https://")


# ── parse_next_data tests ───────────────────────────────────────────────────

def _make_next_data_html(listings: list) -> str:
    """Wrap a list of listing dicts inside a minimal __NEXT_DATA__ script tag."""
    payload = {
        "props": {
            "pageProps": {
                "dehydratedState": {
                    "queries": [
                        {"state": {"data": {"private": listings}}}
                    ]
                }
            }
        }
    }
    return f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(payload)}</script>'


def test_parse_next_data_returns_enrichment():
    html = _make_next_data_html([{
        "token": "abc123",
        "engineType": {"text": "בנזין"},
        "engineVolume": 1368,
        "address": {"area": {"text": "תל אביב"}},
        "metaData": {
            "coverImage": "https://img.yad2.co.il/cover.jpeg",
            "images": ["https://img.yad2.co.il/1.jpeg", "https://img.yad2.co.il/2.jpeg"],
        },
    }])
    result = parse_next_data(html)
    assert "abc123" in result
    enrichment = result["abc123"]
    assert enrichment["current_ownership"] == "פרטית"
    assert enrichment["engine_type"] == "בנזין"
    assert enrichment["engine_cc"] == "1368"
    assert enrichment["location"] == "תל אביב"
    assert len(enrichment["images"]) == 2
    assert enrichment["images"][0].url == "https://img.yad2.co.il/1.jpeg"


def test_parse_next_data_empty_on_bad_json():
    html = '<script id="__NEXT_DATA__" type="application/json">{bad json!!}</script>'
    assert parse_next_data(html) == {}


def test_parse_next_data_empty_on_missing_section():
    html = '<script id="__NEXT_DATA__" type="application/json">{"props": {}}</script>'
    assert parse_next_data(html) == {}



def test_parsed_at_is_set(search_card_html):
    cards = parse_search_page(search_card_html)
    assert cards[0].parsed_at is not None
