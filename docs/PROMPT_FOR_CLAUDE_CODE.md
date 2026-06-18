# Prompt for Claude Code / Codex - Yad2 Telegram Car Monitoring Bot

You are implementing a Python project from a planning package. Do not invent missing requirements. Use the attached files as the source of truth.

## Goal

Build a debug-first, file-driven Yad2 car listing monitoring pipeline with Telegram notifications.

The pipeline has these phases:

1. Metadata validation
2. Search URL builder
3. Search page collector
4. Search card parser
5. Detail page collector
6. Detail parser
7. Keyword matching
8. Scoring
9. Telegram notifier
10. SQLite persistence and duplicate prevention
11. Tests based on the attached HTML samples

## Critical constraint

Do not hard-code the business rules. Load them from:

- `configs/search_profile_primary.json`
- `data/yad2_filter_metadata.json`
- `configs/listing_keyword_rules.json`
- `configs/scoring_rules.json`
- `docs/telegram_message_template.md`

Use the HTML samples under `samples/` as parser fixtures.

## Compliance and behavior gate

This project should be implemented as a local/debug-first tool. Add a visible compliance warning in the README and config because Yad2 may restrict automated crawling. Do not implement bypassing anti-bot protections, private cookies, captchas, authentication, or blocked endpoints. Use only public pages and polite rate-limited requests.

## Required project tree

Create:

```text
yad2_car_bot/
├── README.md
├── requirements.txt
├── .env.example
├── configs/
│   ├── search_profile_primary.json
│   ├── listing_keyword_rules.json
│   └── scoring_rules.json
├── data/
│   ├── yad2_filter_metadata.json
│   ├── yad2_car_metadata.json
│   ├── yad2_car_models_flat.json
│   ├── yad2_car_models.csv
│   └── yad2_car_metadata.sqlite
├── samples/
│   ├── search_result_card.html
│   ├── listing_detail_technical_section.html
│   └── listing_detail_description_location_phone_image.html
├── src/
│   └── yad2_car_bot/
│       ├── __init__.py
│       ├── config.py
│       ├── models.py
│       ├── validators.py
│       ├── url_builder.py
│       ├── http_client.py
│       ├── parsers/
│       │   ├── __init__.py
│       │   ├── search_parser.py
│       │   ├── detail_parser.py
│       │   └── html_utils.py
│       ├── scoring/
│       │   ├── __init__.py
│       │   ├── keyword_matcher.py
│       │   └── scoring_engine.py
│       ├── storage/
│       │   ├── __init__.py
│       │   └── sqlite_store.py
│       ├── telegram/
│       │   ├── __init__.py
│       │   ├── renderer.py
│       │   └── notifier.py
│       ├── debug/
│       │   ├── __init__.py
│       │   └── snapshots.py
│       └── cli.py
└── tests/
    ├── test_url_builder.py
    ├── test_search_parser.py
    ├── test_detail_parser.py
    ├── test_keyword_matcher.py
    ├── test_scoring_engine.py
    ├── test_telegram_renderer.py
    └── test_validators.py
```

## Search profile

The active search profile is stored in `configs/search_profile_primary.json`.

Important expected params:

- `manufacturer=19,36,21,27`
- `year=2016-2026`
- `price=28000-55000`
- `km=5000-150000`
- `engineval=1250-3200`
- `hand=0-2`
- `engineType=1101`
- `gearBox=102`
- `priceOnly=1`
- `imgOnly=1`
- `ownerID=1`

Do not add `model` unless the profile explicitly contains model IDs.
Do not add `yad2_source`.

## Metadata

Use `data/yad2_filter_metadata.json`.

Manufacturer IDs:

- Toyota = 19
- Hyundai = 21
- Mazda = 27
- Suzuki = 36
- Nissan = 32

Validation:
- Fail startup if active manufacturers have duplicate IDs.
- Fail startup if an active manufacturer has no ID.
- Warn for `manual_verify_once`.

Filter IDs:
- `engineType 1101 = בנזין`
- `engineType 2101 = היברידי-בנזין`
- `gearBox 102 = אוטומט`
- `gearBox 101 = ידני`
- `ownerID 1 = פרטי`

## Phase 1 - Search card parser

Use `samples/search_result_card.html` as the golden fixture.

Preferred root selector:

```css
a[data-nagish="private-item-link"][data-listing-type]
```

Extract:

- `listing_id`: root `data-testid`, fallback parse from href `/item/<id>` or `item/<id>`
- `listing_url_relative`: root `href`
- `listing_url`: absolute canonical URL
- `listing_type`: root `data-listing-type`
- `title`
- `subtitle`
- `year`
- `hand`
- `price`
- `image_url`
- `tags`
- `raw_card_html_hash`
- `parsed_at`

Selectors:
- price: `span[data-testid="price"]`
- image: `img[data-testid="image"]`
- tags: all `span[data-testid="listing-item-flag"]`

Do not rely only on hashed CSS classes.

Canonicalize listing URL:
- Join relative path to `https://www.yad2.co.il/vehicles/cars/` or site root correctly.
- Strip tracking parameters:
  - `opened-from`
  - `component-type`
  - `spot`
  - `location`
  - `pagination`
  - `yad2_source`

## Phase 2 - Detail page parser

Use `samples/listing_detail_technical_section.html` as the technical golden fixture.

Technical section selector:

```css
section[data-testid="additional-info"]
```

Parse label/value pairs:

```css
dd[data-testid$="-label"]
dt[data-testid$="-value"]
```

Pair each label with the next value in the same `dl`.

Map Hebrew labels:

- `קילומטראז׳` -> `km`
- `צבע` -> `color`
- `בעלות נוכחית` -> `current_ownership`
- `טסט עד` -> `test_valid_until`
- `תיבת הילוכים` -> `gearbox`
- `תאריך עליה לכביש` -> `date_on_road`
- `סוג מנוע` -> `engine_type`
- `מרכב` -> `body_type`
- `מושבים` -> `seats`
- `כוח סוס` -> `horse_power`
- `נפח מנוע` -> `engine_cc`
- `צריכת דלק משולבת` -> `combined_fuel_consumption`

Use `samples/listing_detail_description_location_phone_image.html` for these selectors:

- location: `span[data-testid="location"]`
- description: `p[data-testid="vehicle-description"]`
- phone availability only: `div[data-testid="phone-number-link"] a[href^="tel:"]`
- detail image: `div[data-testid="image-box"] img[data-testid="image"]`

Do not store raw phone numbers by default. Store only `phone_available: true/false`.

## Normalized dataclasses

Use typed dataclasses or Pydantic models.

Create:

- `SearchProfile`
- `ManufacturerMetadata`
- `SearchCardListing`
- `DetailListing`
- `ListingImage`
- `KeywordMatch`
- `ScoreBreakdown`
- `ScoredListing`
- `TelegramPayload`

Every parser output must include:
- `source_flags`
- `parser_provenance`
- `parsed_at`

## Keyword rules

Load from `configs/listing_keyword_rules.json`.

Categories:
- `hard_reject`
- `soft_flags`
- `positive`

Normalize Hebrew text:
- Strip punctuation
- Collapse whitespace
- Preserve phrase matching
- Match both description and tags where relevant
- Record matched category and exact term

## Scoring

Load from `configs/scoring_rules.json`.

Start with `base_score`.

Hard rejects:
- taxi
- rental
- accident_or_chassis
- severe_mechanical

If any hard reject is triggered:
- `score = hard_reject_score`
- `decision = rejected`
- no Telegram notification

Notify only if:
- `score >= minimum_score_to_notify`
- no hard reject

Output:
- `score`
- `score_breakdown`
- `positive_reasons`
- `flags`
- `decision`

## Telegram

Load template from `docs/telegram_message_template.md`.

If listing has images:
- Send first image with caption.
- Optionally send media group for additional images.

If listing has no images:
- Send plain text.

Caption must be safe for Telegram limits. If too long:
1. Trim extra flags
2. Trim extra positives
3. Trim subtitle
4. If still too long, send photo then separate text message

Do not include phone number.

Environment variables:

```text
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

## HTTP client

Implement:
- timeout
- retries
- exponential backoff with jitter
- honor `Retry-After` on 429/503
- low concurrency
- user-agent config
- save raw HTML snapshots in debug mode

Do not bypass anti-bot protections.
Do not use private cookies/tokens.
Do not solve captchas.

## SQLite storage

Create tables:

- `search_runs`
- `listings`
- `listing_details`
- `listing_images`
- `keyword_hits`
- `scores`
- `notifications`
- `parser_snapshots`

Dedupe by:
- `listing_id`
- canonical URL
- content hash

Do not notify twice for the same listing unless:
- it was never notified before, or
- score changed materially, or
- price dropped materially

## CLI

Implement commands:

```bash
python -m yad2_car_bot.cli validate-config
python -m yad2_car_bot.cli build-url --profile configs/search_profile_primary.json
python -m yad2_car_bot.cli parse-search-sample samples/search_result_card.html
python -m yad2_car_bot.cli parse-detail-sample samples/listing_detail_technical_section.html
python -m yad2_car_bot.cli score-sample
python -m yad2_car_bot.cli render-telegram-sample
python -m yad2_car_bot.cli run-once --dry-run
```

Default mode must be dry-run. Telegram sending only if explicitly enabled.

## Tests

Build tests from the attached samples.

Tests must cover:
- search URL generation
- metadata validation
- search card parsing
- technical detail parsing
- description/location/phone/image parsing
- Hebrew keyword matching
- scoring breakdown
- Telegram rendering
- duplicate prevention
- URL canonicalization

Acceptance criteria:
- Parser extracts listing ID, title, price, year, hand, image, tags from the search card sample.
- Parser extracts km, color, ownership, test date, gearbox, on-road date, engine type, body type, seats, horsepower, engine CC, fuel consumption from the technical sample.
- Scoring returns auditable breakdown.
- Telegram payload includes image when available.
- Phone number is not stored or sent.
- Tests pass.
- README documents setup and compliance guardrails.
