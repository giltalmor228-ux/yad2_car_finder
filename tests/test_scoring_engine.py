"""Tests for scoring/scoring_engine.py"""
import pytest
from datetime import datetime, timezone

from yad2_car_bot.models import SearchCardListing, DetailListing, KeywordMatch
from yad2_car_bot.scoring.keyword_matcher import match_keywords
from yad2_car_bot.scoring.scoring_engine import score_listing


def _make_card(**kwargs):
    defaults = dict(
        listing_id="test_001",
        listing_url_relative="item/test_001",
        listing_url="https://www.yad2.co.il/vehicles/cars/item/test_001",
        listing_type="private-vehicle",
        title="יונדאי i20",
        subtitle="1.4 אוטומט",
        year=2018,
        hand=1,
        price="45,000 ₪",
        image_url="https://img.yad2.co.il/test.jpeg",
        tags=["יד ראשונה"],
        raw_card_html_hash="abc123",
        parsed_at=datetime.now(tz=timezone.utc),
    )
    defaults.update(kwargs)
    return SearchCardListing(**defaults)


def _make_detail(**kwargs):
    defaults = dict(
        km="60,000",
        color="לבן",
        current_ownership="פרטית",
        test_valid_until="01/06/2027",
        gearbox="אוטומטי",
        date_on_road="01/2018",
        engine_type="בנזין",
        body_type="האצ'בק",
        seats="5",
        horse_power="100",
        engine_cc="1,368",
        combined_fuel_consumption="14.93",
        location="תל אביב",
        description="רכב שמור ומטופל, ספר טיפולים",
        phone_available=True,
        images=[],
        parsed_at=datetime.now(tz=timezone.utc),
    )
    defaults.update(kwargs)
    return DetailListing(**defaults)


def test_base_score_is_present(app_config):
    card = _make_card()
    detail = _make_detail()
    matches = match_keywords(detail.description, card.tags, app_config.keyword_rules)
    scored = score_listing(card, detail, matches, app_config.scoring_rules)
    assert "base" in scored.score_breakdown.factors
    assert scored.score_breakdown.factors["base"] == 50


def test_hard_reject_gives_zero_score(app_config):
    card = _make_card()
    detail = _make_detail(description="מונית לשעבר למכירה")
    matches = match_keywords(detail.description, card.tags, app_config.keyword_rules)
    scored = score_listing(card, detail, matches, app_config.scoring_rules)
    assert scored.score == 0
    assert scored.decision == "rejected"
    assert len(scored.flags) > 0


def test_no_hard_reject_decision_is_notify_or_skip(app_config):
    card = _make_card()
    detail = _make_detail()
    matches = match_keywords(detail.description, card.tags, app_config.keyword_rules)
    scored = score_listing(card, detail, matches, app_config.scoring_rules)
    assert scored.decision in ("notify", "skip")


def test_private_ownership_adds_points(app_config):
    card = _make_card()
    detail = _make_detail(current_ownership="פרטית")
    matches = match_keywords(detail.description, card.tags, app_config.keyword_rules)
    scored = score_listing(card, detail, matches, app_config.scoring_rules)
    assert "private_ownership" in scored.score_breakdown.factors
    assert scored.score_breakdown.factors["private_ownership"] > 0


def test_missing_price_penalizes(app_config):
    card = _make_card(price=None)
    detail = _make_detail()
    matches = match_keywords(detail.description, card.tags, app_config.keyword_rules)
    scored = score_listing(card, detail, matches, app_config.scoring_rules)
    assert "missing_price" in scored.score_breakdown.factors
    assert scored.score_breakdown.factors["missing_price"] < 0


def test_missing_image_penalizes(app_config):
    card = _make_card(image_url=None)
    detail = _make_detail()
    matches = match_keywords(detail.description, card.tags, app_config.keyword_rules)
    scored = score_listing(card, detail, matches, app_config.scoring_rules)
    assert "missing_images" in scored.score_breakdown.factors
    assert scored.score_breakdown.factors["missing_images"] < 0


def test_low_km_adds_points(app_config):
    card = _make_card()
    detail = _make_detail(km="30,000")
    matches = match_keywords(detail.description, card.tags, app_config.keyword_rules)
    scored = score_listing(card, detail, matches, app_config.scoring_rules)
    assert "low_km" in scored.score_breakdown.factors
    assert scored.score_breakdown.factors["low_km"] > 0


def test_high_km_penalizes(app_config):
    card = _make_card()
    detail = _make_detail(km="140,000")
    matches = match_keywords(detail.description, card.tags, app_config.keyword_rules)
    scored = score_listing(card, detail, matches, app_config.scoring_rules)
    assert "high_km" in scored.score_breakdown.factors
    assert scored.score_breakdown.factors["high_km"] < 0


def test_score_capped_at_100(app_config):
    card = _make_card()
    detail = _make_detail(description="שמור ומטופל מרכז שירות מורשה ספר טיפולים קבלות מתחייב בבדיקה")
    matches = match_keywords(detail.description, card.tags, app_config.keyword_rules)
    scored = score_listing(card, detail, matches, app_config.scoring_rules)
    assert scored.score <= 100


def test_score_not_below_zero(app_config):
    card = _make_card(price=None, image_url=None)
    detail = _make_detail(current_ownership=None, description="ירידת ערך, ליסינג, נורת מנוע")
    matches = match_keywords(detail.description, card.tags, app_config.keyword_rules)
    scored = score_listing(card, detail, matches, app_config.scoring_rules)
    assert scored.score >= 0


def test_score_breakdown_sums_to_score(app_config):
    card = _make_card()
    detail = _make_detail()
    matches = match_keywords(detail.description, card.tags, app_config.keyword_rules)
    scored = score_listing(card, detail, matches, app_config.scoring_rules)
    if scored.decision != "rejected":
        # score is clamped; sum may differ due to clamping
        raw_sum = sum(scored.score_breakdown.factors.values())
        assert scored.score == max(0, min(100, raw_sum))


def test_notify_threshold(app_config):
    """A high-quality listing should meet the notify threshold when notify_all is off."""
    rules = dict(app_config.scoring_rules)
    rules["notify_all_matches"] = False
    rules["minimum_score_to_notify"] = 70
    card = _make_card()
    detail = _make_detail(
        km="40,000",
        current_ownership="פרטית",
        test_valid_until="01/2027",
        description="שמור ומטופל, ספר טיפולים, קבלות, מתחייב בבדיקה",
    )
    matches = match_keywords(detail.description, card.tags, app_config.keyword_rules)
    scored = score_listing(card, detail, matches, rules)
    assert scored.score >= rules["minimum_score_to_notify"]
    assert scored.decision == "notify"


def test_notify_all_matches_forces_notify(app_config):
    rules = dict(app_config.scoring_rules)
    rules["notify_all_matches"] = True
    rules["minimum_score_to_notify"] = 99
    card = _make_card(hand=None, price=None, image_url=None)
    detail = _make_detail(current_ownership=None, description="רכב רגיל")
    matches = match_keywords(detail.description, card.tags, app_config.keyword_rules)
    scored = score_listing(card, detail, matches, rules)
    assert scored.decision == "notify"
