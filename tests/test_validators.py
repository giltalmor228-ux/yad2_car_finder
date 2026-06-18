"""Tests for validators.py"""
import pytest
from yad2_car_bot.config import load_config
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
    from copy import deepcopy
    from yad2_car_bot.models import ManufacturerEntry

    cfg = deepcopy(app_config)
    # Make Hyundai use same ID as Toyota (19)
    cfg.search_profile.cars["Hyundai"] = ManufacturerEntry(manufacturer_id=19, models=[])
    issues = validate_config(cfg)
    errors = [msg for sev, msg in issues if sev == ERROR]
    assert any("19" in e for e in errors), f"Expected duplicate ID error. Got: {errors}"


def test_missing_manufacturer_id_fails(app_config):
    from copy import deepcopy
    from yad2_car_bot.models import ManufacturerEntry

    cfg = deepcopy(app_config)
    # manufacturer_id is required in ManufacturerEntry, use a sentinel None via raw dict
    # We patch the profile's cars dict directly
    cfg.search_profile.cars["TestBrand"] = ManufacturerEntry(manufacturer_id=0, models=[])
    # Set manufacturer_id to None via object mutation
    cfg.search_profile.cars["TestBrand"].manufacturer_id = None  # type: ignore
    issues = validate_config(cfg)
    errors = [msg for sev, msg in issues if sev == ERROR]
    assert any("TestBrand" in e for e in errors), f"Expected missing ID error. Got: {errors}"
