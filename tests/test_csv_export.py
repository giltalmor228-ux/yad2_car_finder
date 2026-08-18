"""Tests for csv_export.py"""
import csv
from datetime import datetime, timezone
from pathlib import Path

from yad2_car_bot.csv_export import CSV_COLUMNS, export_listings_csv
from yad2_car_bot.models import (
    DetailListing,
    ScoreBreakdown,
    ScoredListing,
    SearchCardListing,
)
from yad2_car_bot.storage.sqlite_store import SQLiteStore


def _card(**kwargs) -> SearchCardListing:
    defaults = dict(
        listing_id="csv001",
        listing_url_relative="/vehicles/item/csv001",
        listing_url="https://www.yad2.co.il/vehicles/item/csv001",
        listing_type="private-vehicle",
        title="מאזדה 3",
        subtitle="אוט׳",
        year=2018,
        hand=1,
        price="45,000 ₪",
        image_url="https://img.yad2.co.il/a.jpeg",
        tags=["יד ראשונה"],
        raw_card_html_hash="hash1",
        parsed_at=datetime.now(tz=timezone.utc),
    )
    defaults.update(kwargs)
    return SearchCardListing(**defaults)


def _detail(**kwargs) -> DetailListing:
    defaults = dict(
        km="60,000",
        color="לבן",
        current_ownership="פרטית",
        original_ownership="פרטית",
        test_valid_until="01/2027",
        gearbox="אוטומט",
        engine_type="בנזין",
        engine_cc="1,500",
        location="תל אביב",
        phone_available=True,
        parsed_at=datetime.now(tz=timezone.utc),
    )
    defaults.update(kwargs)
    return DetailListing(**defaults)


def test_export_listings_csv_writes_message_fields(tmp_path):
    db = tmp_path / "test.sqlite"
    out = tmp_path / "cars.csv"
    with SQLiteStore(db) as store:
        store.save_listing(
            _card(),
            _detail(),
            scored=ScoredListing(
                score=80,
                score_breakdown=ScoreBreakdown(factors={"base": 50}),
                positive_reasons=["low_km"],
                flags=["soft"],
                decision="notify",
            ),
        )
        # Later enrichment without km must not wipe km in the CSV.
        store.save_listing(_card(), _detail(km=None, location="חיפה"))
        store.record_notification("csv001", 80, "45,000 ₪", dry_run=False)

    written = export_listings_csv(db, out)
    assert written == out
    with out.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert list(rows[0].keys()) == CSV_COLUMNS
    row = rows[0]
    assert row["listing_id"] == "csv001"
    assert row["title"] == "מאזדה 3"
    assert row["km"] == "60,000"
    assert row["location"] == "חיפה"
    assert row["engine"] == "בנזין, 1,500"
    assert row["original_ownership"] == "פרטית"
    assert row["score"] == "80"
    assert row["positive_reasons"] == "low_km"
    assert row["url"].endswith("/csv001")
    assert row["last_notified_at"]
    # DD/MM/YYYY HH:MM
    assert "/" in row["first_seen_at"] and ":" in row["first_seen_at"]
    assert "T" not in row["first_seen_at"]
