# Yad2 Car Finder Bot

A debug-first, file-driven Yad2 car listing monitoring pipeline with Telegram notifications.

---

## COMPLIANCE WARNING

> **This tool sends HTTP requests to yad2.co.il.**
> Yad2 may restrict or prohibit automated crawling in their Terms of Service.
> Use this tool **only for personal, non-commercial, low-frequency monitoring** on your own behalf.
> Do **not** use this tool to scrape at scale, bypass rate limits, or circumvent any access controls.
> The tool uses only public pages and polite, rate-limited requests.
> The authors accept no responsibility for violations of Yad2's terms.

---

## Features

- Builds Yad2 search URLs from a structured profile (no hard-coded rules)
- Parses search result cards and detail pages using stable `data-testid` selectors
- Matches Hebrew keywords (hard reject / soft flags / positive)
- Scores listings with an auditable breakdown
- Sends Telegram notifications with images
- Stores results in SQLite with deduplication
- Debug mode: saves raw HTML snapshots

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
pip install -e .   # installs the package in editable mode so CLI works
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
```

### 3. Verify configuration

```bash
python -m yad2_car_bot.cli validate-config
```

---

## CLI Commands

All commands are **dry-run by default** — no Telegram messages are sent unless `--send` is passed.

```bash
# Validate config files and metadata
python -m yad2_car_bot.cli validate-config

# Print the search URL that would be used
python -m yad2_car_bot.cli build-url

# Parse a search result HTML sample
python -m yad2_car_bot.cli parse-search-sample samples/search_result_card.html

# Parse a detail page HTML sample (technical section)
python -m yad2_car_bot.cli parse-detail-sample samples/listing_detail_technical_section.html

# Score a synthetic sample listing
python -m yad2_car_bot.cli score-sample

# Render a Telegram message from a sample listing
python -m yad2_car_bot.cli render-telegram-sample

# Run the full pipeline once (dry-run by default)
python -m yad2_car_bot.cli run-once --dry-run

# Run and actually send Telegram notifications
python -m yad2_car_bot.cli run-once --send

# Use a visible Chrome window when the plain HTTP client receives browser verification.
# Complete any verification yourself, wait for listings, then confirm in the terminal.
python -m yad2_car_bot.cli run-once --browser --dry-run
```

The browser mode is deliberately user-assisted: it does not solve verification,
forge browser tokens, or run headlessly. By default it uses an installed Google
Chrome browser. Set `PLAYWRIGHT_BROWSER_CHANNEL` only if you need a different
Playwright-supported installed browser channel.

---

## Configuration files

| File | Purpose |
|---|---|
| `configs/search_profile_primary.json` | Manufacturers, price range, filters |
| `configs/listing_keyword_rules.json` | Hard reject / soft flags / positive keywords (Hebrew) |
| `configs/scoring_rules.json` | Score factors and thresholds |
| `data/yad2_filter_metadata.json` | Manufacturer ID validation metadata |
| `docs/telegram_message_template.md` | Telegram message template |

---

## Project structure

```
src/yad2_car_bot/     Core Python package
configs/              Search profile and rule configs
data/                 Metadata and SQLite database
samples/              HTML fixtures for testing and debugging
tests/                Pytest test suite
docs/                 Planning and template files
```

---

## Tests

```bash
pytest tests/ -v
```

---

## Privacy

- Raw phone numbers are **never stored or sent**.
- Only `phone_available: true/false` is recorded.
