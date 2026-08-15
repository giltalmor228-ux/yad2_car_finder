# Project status — Yad2 Car Finder Bot

Last updated: 2026-08-15

## Where things stand

The Python pipeline (URL builder, parsers, keyword matching, scoring, SQLite, Telegram) is in place. Live Yad2 collection **does not work over plain HTTP**: Yad2 returns a Radware verification page, not listing HTML.

Collection works by attaching Playwright (JS) to a Chrome window you start yourself with remote debugging. On 2026-08-15 this successfully found **34 car listing cards** on the live search page.

There is **no “press Enter” step**. After attach, the collector navigates the existing Chrome tab to the search URL and snapshots as soon as listing cards appear.

Use the project `.venv` for all CLI commands. System `python3` does not have the package dependencies (`bs4`, etc.).

```bash
source .venv/bin/activate
```

---

## One-time setup (already done on this machine)

1. Python venv: `.venv` with `pip install -r requirements.txt` and `pip install -e .`
2. Node.js + Playwright JS: `cd js_browser && npm install`
3. Copy `.env.example` to `.env` and fill Telegram credentials only if you want `--send`

---

## How to configure a new search

The bot does **not** take search filters on the command line. Edit the profile file, then validate.

**File:** [configs/search_profile_primary.json](configs/search_profile_primary.json)

That is the only profile `collect` / `run-once` / `build-url` load today.

### Manufacturers

Under `cars`, each key is a display name. The ID must match [data/yad2_filter_metadata.json](data/yad2_filter_metadata.json):

| ID | Brand |
|---:|---|
| 19 | Toyota |
| 21 | Hyundai |
| 27 | Mazda |
| 36 | Suzuki |
| 32 | Nissan |

Example: add Nissan and drop Suzuki:

```json
"cars": {
  "Toyota": { "manufacturer_id": 19, "models": [] },
  "Hyundai": { "manufacturer_id": 21, "models": [] },
  "Mazda": { "manufacturer_id": 27, "models": [] },
  "Nissan": { "manufacturer_id": 32, "models": [] }
}
```

Leave `"models": []` to search **all models** for that manufacturer. Do not add a `model=` query param unless you later extend the profile with real Yad2 model IDs.

Also update `expected_yad2_query_params.manufacturer` to the same ID list (comma-separated, same order), or `validate-config` may warn.

### Numeric filters

Edit `filters`:

| Field | Yad2 URL param | Meaning |
|---|---|---|
| `year.min` / `year.max` | `year` | Model years |
| `price.min` / `price.max` | `price` | ILS |
| `km.min` / `km.max` | `km` | Mileage |
| `engine_cc.min` / `engine_cc.max` | `engineval` | Engine size |
| `hand.min` / `hand.max` | `hand` | Previous owners (`0-2` = up to 2nd hand) |

### Engine, gearbox, owner

IDs from `data/yad2_filter_metadata.json`:

- `engine_types`: `1101` = petrol (בנזין), `2101` = hybrid-petrol
- `gearbox`: `102` = automatic, `101` = manual
- `owner_type`: `1` = private (פרטי)

`price_only` / `image_only` map to `priceOnly=1` and `imgOnly=1`.

### Keywords and scoring (optional)

These are not the search URL; they decide which listings to keep/notify:

- [configs/listing_keyword_rules.json](configs/listing_keyword_rules.json) — Hebrew hard rejects, soft flags, positives
- [configs/scoring_rules.json](configs/scoring_rules.json) — score factors and notify threshold

### Check the new search

```bash
source .venv/bin/activate
python -m yad2_car_bot.cli validate-config
python -m yad2_car_bot.cli build-url
```

`build-url` prints the Yad2 URL that `--browser` will open. Open it in the debug Chrome once if you want to confirm filters by eye.

---

## How to trigger a run

Plain HTTP (`--http`) hits Radware and is not usable for live data. Always use **`--browser`** and an already-open debug Chrome.

### 1. Start debug Chrome (once per session)

Quit regular Chrome if it conflicts, then:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/chrome-yad2-debug"
```

Leave this window open. Complete any Yad2 verification in that window if asked (homepage is enough). You do **not** need to open the car search yourself; the collector navigates the current tab.

### 2. Point the bot at that Chrome

In the project terminal:

```bash
source .venv/bin/activate
export PLAYWRIGHT_CDP_URL=http://127.0.0.1:9222
```

Do not set `PLAYWRIGHT_REUSE_TAB` unless the **car search** tab already shows listing cards. A Yad2 homepage is not a search page.

### 3a. Collect HTML only (no scoring, no DB, no Telegram)

```bash
python -m yad2_car_bot.cli collect --browser --out debug_snapshots/search.html
```

Success looks like: `Found N listing card(s)` then `Saved ...` and `Recognized listing cards: N`.

Inspect without hitting the network again:

```bash
python -m yad2_car_bot.cli parse-search-sample debug_snapshots/search.html
```

### 3b. Full bot pipeline (parse, score, SQLite)

Dry-run (recommended first; no Telegram):

```bash
python -m yad2_car_bot.cli run-once --browser --dry-run
```

Send Telegram (needs `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`):

```bash
python -m yad2_car_bot.cli run-once --browser --send
```

Listings are stored in `data/yad2_car_monitor.sqlite`. The bot will not notify twice for the same listing unless the score or price changes materially.

---

## What was verified live

- `collect --http` → Radware page, 0 listing cards (now treated as failure)
- Attaching to Chrome on `127.0.0.1:9222` → navigates to `/vehicles/cars?...` and finds listing cards (34 on 2026-08-15)
- Waiting for a manual Enter key was removed; it often did nothing because stdin was not reaching the Node process

---

## Compliance

Personal, low-frequency use of public pages only. The bot does not solve Radware/captchas, forge tokens, or run headless verification bypass. You complete any browser check in the debug Chrome yourself.
