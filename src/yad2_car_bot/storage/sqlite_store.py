from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from yad2_car_bot.models import (
    DetailListing,
    KeywordMatch,
    SearchCardListing,
    ScoredListing,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS search_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at TEXT NOT NULL,
    profile_name TEXT NOT NULL,
    search_url TEXT,
    listings_found INTEGER DEFAULT 0,
    listings_new INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id TEXT UNIQUE NOT NULL,
    canonical_url TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    listing_type TEXT,
    title TEXT,
    subtitle TEXT,
    year INTEGER,
    hand INTEGER,
    price TEXT,
    image_url TEXT,
    tags TEXT,
    parsed_at TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    source_flags TEXT,
    parser_provenance TEXT
);

CREATE TABLE IF NOT EXISTS listing_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id TEXT NOT NULL,
    km TEXT,
    color TEXT,
    current_ownership TEXT,
    test_valid_until TEXT,
    gearbox TEXT,
    date_on_road TEXT,
    engine_type TEXT,
    body_type TEXT,
    seats TEXT,
    horse_power TEXT,
    engine_cc TEXT,
    combined_fuel_consumption TEXT,
    location TEXT,
    description TEXT,
    phone_available INTEGER DEFAULT 0,
    parsed_at TEXT
);

CREATE TABLE IF NOT EXISTS listing_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id TEXT NOT NULL,
    url TEXT NOT NULL,
    image_index INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS keyword_hits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id TEXT NOT NULL,
    term TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT NOT NULL,
    field_matched TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id TEXT NOT NULL,
    score INTEGER NOT NULL,
    score_breakdown TEXT,
    positive_reasons TEXT,
    flags TEXT,
    decision TEXT,
    scored_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id TEXT NOT NULL,
    sent_at TEXT NOT NULL,
    score_at_send INTEGER,
    price_at_send TEXT,
    dry_run INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS parser_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id TEXT,
    url TEXT,
    snapshot_path TEXT,
    snapshot_type TEXT,
    captured_at TEXT NOT NULL
);
"""

# Thresholds for re-notification
_SCORE_CHANGE_THRESHOLD = 10
_PRICE_DROP_PCT_THRESHOLD = 0.05


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _extract_price_int(price_str: Optional[str]) -> Optional[int]:
    """Extract integer from price string like '50,000 ₪'."""
    if not price_str:
        return None
    import re
    digits = re.sub(r"[^\d]", "", price_str)
    return int(digits) if digits else None


class SQLiteStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "SQLiteStore":
        self.connect()
        return self

    def __exit__(self, *_) -> None:
        self.close()

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Not connected. Use connect() or context manager.")
        return self._conn

    # ── Search runs ──────────────────────────────────────────────────────────

    def start_run(self, profile_name: str, search_url: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO search_runs (run_at, profile_name, search_url) VALUES (?,?,?)",
            (_now(), profile_name, search_url),
        )
        self.conn.commit()
        return cur.lastrowid

    def finish_run(self, run_id: int, listings_found: int, listings_new: int) -> None:
        self.conn.execute(
            "UPDATE search_runs SET listings_found=?, listings_new=? WHERE id=?",
            (listings_found, listings_new, run_id),
        )
        self.conn.commit()

    # ── Deduplication ────────────────────────────────────────────────────────

    def is_known_listing(
        self,
        listing_id: str,
        canonical_url: str,
        content_hash: str,
    ) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM listings WHERE listing_id=? OR canonical_url=? OR content_hash=?",
            (listing_id, canonical_url, content_hash),
        ).fetchone()
        return row is not None

    # ── Save listing ─────────────────────────────────────────────────────────

    def save_listing(
        self,
        card: SearchCardListing,
        detail: Optional[DetailListing] = None,
        keyword_hits: Optional[list[KeywordMatch]] = None,
        scored: Optional[ScoredListing] = None,
    ) -> None:
        now = _now()
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO listings (
                    listing_id, canonical_url, content_hash, listing_type,
                    title, subtitle, year, hand, price, image_url, tags,
                    parsed_at, first_seen_at, last_seen_at, source_flags, parser_provenance
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(listing_id) DO UPDATE SET
                    last_seen_at=excluded.last_seen_at,
                    content_hash=excluded.content_hash,
                    price=excluded.price
                """,
                (
                    card.listing_id,
                    card.listing_url,
                    card.raw_card_html_hash,
                    card.listing_type,
                    card.title,
                    card.subtitle,
                    card.year,
                    card.hand,
                    card.price,
                    card.image_url,
                    json.dumps(card.tags, ensure_ascii=False),
                    card.parsed_at.isoformat(),
                    now,
                    now,
                    json.dumps(card.source_flags, ensure_ascii=False),
                    card.parser_provenance,
                ),
            )

            if detail:
                self.conn.execute(
                    """
                    INSERT INTO listing_details (
                        listing_id, km, color, current_ownership, test_valid_until,
                        gearbox, date_on_road, engine_type, body_type, seats,
                        horse_power, engine_cc, combined_fuel_consumption,
                        location, description, phone_available, parsed_at
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        card.listing_id,
                        detail.km, detail.color, detail.current_ownership,
                        detail.test_valid_until, detail.gearbox, detail.date_on_road,
                        detail.engine_type, detail.body_type, detail.seats,
                        detail.horse_power, detail.engine_cc,
                        detail.combined_fuel_consumption, detail.location,
                        detail.description, int(detail.phone_available),
                        detail.parsed_at.isoformat(),
                    ),
                )
                for img in detail.images:
                    self.conn.execute(
                        "INSERT INTO listing_images (listing_id, url, image_index) VALUES (?,?,?)",
                        (card.listing_id, img.url, img.index),
                    )

            if keyword_hits:
                for hit in keyword_hits:
                    self.conn.execute(
                        "INSERT INTO keyword_hits (listing_id, term, category, subcategory, field_matched)"
                        " VALUES (?,?,?,?,?)",
                        (card.listing_id, hit.term, hit.category, hit.subcategory, hit.field_matched),
                    )

            if scored:
                self.conn.execute(
                    """
                    INSERT INTO scores (
                        listing_id, score, score_breakdown, positive_reasons,
                        flags, decision, scored_at
                    ) VALUES (?,?,?,?,?,?,?)
                    """,
                    (
                        card.listing_id,
                        scored.score,
                        json.dumps(scored.score_breakdown.factors, ensure_ascii=False),
                        json.dumps(scored.positive_reasons, ensure_ascii=False),
                        json.dumps(scored.flags, ensure_ascii=False),
                        scored.decision,
                        now,
                    ),
                )

    # ── Notification deduplication ───────────────────────────────────────────

    def should_notify(
        self,
        listing_id: str,
        new_score: int,
        new_price: Optional[str],
    ) -> bool:
        """Return True if a notification should be sent for this listing."""
        row = self.conn.execute(
            "SELECT score_at_send, price_at_send FROM notifications WHERE listing_id=? AND dry_run=0 ORDER BY sent_at DESC LIMIT 1",
            (listing_id,),
        ).fetchone()

        if row is None:
            return True  # never notified

        prev_score = row["score_at_send"]
        prev_price = row["price_at_send"]

        # Re-notify if score changed materially
        if prev_score is not None and abs(new_score - prev_score) >= _SCORE_CHANGE_THRESHOLD:
            return True

        # Re-notify if price dropped materially
        prev_price_int = _extract_price_int(prev_price)
        new_price_int = _extract_price_int(new_price)
        if prev_price_int and new_price_int:
            drop_pct = (prev_price_int - new_price_int) / prev_price_int
            if drop_pct >= _PRICE_DROP_PCT_THRESHOLD:
                return True

        return False

    def record_notification(
        self,
        listing_id: str,
        score: int,
        price: Optional[str],
        dry_run: bool = True,
    ) -> None:
        self.conn.execute(
            "INSERT INTO notifications (listing_id, sent_at, score_at_send, price_at_send, dry_run) VALUES (?,?,?,?,?)",
            (listing_id, _now(), score, price, int(dry_run)),
        )
        self.conn.commit()

    def record_snapshot(
        self,
        url: str,
        snapshot_path: str,
        snapshot_type: str,
        listing_id: Optional[str] = None,
    ) -> None:
        self.conn.execute(
            "INSERT INTO parser_snapshots (listing_id, url, snapshot_path, snapshot_type, captured_at)"
            " VALUES (?,?,?,?,?)",
            (listing_id, url, snapshot_path, snapshot_type, _now()),
        )
        self.conn.commit()
