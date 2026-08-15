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

Leave `"models": []` under each brand unused for URL filtering. Live searches are
driven by ``search_groups`` (below). The ``cars`` map is still used for validation
and as the fallback when ``search_groups`` is empty.

### Search groups (2 Yad2 searches)

Yad2 allows **at most 4 manufacturers** and **at most 4 models total** in one
search URL. Configure two (or more) groups so one `collect` / `run-once` covers
more brands/models:

```json
"search_groups": [
  {
    "manufacturers": [19, 21, 27, 36],
    "models": [10247, 10226, 10238, 10225]
  },
  {
    "manufacturers": [19, 21, 27, 36],
    "models": [11228, 11150, 10236, 10230]
  }
]
```

Manufacturer IDs: Toyota 19, Hyundai 21, Mazda 27, Suzuki 36, Nissan 32.
Model IDs: see [data/yad2_car_models.csv](data/yad2_car_models.csv)
(e.g. Yaris `10247`, Corolla `10226`, RAV4 `10238`, C-HR `10225`).

- Empty `"search_groups": []` → one URL from ``cars`` with **no** `model=` filter.
- Non-empty → one Yad2 URL per group; `collect` / `run-once --browser` runs them
  in sequence (short pause between groups).
- Per group: ≤4 manufacturers, ≤4 models (models are optional; omit/`[]` means
  all models under those manufacturers).
- `build-url` prints every URL (one per line).
- `validate-config` enforces the caps and unknown IDs.

Also update `expected_yad2_query_params.manufacturer` when you change the
fallback ``cars`` list.

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

`build-url` prints every Yad2 URL that `--browser` will open (one line per
`search_groups` entry). Open them in the debug Chrome once if you want to confirm
filters by eye.

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

Success looks like: `Found N listing card(s)` then `Group 1: saved ...` and
`recognized listing cards`. With two search groups you also get `search-2.html`.

Inspect without hitting the network again:

```bash
python -m yad2_car_bot.cli parse-search-sample debug_snapshots/search.html
python -m yad2_car_bot.cli parse-search-sample debug_snapshots/search-2.html
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

### 3c. Watch every 15 minutes (new ads only)

Keeps Chrome attached, refreshes all search groups on an interval, compares to
SQLite from the previous cycle, and Telegram-notifies **only brand-new** listings.

```bash
# First cycle = baseline (store only). Then every 15 min → new ads only.
python -m yad2_car_bot.cli watch --browser --send

# Dry-run (log would-be notifications, still writes SQLite):
python -m yad2_car_bot.cli watch --browser --dry-run

# Custom interval (minutes):
python -m yad2_car_bot.cli watch --browser --send --interval-minutes 15
```

Stop with Ctrl+C. Use `--no-seed-first` if you want the first cycle to notify
immediately for ads not already in the DB.

---

## What was verified live

- `collect --http` → Radware page, 0 listing cards (now treated as failure)
- Attaching to Chrome on `127.0.0.1:9222` → navigates to `/vehicles/cars?...` and finds listing cards (34 on 2026-08-15)
- Waiting for a manual Enter key was removed; it often did nothing because stdin was not reaching the Node process

---

## Compliance

Personal, low-frequency use of public pages only. The bot does not solve Radware/captchas, forge tokens, or run headless verification bypass. You complete any browser check in the debug Chrome yourself.
