"""Tests for validators.py"""
from copy import deepcopy

from yad2_car_bot.models import SearchGroup
from yad2_car_bot.validators import validate_config, ERROR, WARNING


def test_valid_config_has_no_errors(app_config):
    issues = validate_config(app_config)
    errors = [msg for sev, msg in issues if sev == ERROR]
    assert errors == [], f"Unexpected errors: {errors}"


def test_manual_verify_once_generates_warning(app_config):
    issues = validate_config(app_config)
    warnings = [msg for sev, msg in issues if sev == WARNING]
    # Suzuki (36) and Nissan (32) are manual_verify_once in filter metadata
    assert any("Suzuki" in w or "36" in w for w in warnings), \
        f"Expected Suzuki warning. Got: {warnings}"


def test_duplicate_manufacturer_id_fails(app_config):
    from yad2_car_bot.models import ManufacturerEntry

    cfg = deepcopy(app_config)
    cfg.search_profile.cars["Hyundai"] = ManufacturerEntry(manufacturer_id=19, models=[])
    issues = validate_config(cfg)
    errors = [msg for sev, msg in issues if sev == ERROR]
    assert any("19" in e for e in errors), f"Expected duplicate ID error. Got: {errors}"


def test_missing_manufacturer_id_fails(app_config):
    from yad2_car_bot.models import ManufacturerEntry

    cfg = deepcopy(app_config)
    cfg.search_profile.cars["TestBrand"] = ManufacturerEntry(manufacturer_id=0, models=[])
    cfg.search_profile.cars["TestBrand"].manufacturer_id = None  # type: ignore
    issues = validate_config(cfg)
    errors = [msg for sev, msg in issues if sev == ERROR]
    assert any("TestBrand" in e for e in errors), f"Expected missing ID error. Got: {errors}"


def test_search_group_too_many_manufacturers_fails(app_config):
    cfg = deepcopy(app_config)
    cfg.search_profile.search_groups = [
        SearchGroup(manufacturers=[19, 21, 27, 36, 32], models=[10247])
    ]
    issues = validate_config(cfg)
    errors = [msg for sev, msg in issues if sev == ERROR]
    assert any("manufacturers" in e and "at most 4" in e for e in errors), (
        f"Expected manufacturer cap error. Got: {errors}"
    )


def test_search_group_too_many_models_fails(app_config):
    cfg = deepcopy(app_config)
    cfg.search_profile.search_groups = [
        SearchGroup(
            manufacturers=[19],
            models=[10247, 10226, 10238, 10225, 10218],
        )
    ]
    issues = validate_config(cfg)
    errors = [msg for sev, msg in issues if sev == ERROR]
    assert any("model" in e and "at most 4" in e for e in errors), (
        f"Expected model cap error. Got: {errors}"
    )


def test_search_group_empty_manufacturers_fails(app_config):
    cfg = deepcopy(app_config)
    cfg.search_profile.search_groups = [SearchGroup(manufacturers=[], models=[10247])]
    issues = validate_config(cfg)
    errors = [msg for sev, msg in issues if sev == ERROR]
    assert any("manufacturers is empty" in e for e in errors), (
        f"Expected empty manufacturers error. Got: {errors}"
    )


def test_unknown_model_id_fails(app_config):
    cfg = deepcopy(app_config)
    cfg.search_profile.search_groups = [
        SearchGroup(manufacturers=[19], models=[99999999])
    ]
    issues = validate_config(cfg)
    errors = [msg for sev, msg in issues if sev == ERROR]
    assert any("99999999" in e and "unknown" in e for e in errors), (
        f"Expected unknown model ID error. Got: {errors}"
    )


def test_duplicate_model_id_across_groups_warns(app_config):
    cfg = deepcopy(app_config)
    cfg.search_profile.search_groups = [
        SearchGroup(manufacturers=[19], models=[10247, 10226]),
        SearchGroup(manufacturers=[19], models=[10247, 10238]),
    ]
    issues = validate_config(cfg)
    warnings = [msg for sev, msg in issues if sev == WARNING]
    assert any("10247" in w and "appears in both" in w for w in warnings), (
        f"Expected duplicate-model warning. Got: {warnings}"
    )
