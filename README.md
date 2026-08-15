# Yad2 Car Finder Bot

A debug-first, file-driven Yad2 car listing monitoring pipeline with Telegram notifications.

Current operator notes (how to change the search and how to run collection) are in [PROJECT_STATUS.md](PROJECT_STATUS.md).

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

Use a virtualenv so the CLI has BeautifulSoup and the rest of the Python packages
(plain `python3 -m pip install` often fails on macOS).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .   # installs the package in editable mode so CLI works
```

After that, run every CLI command from the activated venv (no `PYTHONPATH` needed):

```bash
source .venv/bin/activate
python -m yad2_car_bot.cli collect --browser --out debug_snapshots/search.html
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

### 4. (Optional) Set up the Node.js browser collector

`--browser` mode shells out to a small Node.js/Playwright (JS) script instead of
using Playwright from Python. It is only needed if you plan to use `--browser`.

```bash
# Requires Node.js (LTS) installed and on PATH
cd js_browser
npm install
npx playwright install chromium
cd ..
```

If your `node` binary isn't on PATH, set `NODE_EXECUTABLE` in `.env` to its full path.

To reuse a Chrome window that is already open, Playwright can only attach if that
Chrome was started with a remote-debugging port. You cannot attach to a normal
Chrome that is already running without that flag.

Quit Chrome completely, then start it once like this (macOS):

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/chrome-yad2-debug"
```

Use a dedicated `--user-data-dir` so this does not fight with your everyday Chrome
profile. Open Yad2 in that window, complete any verification yourself, then:

```bash
export PLAYWRIGHT_CDP_URL=http://127.0.0.1:9222
export PLAYWRIGHT_REUSE_TAB=true
python -m yad2_car_bot.cli collect --browser --out debug_snapshots/search.html
```

`PLAYWRIGHT_REUSE_TAB=true` snapshots an existing tab **only if that tab already
shows listing cards**. A Yad2 homepage is not enough; in that case a new tab is
opened with the search URL. Leave `PLAYWRIGHT_REUSE_TAB` unset to always open a
new search tab in the attached Chrome.

---

## CLI Commands

All commands are **dry-run by default** — no Telegram messages are sent unless `--send` is passed.

```bash
# Validate config files and metadata
python -m yad2_car_bot.cli validate-config

# Print the search URL that would be used
python -m yad2_car_bot.cli build-url

# Fetch the live Yad2 search page and save the HTML (HTTP client; no scoring/Telegram)
python -m yad2_car_bot.cli collect --http --out debug_snapshots/search.html

# Same collection using the attached/visible Chrome (starts as soon as listing cards appear)
python -m yad2_car_bot.cli collect --browser --out debug_snapshots/search.html

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
python -m yad2_car_bot.cli run-once --browser --dry-run
```

The browser mode is deliberately user-assisted: it does not solve verification,
forge browser tokens, or run headlessly. Under the hood, `--browser` runs
`js_browser/fetch_page.js` (Node.js/Playwright JS), opens or attaches to Chrome,
waits until listing cards appear, then returns the page HTML to the Python
pipeline. By default it uses an installed Google Chrome browser. Set
`PLAYWRIGHT_BROWSER_CHANNEL` only if you need a different Playwright-supported
installed browser channel, and see [Setup step 4](#4-optional-set-up-the-nodejs-browser-collector)
for the one-time Node.js setup this mode requires.

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
js_browser/           Node.js/Playwright (JS) user-assisted browser collector
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
