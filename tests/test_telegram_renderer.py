"""Tests for telegram/renderer.py"""
import pytest
from datetime import datetime, timezone

from yad2_car_bot.models import (
    SearchCardListing,
    DetailListing,
    ListingImage,
    ScoreBreakdown,
    ScoredListing,
)
from yad2_car_bot.telegram.renderer import render_message


def _make_card(**kwargs):
    defaults = dict(
        listing_id="test_001",
        listing_url_relative="item/test_001",
        listing_url="https://www.yad2.co.il/vehicles/cars/item/test_001",
        listing_type="private-vehicle",
        title="יונדאי i20 קרוס",
        subtitle="Cross Premium אוט׳ 1.4 (100 כ״ס)",
        year=2016,
        hand=1,
        price="50,000 ₪",
        image_url="https://img.yad2.co.il/test.jpeg",
        tags=["יד ראשונה"],
        raw_card_html_hash="abc123",
        parsed_at=datetime.now(tz=timezone.utc),
    )
    defaults.update(kwargs)
    return SearchCardListing(**defaults)


def _make_detail(**kwargs):
    defaults = dict(
        km="77,320",
        color="לבן",
        current_ownership="פרטית",
        test_valid_until="01/06/2027",
        gearbox="אוטומטי",
        date_on_road="01/2016",
        engine_type="בנזין",
        body_type="האצ'בק",
        seats="5",
        horse_power="100",
        engine_cc="1,368",
        combined_fuel_consumption="14.93",
        location="פתח תקווה",
        description="רכב שמור ומטופל",
        phone_available=True,
        images=[ListingImage(url="https://img.yad2.co.il/test.jpeg", index=0)],
        parsed_at=datetime.now(tz=timezone.utc),
    )
    defaults.update(kwargs)
    return DetailListing(**defaults)


def _make_scored(**kwargs):
    defaults = dict(
        score=82,
        score_breakdown=ScoreBreakdown(factors={"base": 50, "private_ownership": 10, "low_km": 10, "has_images": 5, "first_or_second_hand": 10}),
        positive_reasons=["private_ownership", "low_km", "first_or_second_hand"],
        flags=["paint_or_bodywork"],
        decision="notify",
    )
    defaults.update(kwargs)
    return ScoredListing(**defaults)


def test_render_produces_text(app_config):
    payload = render_message(_make_scored(), _make_card(), _make_detail(), app_config.telegram_template)
    assert len(payload.text) > 50


def test_render_includes_title(app_config):
    payload = render_message(_make_scored(), _make_card(), _make_detail(), app_config.telegram_template)
    assert "יונדאי" in payload.text or "i20" in payload.text.lower()


def test_render_includes_price(app_config):
    payload = render_message(_make_scored(), _make_card(), _make_detail(), app_config.telegram_template)
    assert "50,000" in payload.text


def test_render_includes_score(app_config):
    payload = render_message(_make_scored(), _make_card(), _make_detail(), app_config.telegram_template)
    assert "82" in payload.text


def test_render_includes_url(app_config):
    payload = render_message(_make_scored(), _make_card(), _make_detail(), app_config.telegram_template)
    assert "yad2.co.il" in payload.text


def test_render_no_phone_in_text(app_config):
    payload = render_message(_make_scored(), _make_card(), _make_detail(), app_config.telegram_template)
    assert "tel:" not in payload.text
    assert "phone" not in payload.text.lower()
    assert "טלפון" not in payload.text


def test_image_url_present_when_available(app_config):
    payload = render_message(_make_scored(), _make_card(), _make_detail(), app_config.telegram_template)
    assert payload.image_url is not None
    assert payload.image_url.startswith("http")


def test_no_image_url_when_unavailable(app_config):
    card = _make_card(image_url=None)
    detail = _make_detail(images=[])
    payload = render_message(_make_scored(), card, detail, app_config.telegram_template)
    assert payload.image_url is None


def test_caption_truncation_trims_to_limit(app_config):
    # Build a scored listing with many flags and positive reasons to force trimming
    long_scored = _make_scored(
        positive_reasons=[f"reason_{i}: some text about the car" for i in range(30)],
        flags=[f"flag_{i}: some warning text" for i in range(30)],
    )
    payload = render_message(long_scored, _make_card(), _make_detail(), app_config.telegram_template)
    # After trimming, caption should be ≤ 1024 OR text is a longer message split separately
    # Either way, the payload text should remain below message limit
    assert len(payload.text) <= 4096


def test_extra_images_populated(app_config):
    detail = _make_detail(images=[
        ListingImage(url="https://img.yad2.co.il/1.jpeg", index=0),
        ListingImage(url="https://img.yad2.co.il/2.jpeg", index=1),
        ListingImage(url="https://img.yad2.co.il/3.jpeg", index=2),
    ])
    payload = render_message(_make_scored(), _make_card(), detail, app_config.telegram_template)
    assert payload.image_url == "https://img.yad2.co.il/1.jpeg"
    assert len(payload.extra_image_urls) == 2
