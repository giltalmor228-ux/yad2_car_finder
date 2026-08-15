from __future__ import annotations

import json
import logging
import os
import sys
import time
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

# Polite pause between search-group fetches in the same Chrome session.
_GROUP_PAUSE_SECONDS = 3
# Default watch interval (minutes) between full search refreshes.
_DEFAULT_WATCH_INTERVAL_MINUTES = 15


def _base_dir() -> Path:
    """Return the project root (parent of src/) based on this file's location."""
    return Path(__file__).resolve().parent.parent.parent


def _make_page_client(use_browser: bool, debug_mode: bool = False):
    """Return the HTTP or user-assisted browser collector."""
    if use_browser:
        from yad2_car_bot.browser_client import BrowserYad2Client

        return BrowserYad2Client()

    from yad2_car_bot.http_client import Yad2Client

    return Yad2Client(debug_mode=debug_mode)


def _out_path_for_group(out_path: str | None, group_index: int) -> Path | None:
    """Return the output path for search group *group_index* (1-based).

    Group 1 keeps the original name; later groups get a ``-2``, ``-3``, … suffix
    before the file extension (e.g. ``search.html`` → ``search-2.html``).
    """
    if not out_path:
        return None
    path = Path(out_path)
    if group_index == 1:
        return path
    return path.with_name(f"{path.stem}-{group_index}{path.suffix}")


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
    """Print Yad2 search URL(s) derived from the active search profile.

    One URL per ``search_groups`` entry (or a single URL when groups are empty).
    """
    from yad2_car_bot.config import load_config
    from yad2_car_bot.url_builder import build_search_urls

    base = Path(base_dir_str) if base_dir_str else _base_dir()
    cfg = load_config(base)
    for url in build_search_urls(cfg.search_profile, cfg.model_catalog):
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


@cli.command("collect")
@click.option("--base-dir", "base_dir_str", default=None)
@click.option(
    "--browser/--http",
    "use_browser",
    default=False,
    help="Use a visible, user-assisted Playwright browser instead of HTTP requests.",
)
@click.option(
    "--out",
    "out_path",
    default=None,
    type=click.Path(dir_okay=False, writable=True),
    help="Where to write the collected HTML. Defaults to debug_snapshots/.",
)
def collect(base_dir_str, use_browser, out_path):
    """Fetch Yad2 search page(s) and save HTML. Does not score, store, or notify.

    When ``search_groups`` is set, fetches one URL per group and writes
    ``search.html``, ``search-2.html``, …
    """
    from yad2_car_bot.browser_client import is_radware_verification_page
    from yad2_car_bot.config import load_config
    from yad2_car_bot.debug.snapshots import save_snapshot
    from yad2_car_bot.parsers.search_parser import parse_search_page
    from yad2_car_bot.url_builder import build_search_urls
    from yad2_car_bot.validators import assert_valid_config

    base = Path(base_dir_str) if base_dir_str else _base_dir()
    cfg = load_config(base)
    assert_valid_config(cfg)

    client = _make_page_client(use_browser)
    search_urls = build_search_urls(cfg.search_profile, cfg.model_catalog)

    if use_browser:
        click.secho(
            "[BROWSER] Collecting as soon as listing cards appear.",
            fg="cyan",
        )
    else:
        click.secho("[HTTP] Collecting with the polite requests client.", fg="cyan")

    for index, search_url in enumerate(search_urls, start=1):
        if index > 1:
            click.echo(f"Waiting {_GROUP_PAUSE_SECONDS}s before next search group...")
            time.sleep(_GROUP_PAUSE_SECONDS)

        click.echo(f"Fetching group {index}/{len(search_urls)}: {search_url}")
        try:
            html = client.get_page(search_url, require_listings=False)
        except RuntimeError as exc:
            click.secho(f"Failed to fetch search page: {exc}", fg="red")
            sys.exit(1)

        if is_radware_verification_page(html):
            click.secho(
                "The response is Yad2's Radware browser-verification page, not listing HTML. "
                "Retry with: python -m yad2_car_bot.cli collect --browser",
                fg="red",
            )
            sys.exit(1)

        group_out = _out_path_for_group(out_path, index)
        if group_out is not None:
            group_out.parent.mkdir(parents=True, exist_ok=True)
            group_out.write_text(html, encoding="utf-8")
            dest = group_out
        else:
            dest = save_snapshot(
                search_url, html, snapshot_dir=str(base / "debug_snapshots")
            )

        listing_count = len(parse_search_page(html))
        click.echo(f"Group {index}: saved {len(html)} chars to {dest}")
        click.echo(f"Group {index}: recognized listing cards: {listing_count}")
        if listing_count == 0:
            click.secho(
                f"Group {index}: no listing cards (empty result or filters too tight).",
                fg="yellow",
            )


def _run_pipeline(
    *,
    cfg,
    client,
    store,
    search_urls: list[str],
    token: str,
    chat_id: str,
    dry_run: bool,
    notify_mode: str = "standard",
) -> dict[str, int]:
    """Fetch all search groups, score, store, and optionally notify.

    ``notify_mode``:
      - ``standard``: notify by score + ``should_notify`` (incl. price/score re-notify)
      - ``new_only``: notify only listings never seen in SQLite before
      - ``none``: store/score only; never send Telegram (baseline / seed run)
    """
    from yad2_car_bot.models import DetailListing
    from yad2_car_bot.parsers.search_parser import (
        _gearbox_from_text,
        parse_next_data,
        parse_search_page,
    )
    from yad2_car_bot.scoring.keyword_matcher import match_keywords
    from yad2_car_bot.scoring.scoring_engine import score_listing
    from yad2_car_bot.telegram.notifier import send_notification
    from yad2_car_bot.telegram.renderer import render_message

    if notify_mode not in {"standard", "new_only", "none"}:
        raise ValueError(f"Unknown notify_mode: {notify_mode}")

    primary_url = search_urls[0]
    run_id = store.start_run(cfg.search_profile.profile_name, primary_url)

    total_cards = 0
    new_count = 0
    notify_count = 0
    seen_listing_ids: set[str] = set()

    for index, search_url in enumerate(search_urls, start=1):
        if index > 1:
            click.echo(f"Waiting {_GROUP_PAUSE_SECONDS}s before next search group...")
            time.sleep(_GROUP_PAUSE_SECONDS)

        click.echo(f"Fetching group {index}/{len(search_urls)}: {search_url}")
        try:
            html = client.get_page(search_url, require_listings=False)
        except RuntimeError as exc:
            click.secho(f"Failed to fetch search page: {exc}", fg="red")
            store.finish_run(run_id, total_cards, new_count)
            raise

        cards = parse_search_page(html)
        enrichment_map = parse_next_data(html)
        click.echo(f"Group {index}: found {len(cards)} listing(s).")
        if not cards:
            click.secho(
                f"Group {index}: no listings; continuing with remaining groups.",
                fg="yellow",
            )
            continue

        for card in cards:
            if card.listing_id in seen_listing_ids:
                click.echo(f"  skip duplicate across groups: {card.listing_id}")
                continue
            seen_listing_ids.add(card.listing_id)
            total_cards += 1

            is_new = not store.is_known_listing(
                card.listing_id, card.listing_url, card.raw_card_html_hash
            )

            enrichment = enrichment_map.get(card.listing_id, {})
            detail = DetailListing(
                engine_type=enrichment.get("engine_type"),
                engine_cc=enrichment.get("engine_cc"),
                location=enrichment.get("location"),
                current_ownership=enrichment.get("current_ownership"),
                gearbox=enrichment.get("gearbox")
                or _gearbox_from_text(card.subtitle)
                or cfg.search_profile.filters.gearbox.name,
                images=enrichment.get("images", []),
                parsed_at=datetime.now(tz=timezone.utc),
                parser_provenance="search_json_enrichment",
            )

            matches = match_keywords(detail.description, card.tags, cfg.keyword_rules)
            scored = score_listing(card, detail, matches, cfg.scoring_rules)

            store.save_listing(card, detail, matches, scored)

            if is_new:
                new_count += 1

            should_send = False
            if notify_mode == "none":
                should_send = False
            elif notify_mode == "new_only":
                should_send = (
                    is_new
                    and scored.decision == "notify"
                    and store.should_notify(card.listing_id, scored.score, card.price)
                )
            else:  # standard
                should_send = scored.decision == "notify" and store.should_notify(
                    card.listing_id, scored.score, card.price
                )

            if should_send:
                payload = render_message(scored, card, detail, cfg.telegram_template)
                ok = send_notification(payload, token, chat_id, dry_run=dry_run)
                if ok:
                    store.record_notification(
                        card.listing_id, scored.score, card.price, dry_run=dry_run
                    )
                    notify_count += 1
                    click.echo(
                        f"  → {'[DRY RUN] ' if dry_run else ''}Notified: "
                        f"{card.listing_id} score={scored.score}"
                    )
            else:
                reason = "seed/baseline" if notify_mode == "none" else scored.decision
                if notify_mode == "new_only" and not is_new:
                    reason = "already seen"
                click.echo(
                    f"  skip: {card.listing_id} score={scored.score} ({reason})"
                )

    store.finish_run(run_id, total_cards, new_count)
    return {
        "cards": total_cards,
        "new": new_count,
        "notified": notify_count,
    }


def _prepare_run(base_dir_str, dry_run, db, use_browser):
    """Load config/client/urls shared by ``run-once`` and ``watch``."""
    from yad2_car_bot.config import load_config
    from yad2_car_bot.url_builder import build_search_urls
    from yad2_car_bot.validators import assert_valid_config

    base = Path(base_dir_str) if base_dir_str else _base_dir()
    cfg = load_config(base)
    assert_valid_config(cfg)

    db_path = db or str(base / "data" / "yad2_car_monitor.sqlite")
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    debug_mode = os.getenv("DEBUG_SNAPSHOTS", "false").lower() == "true"

    if not dry_run and (not token or not chat_id):
        click.secho(
            "ERROR: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set for --send mode.",
            fg="red",
        )
        sys.exit(1)

    client = _make_page_client(use_browser, debug_mode=debug_mode)
    search_urls = build_search_urls(cfg.search_profile, cfg.model_catalog)

    if use_browser:
        click.secho(
            "[BROWSER] Collecting as soon as listing cards appear.",
            fg="cyan",
        )
    if dry_run:
        click.secho("[DRY RUN] No Telegram messages will be sent.", fg="yellow")
    if len(search_urls) > 1:
        click.echo(f"Running {len(search_urls)} search-group searches.")

    return cfg, client, search_urls, db_path, token, chat_id


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
    """Run the full pipeline once (all search groups).

    By default operates in dry-run mode — no Telegram messages are sent.
    Pass --send to actually send notifications.
    """
    from yad2_car_bot.storage.sqlite_store import SQLiteStore

    cfg, client, search_urls, db_path, token, chat_id = _prepare_run(
        base_dir_str, dry_run, db, use_browser
    )

    with SQLiteStore(db_path) as store:
        try:
            stats = _run_pipeline(
                cfg=cfg,
                client=client,
                store=store,
                search_urls=search_urls,
                token=token,
                chat_id=chat_id,
                dry_run=dry_run,
                notify_mode="standard",
            )
        except RuntimeError:
            sys.exit(1)

    click.echo(
        f"\nDone. Cards={stats['cards']}, New={stats['new']}, "
        f"Notified={stats['notified']}."
    )


@cli.command("watch")
@click.option("--base-dir", "base_dir_str", default=None)
@click.option("--dry-run/--send", default=True, help="Default: dry-run (no Telegram).")
@click.option("--db", default=None, help="SQLite database path.")
@click.option(
    "--browser/--http",
    "use_browser",
    default=True,
    help="Default: browser (CDP). Prefer this for live Yad2 pages.",
)
@click.option(
    "--interval-minutes",
    default=_DEFAULT_WATCH_INTERVAL_MINUTES,
    show_default=True,
    type=click.IntRange(1, 24 * 60),
    help="Minutes to wait between refreshes.",
)
@click.option(
    "--seed-first/--no-seed-first",
    default=True,
    help="First cycle only stores listings (no Telegram), then notify new ads only.",
)
def watch(base_dir_str, dry_run, db, use_browser, interval_minutes, seed_first):
    """Refresh every N minutes and Telegram only brand-new listings.

    Compares each cycle to listings already stored in SQLite (from the previous
    cycle / earlier runs). Existing ads are skipped; only new matching ads are
    notified.

    With ``--seed-first`` (default), the first cycle builds a baseline without
    sending messages, waits ``--interval-minutes``, then starts notifying.
    """
    from yad2_car_bot.storage.sqlite_store import SQLiteStore

    cfg, client, search_urls, db_path, token, chat_id = _prepare_run(
        base_dir_str, dry_run, db, use_browser
    )

    interval_seconds = interval_minutes * 60
    click.secho(
        f"[WATCH] Every {interval_minutes} min · notify new listings only"
        f"{' · first cycle = baseline (no Telegram)' if seed_first else ''}. "
        "Ctrl+C to stop.",
        fg="cyan",
    )

    cycle = 0
    with SQLiteStore(db_path) as store:
        while True:
            cycle += 1
            started = datetime.now(tz=timezone.utc)
            if seed_first and cycle == 1:
                notify_mode = "none"
                label = "baseline seed"
            else:
                notify_mode = "new_only"
                label = "new-only refresh"

            click.echo(f"\n=== Watch cycle {cycle} ({label}) @ {started.isoformat()} ===")
            try:
                stats = _run_pipeline(
                    cfg=cfg,
                    client=client,
                    store=store,
                    search_urls=search_urls,
                    token=token,
                    chat_id=chat_id,
                    dry_run=dry_run,
                    notify_mode=notify_mode,
                )
            except KeyboardInterrupt:
                click.secho("\n[WATCH] Stopped.", fg="yellow")
                break
            except RuntimeError:
                click.secho(
                    "Cycle failed; will retry after the interval.",
                    fg="red",
                )
                stats = {"cards": 0, "new": 0, "notified": 0}

            click.echo(
                f"Cycle {cycle} done. Cards={stats['cards']}, New={stats['new']}, "
                f"Notified={stats['notified']}."
            )
            click.echo(f"Sleeping {interval_minutes} minute(s) until next refresh...")
            try:
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                click.secho("\n[WATCH] Stopped.", fg="yellow")
                break


def main():
    cli()


if __name__ == "__main__":
    main()
