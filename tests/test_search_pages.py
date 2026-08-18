"""Tests for multi-page search collection."""
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from yad2_car_bot.parsers.search_parser import parse_feed_pagination
from yad2_car_bot.search_pages import fetch_all_search_pages
from yad2_car_bot.url_builder import with_page


def test_with_page_omits_param_on_page_one():
    base = "https://www.yad2.co.il/vehicles/cars?manufacturer=36&model=10490"
    assert "page=" not in with_page(base, 1)
    assert parse_qs(urlparse(with_page(base, 2)).query)["page"] == ["2"]
    assert parse_qs(urlparse(with_page(base, 3)).query)["page"] == ["3"]


def test_with_page_replaces_existing_page_param():
    url = "https://www.yad2.co.il/vehicles/cars?manufacturer=36&page=9"
    assert "page=9" not in with_page(url, 1)
    assert parse_qs(urlparse(with_page(url, 2)).query)["page"] == ["2"]


def test_parse_feed_pagination_from_snapshot():
    snapshot = Path("debug_snapshots/search.html")
    if not snapshot.exists():
        import pytest

        pytest.skip("debug_snapshots/search.html not present")
    pagination = parse_feed_pagination(snapshot.read_text(encoding="utf-8"))
    assert pagination is not None
    assert pagination["pages"] >= 1
    assert pagination["total"] >= pagination["pages"]


def test_fetch_all_search_pages_stops_on_fetch_failure():
    page1 = Path("debug_snapshots/search.html")
    if not page1.exists():
        import pytest

        pytest.skip("debug_snapshots/search.html not present")

    html1 = page1.read_text(encoding="utf-8")
    calls: list[str] = []

    class Client:
        def get_page(self, url, **_kwargs):
            calls.append(url)
            if "page=2" in url:
                raise RuntimeError("boom")
            return html1

    cards, enrichment, first_html = fetch_all_search_pages(
        Client(),
        "https://www.yad2.co.il/vehicles/cars?manufacturer=36",
        page_pause_seconds=0,
    )
    assert first_html == html1
    assert len(cards) >= 40
    assert enrichment
    assert any("page=2" in u for u in calls)


def test_fetch_all_search_pages_respects_known_page_count(mocker):
    page1 = Path("debug_snapshots/search.html")
    if not page1.exists():
        import pytest

        pytest.skip("debug_snapshots/search.html not present")

    html1 = page1.read_text(encoding="utf-8")
    # Force pagination.pages = 1 so we never request page 2.
    mocker.patch(
        "yad2_car_bot.search_pages.parse_feed_pagination",
        return_value={"pages": 1, "perPage": 40, "total": 10},
    )
    calls: list[str] = []

    class Client:
        def get_page(self, url, **_kwargs):
            calls.append(url)
            return html1

    cards, _enrichment, _html = fetch_all_search_pages(
        Client(),
        "https://www.yad2.co.il/vehicles/cars?manufacturer=36",
        page_pause_seconds=0,
    )
    assert len(cards) >= 1
    assert len(calls) == 1
    assert all("page=" not in u for u in calls)
