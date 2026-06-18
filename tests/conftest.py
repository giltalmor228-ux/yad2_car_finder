"""Shared pytest fixtures for all test modules."""
from pathlib import Path

import pytest

SAMPLES_DIR = Path(__file__).parent.parent / "samples"
CONFIGS_DIR = Path(__file__).parent.parent / "configs"
DATA_DIR = Path(__file__).parent.parent / "data"
PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture
def search_card_html():
    return (SAMPLES_DIR / "search_result_card.html").read_text(encoding="utf-8")


@pytest.fixture
def technical_html():
    return (SAMPLES_DIR / "listing_detail_technical_section.html").read_text(encoding="utf-8")


@pytest.fixture
def description_html():
    return (SAMPLES_DIR / "listing_detail_description_location_phone_image.html").read_text(encoding="utf-8")


@pytest.fixture
def app_config():
    from yad2_car_bot.config import load_config
    return load_config(PROJECT_ROOT)
