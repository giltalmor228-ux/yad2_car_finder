from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import click
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger("yad2_car_bot.cli")


def _base_dir() -> Path:
    """Return the project root (parent of src/) based on this file's location."""
    return Path(__file__).resolve().parent.parent.parent


@click.group()
def cli():
    """Yad2 Car Finder Bot — debug-first car monitoring pipeline."""


@cli.command("validate-config")
@click.option("--base-dir", "base_dir_str", default=None, help="Project root directory.")
def validate_config(base_dir_str):
    """Validate config files and metadata. Exits non-zero on errors."""
    from yad2_car_bot.config import load_config
    from yad2_car_bot.validators import validate_config as _validate

    base = Path(base_dir_str) if base_dir_str else _base_dir()
    cfg = load_config(base)
    issues = _validate(cfg)

    if not issues:
        click.secho("✓ Config is valid.", fg="green")
        return

    has_error = False
    for sev, msg in issues:
        color = "red" if sev == "ERROR" else "yellow"
        click.secho(f"[{sev}] {msg}", fg=color)
        if sev == "ERROR":
            has_error = True

    if has_error:
        sys.exit(1)


@cli.command("build-url")
@click.option("--base-dir", "base_dir_str", default=None)
def build_url(base_dir_str):
    """Print the Yad2 search URL derived from the active search profile."""
    from yad2_car_bot.config import load_config
    from yad2_car_bot.url_builder import build_search_url

    base = Path(base_dir_str) if base_dir_str else _base_dir()
    cfg = load_config(base)
    url = build_search_url(cfg.search_profile)
    click.echo(url)


@cli.command("parse-search-sample")
@click.argument("html_file", type=click.Path(exists=True))
def parse_search_sample(html_file):
    """Parse a search result HTML file and print extracted listings as JSON."""
    from yad2_car_bot.parsers.search_parser import parse_search_page

    html = Path(html_file).read_text(encoding="utf-8")
    listings = parse_search_page(html)

    if not listings:
        click.secho("No listings found in the file.", fg="yellow")
        return

    for card in listings:
        click.echo(card.model_dump_json(indent=2))


@cli.command("parse-detail-sample")
@click.argument("html_file", type=click.Path(exists=True))
@click.option("--description-file", default=None, help="Optional separate description/location HTML file.")
def parse_detail_sample(html_file, description_file):
    """Parse a detail page HTML sample and print extracted data as JSON."""
    from yad2_car_bot.parsers.detail_parser import (
        parse_technical_section,
        parse_description_location,
        merge_detail,
    )

    html = Path(html_file).read_text(encoding="utf-8")
    technical = parse_technical_section(html)
    click.secho("Technical fields:", bold=True)
    click.echo(json.dumps(technical, ensure_ascii=False, indent=2))

    if description_file:
        desc_html = Path(description_file).read_text(encoding="utf-8")
        desc = parse_description_location(desc_html)
        detail = merge_detail(technical, desc)
        click.secho("\nMerged DetailListing:", bold=True)
        click.echo(detail.model_dump_json(indent=2))


@cli.command("score-sample")
@click.option("--base-dir", "base_dir_str", default=None)
def score_sample(base_dir_str):
    """Score a synthetic sample listing and print the breakdown."""
    from yad2_car_bot.config import load_config
    from yad2_car_bot.parsers.search_parser import parse_search_page
    from yad2_car_bot.parsers.detail_parser import parse_description_location, parse_technical_section, merge_detail
    from yad2_car_bot.scoring.keyword_matcher import match_keywords
    from yad2_car_bot.scoring.scoring_engine import score_listing

    base = Path(base_dir_str) if base_dir_str else _base_dir()
    cfg = load_config(base)

    # Parse the bundled samples
    search_html = (base / "samples" / "search_result_card.html").read_text(encoding="utf-8")
    tech_html = (base / "samples" / "listing_detail_technical_section.html").read_text(encoding="utf-8")
    desc_html = (base / "samples" / "listing_detail_description_location_phone_image.html").read_text(encoding="utf-8")

    cards = parse_search_page(search_html)
    if not cards:
        click.secho("Could not parse search sample.", fg="red")
        sys.exit(1)

    card = cards[0]
    technical = parse_technical_section(tech_html)
    desc = parse_description_location(desc_html)
    detail = merge_detail(technical, desc)

    matches = match_keywords(detail.description, card.tags, cfg.keyword_rules)
    scored = score_listing(card, detail, matches, cfg.scoring_rules)

    click.secho(f"Score: {scored.score}/100  →  {scored.decision.upper()}", bold=True)
    click.echo("\nBreakdown:")
    for factor, points in scored.score_breakdown.factors.items():
        click.echo(f"  {factor:35s} {points:+d}")
    click.echo(f"\nPositives: {scored.positive_reasons}")
    click.echo(f"Flags:     {scored.flags}")


@cli.command("render-telegram-sample")
@click.option("--base-dir", "base_dir_str", default=None)
def render_telegram_sample(base_dir_str):
    """Render a Telegram message from the sample listings and print it."""
    from yad2_car_bot.config import load_config
    from yad2_car_bot.parsers.search_parser import parse_search_page
    from yad2_car_bot.parsers.detail_parser import parse_description_location, parse_technical_section, merge_detail
    from yad2_car_bot.scoring.keyword_matcher import match_keywords
    from yad2_car_bot.scoring.scoring_engine import score_listing
    from yad2_car_bot.telegram.renderer import render_message

    base = Path(base_dir_str) if base_dir_str else _base_dir()
    cfg = load_config(base)

    search_html = (base / "samples" / "search_result_card.html").read_text(encoding="utf-8")
    tech_html = (base / "samples" / "listing_detail_technical_section.html").read_text(encoding="utf-8")
    desc_html = (base / "samples" / "listing_detail_description_location_phone_image.html").read_text(encoding="utf-8")

    cards = parse_search_page(search_html)
    if not cards:
        click.secho("Could not parse search sample.", fg="red")
        sys.exit(1)

    card = cards[0]
    technical = parse_technical_section(tech_html)
    desc = parse_description_location(desc_html)
    detail = merge_detail(technical, desc)
    matches = match_keywords(detail.description, card.tags, cfg.keyword_rules)
    scored = score_listing(card, detail, matches, cfg.scoring_rules)
    payload = render_message(scored, card, detail, cfg.telegram_template)

    click.secho("=== Telegram Message ===", bold=True)
    click.echo(payload.text)
    if payload.image_url:
        click.secho(f"\nImage: {payload.image_url}", fg="cyan")
    click.secho(f"\nMessage length: {len(payload.text)} chars", fg="blue")


@cli.command("run-once")
@click.option("--base-dir", "base_dir_str", default=None)
@click.option("--dry-run/--send", default=True, help="Default: dry-run (no Telegram).")
@click.option("--db", default=None, help="SQLite database path.")
@click.option(
    "--browser/--http",
    "use_browser",
    default=False,
    help="Use a visible, user-assisted Playwright browser instead of HTTP requests.",
)
def run_once(base_dir_str, dry_run, db, use_browser):
    """Run the full pipeline once.

    By default operates in dry-run mode — no Telegram messages are sent.
    Pass --send to actually send notifications.
    """
    from yad2_car_bot.config import load_config
    from yad2_car_bot.validators import assert_valid_config
    from yad2_car_bot.url_builder import build_search_url
    from yad2_car_bot.http_client import Yad2Client
    from yad2_car_bot.parsers.search_parser import parse_search_page, parse_next_data
    from yad2_car_bot.models import DetailListing
    from yad2_car_bot.scoring.keyword_matcher import match_keywords
    from yad2_car_bot.scoring.scoring_engine import score_listing
    from yad2_car_bot.telegram.renderer import render_message
    from yad2_car_bot.telegram.notifier import send_notification
    from yad2_car_bot.storage.sqlite_store import SQLiteStore

    base = Path(base_dir_str) if base_dir_str else _base_dir()
    cfg = load_config(base)
    assert_valid_config(cfg)

    db_path = db or str(base / "data" / "yad2_car_monitor.sqlite")
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    debug_mode = os.getenv("DEBUG_SNAPSHOTS", "false").lower() == "true"

    if not dry_run and (not token or not chat_id):
        click.secho("ERROR: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set for --send mode.", fg="red")
        sys.exit(1)

    if use_browser:
        from yad2_car_bot.browser_client import BrowserYad2Client

        client = BrowserYad2Client()
    else:
        client = Yad2Client(debug_mode=debug_mode)
    search_url = build_search_url(cfg.search_profile)

    click.echo(f"Fetching: {search_url}")
    if use_browser:
        click.secho(
            "[BROWSER] Verification, if requested, must be completed manually.",
            fg="cyan",
        )
    if dry_run:
        click.secho("[DRY RUN] No Telegram messages will be sent.", fg="yellow")

    with SQLiteStore(db_path) as store:
        run_id = store.start_run(cfg.search_profile.profile_name, search_url)

        try:
            html = client.get_page(search_url)
        except RuntimeError as exc:
            click.secho(f"Failed to fetch search page: {exc}", fg="red")
            sys.exit(1)

        cards = parse_search_page(html)
        enrichment_map = parse_next_data(html)
        click.echo(f"Found {len(cards)} listing(s).")

        new_count = 0
        notify_count = 0

        for card in cards:
            is_new = not store.is_known_listing(
                card.listing_id, card.listing_url, card.raw_card_html_hash
            )

            # Build DetailListing from __NEXT_DATA__ JSON (no HTTP fetch needed)
            enrichment = enrichment_map.get(card.listing_id, {})
            detail = DetailListing(
                engine_type=enrichment.get("engine_type"),
                engine_cc=enrichment.get("engine_cc"),
                location=enrichment.get("location"),
                current_ownership=enrichment.get("current_ownership"),
                images=enrichment.get("images", []),
                parsed_at=datetime.now(tz=timezone.utc),
                parser_provenance="search_json_enrichment",
            )

            matches = match_keywords(
                detail.description, card.tags, cfg.keyword_rules
            )
            scored = score_listing(card, detail, matches, cfg.scoring_rules)

            store.save_listing(card, detail, matches, scored)

            if is_new:
                new_count += 1

            if scored.decision == "notify" and store.should_notify(
                card.listing_id, scored.score, card.price
            ):
                payload = render_message(scored, card, detail, cfg.telegram_template)
                ok = send_notification(payload, token, chat_id, dry_run=dry_run)
                if ok:
                    store.record_notification(
                        card.listing_id, scored.score, card.price, dry_run=dry_run
                    )
                    notify_count += 1
                    click.echo(
                        f"  → {'[DRY RUN] ' if dry_run else ''}Notified: {card.listing_id} score={scored.score}"
                    )
            else:
                click.echo(
                    f"  skip: {card.listing_id} score={scored.score} decision={scored.decision}"
                )

        store.finish_run(run_id, len(cards), new_count)
        click.echo(f"\nDone. New={new_count}, Notified={notify_count}.")


def main():
    cli()


if __name__ == "__main__":
    main()
