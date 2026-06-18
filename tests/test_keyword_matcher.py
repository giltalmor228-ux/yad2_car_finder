"""Tests for scoring/keyword_matcher.py"""
import pytest

from yad2_car_bot.scoring.keyword_matcher import match_keywords
from yad2_car_bot.parsers.html_utils import normalize_hebrew


def test_normalize_strips_geresh():
    result = normalize_hebrew("קילומטראז׳")
    # Geresh (׳) must be removed; the base Hebrew letters remain
    assert "׳" not in result
    assert "קילומטראז" in result


def test_normalize_collapses_whitespace():
    assert normalize_hebrew("  foo   bar  ") == "foo bar"


def test_hard_reject_taxi(app_config):
    matches = match_keywords("מונית מכירה", [], app_config.keyword_rules)
    cats = [m.category for m in matches]
    assert "hard_reject" in cats


def test_hard_reject_accident(app_config):
    matches = match_keywords("הרכב עבר תאונה חזקה", [], app_config.keyword_rules)
    cats = [m.category for m in matches]
    assert "hard_reject" in cats


def test_hard_reject_severe_mechanical(app_config):
    matches = match_keywords("הוחלף מנוע לפני שנה", [], app_config.keyword_rules)
    cats = [m.category for m in matches]
    assert "hard_reject" in cats


def test_soft_flag_leasing(app_config):
    matches = match_keywords("ליסינג לשעבר", [], app_config.keyword_rules)
    cats = [m.category for m in matches]
    subcats = [m.subcategory for m in matches]
    assert "soft_flags" in cats
    assert "leasing_or_company" in subcats


def test_soft_flag_paint(app_config):
    matches = match_keywords("עברה פחחות ותיקוני צבע", [], app_config.keyword_rules)
    cats = [m.category for m in matches]
    assert "soft_flags" in cats


def test_positive_condition_match(app_config):
    matches = match_keywords("הרכב שמור ומטופל", [], app_config.keyword_rules)
    cats = [m.category for m in matches]
    assert "positive" in cats


def test_positive_match_in_tags(app_config):
    matches = match_keywords("", ["יד ראשונה", "ספר טיפולים"], app_config.keyword_rules)
    cats = [m.category for m in matches]
    assert "positive" in cats


def test_match_records_term(app_config):
    matches = match_keywords("מרכז שירות מורשה", [], app_config.keyword_rules)
    terms = [m.term for m in matches]
    assert "מרכז שירות מורשה" in terms


def test_match_records_field_matched(app_config):
    matches = match_keywords("", ["ספר טיפולים"], app_config.keyword_rules)
    fields = [m.field_matched for m in matches]
    assert "tags" in fields


def test_no_false_positives(app_config):
    matches = match_keywords("רכב רגיל למכירה", [], app_config.keyword_rules)
    cats = [m.category for m in matches]
    assert "hard_reject" not in cats


def test_real_description_sample(app_config):
    """The sample description should produce positive matches and soft flag for paint."""
    desc = (
        "למכירה יונדאי i20 קרוס, שמורה ומטופלת בזמן. הרכב עבר עכשיו טסט חלק "
        "(בתוקף לשנה שלמה!) ועבר צביעה קוסמטיקה למכסה המנוע והספוילרים "
        "במרכז שירות מורשה כלמוביל יונדאי (יש קבלות ותיעוד מלא) "
        "בנוסף לגלגלי מגנזיום. הרכב נוסע מושלם, אפס תקלות מכניות."
    )
    matches = match_keywords(desc, [], app_config.keyword_rules)
    cats = set(m.category for m in matches)
    assert "positive" in cats
    # paint/bodywork (צביעה) is a soft flag
    assert "soft_flags" in cats
    # no hard reject
    assert "hard_reject" not in cats
