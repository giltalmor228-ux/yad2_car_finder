from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo

    _DISPLAY_TZ = ZoneInfo("Asia/Jerusalem")
except Exception:  # pragma: no cover
    _DISPLAY_TZ = timezone.utc

# Columns aligned with the Telegram/email message template, plus tracking fields.
CSV_COLUMNS = [
    "listing_id",
    "title",
    "subtitle",
    "price",
    "year",
    "km",
    "hand",
    "gearbox",
    "engine",
    "engine_type",
    "engine_cc",
    "location",
    "current_ownership",
    "original_ownership",
    "test_valid_until",
    "score",
    "decision",
    "positive_reasons",
    "flags",
    "image_count",
    "url",
    "color",
    "body_type",
    "phone_available",
    "first_seen_at",
    "last_seen_at",
    "last_notified_at",
    "tags",
]


def default_csv_path(base_dir: Path | None = None) -> Path:
    root = base_dir or Path.cwd()
    return Path(root) / "data" / "listings_export.csv"


def _join_list(raw: str | None) -> str:
    if not raw:
        return ""
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return str(raw)
    if isinstance(data, list):
        return " | ".join(str(x) for x in data)
    return str(data)


def _format_engine(engine_type: str | None, engine_cc: str | None) -> str:
    parts = [p for p in ((engine_type or "").strip(), (engine_cc or "").strip()) if p]
    return ", ".join(parts)


def _format_dt(raw: str | None) -> str:
    """Format ISO timestamps as ``DD/MM/YYYY HH:MM`` (Israel local time)."""
    if not raw:
        return ""
    text = str(raw).strip()
    if not text:
        return ""
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_DISPLAY_TZ).strftime("%d/%m/%Y %H:%M")


def _latest_nonempty(column: str) -> str:
    """SQL snippet: latest non-empty value of a listing_details column."""
    return f"""(
        SELECT d.{column} FROM listing_details d
        WHERE d.listing_id = l.listing_id
          AND d.{column} IS NOT NULL
          AND TRIM(CAST(d.{column} AS TEXT)) != ''
        ORDER BY d.id DESC
        LIMIT 1
    )"""


def export_listings_csv(
    db_path: str | Path,
    csv_path: str | Path | None = None,
) -> Path:
    """Write one CSV row per listing with the same fields used in notifications."""
    db_path = Path(db_path)
    out = Path(csv_path) if csv_path else db_path.parent / "listings_export.csv"
    out.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # Ensure optional column exists for older DBs.
        cols = {
            r[1]
            for r in conn.execute("PRAGMA table_info(listing_details)").fetchall()
        }
        has_original = "original_ownership" in cols

        original_select = (
            _latest_nonempty("original_ownership") + " AS original_ownership"
            if has_original
            else "NULL AS original_ownership"
        )

        rows = conn.execute(
            f"""
            SELECT
                l.listing_id,
                l.title,
                l.subtitle,
                l.price,
                l.year,
                l.hand,
                l.canonical_url AS url,
                l.tags,
                l.first_seen_at,
                l.last_seen_at,
                {_latest_nonempty("km")} AS km,
                {_latest_nonempty("gearbox")} AS gearbox,
                {_latest_nonempty("engine_type")} AS engine_type,
                {_latest_nonempty("engine_cc")} AS engine_cc,
                {_latest_nonempty("location")} AS location,
                {_latest_nonempty("current_ownership")} AS current_ownership,
                {original_select},
                {_latest_nonempty("test_valid_until")} AS test_valid_until,
                {_latest_nonempty("color")} AS color,
                {_latest_nonempty("body_type")} AS body_type,
                (
                    SELECT d.phone_available FROM listing_details d
                    WHERE d.listing_id = l.listing_id
                    ORDER BY d.id DESC LIMIT 1
                ) AS phone_available,
                s.score,
                s.decision,
                s.positive_reasons,
                s.flags,
                (
                    SELECT COUNT(*) FROM listing_images i WHERE i.listing_id = l.listing_id
                ) AS image_count,
                (
                    SELECT n.sent_at FROM notifications n
                    WHERE n.listing_id = l.listing_id AND n.dry_run = 0
                    ORDER BY n.sent_at DESC LIMIT 1
                ) AS last_notified_at
            FROM listings l
            LEFT JOIN scores s
                ON s.id = (
                    SELECT s2.id FROM scores s2
                    WHERE s2.listing_id = l.listing_id
                    ORDER BY s2.id DESC LIMIT 1
                )
            ORDER BY l.first_seen_at DESC
            """
        ).fetchall()
    finally:
        conn.close()

    with out.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            engine_type = row["engine_type"]
            engine_cc = row["engine_cc"]
            writer.writerow(
                {
                    "listing_id": row["listing_id"] or "",
                    "title": row["title"] or "",
                    "subtitle": row["subtitle"] or "",
                    "price": row["price"] or "",
                    "year": row["year"] if row["year"] is not None else "",
                    "km": row["km"] or "",
                    "hand": row["hand"] if row["hand"] is not None else "",
                    "gearbox": row["gearbox"] or "",
                    "engine": _format_engine(engine_type, engine_cc),
                    "engine_type": engine_type or "",
                    "engine_cc": engine_cc or "",
                    "location": row["location"] or "",
                    "current_ownership": row["current_ownership"] or "",
                    "original_ownership": row["original_ownership"] or "",
                    "test_valid_until": row["test_valid_until"] or "",
                    "score": row["score"] if row["score"] is not None else "",
                    "decision": row["decision"] or "",
                    "positive_reasons": _join_list(row["positive_reasons"]),
                    "flags": _join_list(row["flags"]),
                    "image_count": row["image_count"] or 0,
                    "url": row["url"] or "",
                    "color": row["color"] or "",
                    "body_type": row["body_type"] or "",
                    "phone_available": (
                        "yes"
                        if row["phone_available"]
                        else "no"
                        if row["phone_available"] is not None
                        else ""
                    ),
                    "first_seen_at": _format_dt(row["first_seen_at"]),
                    "last_seen_at": _format_dt(row["last_seen_at"]),
                    "last_notified_at": _format_dt(row["last_notified_at"]),
                    "tags": _join_list(row["tags"]),
                }
            )

    return out
