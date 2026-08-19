# Repository Summary

## Run Context

- Operating mode: `REPOSITORY_PLUS_BRIEF`
- Project name: Yad2 Car Finder Bot
- Repository root: repository containing `src/yad2_car_bot/`, `js_browser/`, `configs/`, `PROJECT_STATUS.md`
- Project-description source: `PROJECT_STATUS.md` (user-designated authoritative product context; last updated 2026-08-15)
- Existing `.cursor` state: absent (no `.cursor/` directory, no `AGENTS.md`, no project rules or skills). `.claude/settings.local.json` exists and is outside factory ownership.

## Project Purpose

- Users/operators: a single personal operator monitoring used-car listings on Yad2 (yad2.co.il) at low frequency.
- Primary outcome: collect live search pages, parse listing cards and detail fields, score against Hebrew keyword/scoring rules, persist in SQLite, optionally notify via Telegram and/or email, and export a CSV aligned with the notification message.
- In scope: file-driven search profiles, URL building with Yad2 manufacturer/model caps, user-assisted Chrome/Playwright collection, HTML/`__NEXT_DATA__` parsing, scoring, SQLite dedup/notify, CSV export, pytest-backed offline parsing/scoring tests.
- Out of scope: solving Radware/captchas, forging tokens, headless verification bypass, taking search filters on the CLI, commercial-scale crawling, storing or sending raw seller phone numbers.

## Technology and Repository Map

| Area | Relative paths | Responsibility | Evidence class |
| --- | --- | --- | --- |
| Python package | `src/yad2_car_bot/` | CLI pipeline, config, parsers, scoring, storage, notify | VERIFIED_CODE |
| CLI entry | `src/yad2_car_bot/cli.py` | `validate-config`, `build-url`, `collect`, `parse-*-sample`, `score-sample`, `render-telegram-sample`, `run-once`, `watch`, `export-csv` | VERIFIED_CODE |
| Node collector | `js_browser/fetch_page.js`, `js_browser/package.json` | Visible Playwright Chrome attach/launch; wait for cards; scroll-load; write HTML | VERIFIED_CODE |
| Search profile | `configs/search_profile_primary.json` | Only profile loaded by collect/run-once/build-url | VERIFIED_CONFIG |
| Keyword/scoring | `configs/listing_keyword_rules.json`, `configs/scoring_rules.json` | Keep/notify decisions; not URL filters | VERIFIED_CONFIG |
| Metadata catalogs | `data/yad2_filter_metadata.json`, `data/yad2_car_models_flat.json`, `data/yad2_car_models.csv` | Manufacturer/filter ID validation; model IDs | VERIFIED_CONFIG |
| Operator runbook | `PROJECT_STATUS.md` | How to configure search and run `--browser` collection | VERIFIED_DOC / USER_STATED |
| Setup/CLI catalog | `README.md` | Install, env, CLI list, compliance warning | VERIFIED_DOC |
| Notification contract | `docs/telegram_message_template.md` | Caption/text fields; no raw phone | VERIFIED_DOC |
| Env contract | `.env.example` | Notify channels, Telegram/SMTP, Playwright/CDP, snapshots | VERIFIED_CONFIG |
| Tests | `tests/*.py`, `conftest.py`, `tests/conftest.py` | Pytest; samples + mocks; no live Yad2 in CI | VERIFIED_TEST |
| HTML fixtures | `samples/*.html` | Offline parser tests and `*-sample` CLI commands | VERIFIED_CODE |
| SQLite / CSV | `data/yad2_car_monitor.sqlite` (runtime), `data/listings_export.csv` | Persistence and operator export | VERIFIED_CODE |
| Packaging | `pyproject.toml`, `requirements.txt` | Python >=3.10; pydantic, bs4, lxml, requests, tenacity, click, dotenv; pytest in requirements | VERIFIED_CONFIG |

No GitHub Actions / `.github/` workflows were found. No hardware control plane exists. External runtime dependencies are: operator Chrome with optional CDP `127.0.0.1:9222`, Node.js + Playwright JS, Yad2 public pages, Telegram Bot API and/or SMTP when `--send` is used.

## Runtime and Data Flow

1. Operator edits `configs/search_profile_primary.json` (and optionally keyword/scoring JSON). CLI does not accept search filters as arguments.
2. `load_config()` reads the primary profile, filter metadata, keyword rules, scoring rules, telegram template, and `data/yad2_car_models_flat.json`.
3. `validate-config` / `assert_valid_config` enforce manufacturer IDs and `search_groups` caps (≤4 manufacturers and ≤4 models per group).
4. `build_search_urls()` emits one `https://www.yad2.co.il/vehicles/cars?...` URL per search group (or a single cars-fallback URL if `search_groups` is empty).
5. `collect` / `run-once` / `watch` fetch via `Yad2Client` (`--http`) or `BrowserYad2Client` → `js_browser/fetch_page.js` (`--browser`). Live Yad2 currently returns Radware HTML over plain HTTP.
6. `fetch_all_search_pages()` paginates with `page=2..N` (pause 2s, max 30 pages), parses cards from `__NEXT_DATA__` feed buckets (private, commercial, platinum, solo, boost) and DOM fallbacks, and builds an enrichment map.
7. For `run-once`/`watch`, each unique `listing_id` is scored (`match_keywords` + `score_listing`). Detail HTML is fetched when notify mode is not `none` and the listing is new or `notify_mode=standard`.
8. `SQLiteStore` writes listings/details/scores and decides notifications (`should_notify`: first real send, or score change ≥10, or price drop ≥5%).
9. `send_via_channels` uses the same `TelegramPayload` for Telegram and/or email. Dry-run is the CLI default except that `watch` defaults to `--browser`.
10. After each pipeline cycle, `export_listings_csv` refreshes `data/listings_export.csv`.

## Components and Boundaries

| Component | Owns | Depends on | Boundary risk |
| --- | --- | --- | --- |
| CLI (`cli.py`) | Command surface, group pause (3s), detail pause (1s), watch interval (default 15 min), notify_mode (`standard` / `new_only` / `none`) | config, clients, store, notify | Default `--http` on collect/run-once vs live Radware failure |
| URL builder | Query params, group caps, `with_page` | `SearchProfile` | Yad2 4/4 caps; `expected_yad2_query_params` is cars-fallback, not live groups |
| HTTP client | Polite requests, 429/503 Retry-After, debug snapshots | Yad2 public HTTP | Returns verification HTML, not listings |
| Browser client + `fetch_page.js` | CDP attach or launch Chrome; card stabilize + scroll; detail page kinds | Node on PATH, Playwright, operator Chrome | Verification must stay manual; `PLAYWRIGHT_REUSE_TAB` only if listing cards already visible |
| Search parser | Feed JSON + DOM cards, canonical `/vehicles/item/{id}` URLs | `__NEXT_DATA__` shape, `data-nagish` selectors | Markup/JSON drift silently yields 0 cards |
| Detail parser | Technical labels, description/location, `phone_available` only | `data-testid` + `__NEXT_DATA__` | Hebrew label map; must not persist `tel:` numbers |
| Scoring | Decision `notify` \| `skip` \| `rejected` | keyword + scoring JSON | `notify_all_matches: true` currently forces notify for non-rejected |
| SQLite store | Dedup, schema migrate, re-notify thresholds | `data/yad2_car_monitor.sqlite` | Additive migrations only; operator DB is gitignored |
| Notify | Channel parse, credential checks, Telegram photos/albums, SMTP | `.env` (not committed) | `--send` without creds must fail closed |
| CSV export | `CSV_COLUMNS` contract | SQLite | Column/order changes break operator spreadsheet use |

## Critical Contracts

| Contract | Producer | Consumer | Compatibility/invariant | Source |
| --- | --- | --- | --- | --- |
| Search profile JSON + `SearchProfile` models | Operator / `models.py` | `load_config`, URL builder, validators | `search_groups` drives live URLs; empty groups → cars fallback without `model=` | `config.py`, `url_builder.py` |
| Yad2 group caps | `MAX_MANUFACTURERS_PER_GROUP=4`, `MAX_MODELS_PER_GROUP=4` | validators, URL builder | ERROR if exceeded or unknown IDs | `url_builder.py`, `validators.py` |
| Search URL query params | URL builder | Chrome/Yad2 | `year`, `price`, `km`, `engineval`, `hand`, `engineType`, `gearBox`, `ownerID`, `priceOnly`, `imgOnly`; no `yad2_source` | `url_builder.py`, tests |
| Listing identity | search parser `token` / `listing_id` | SQLite unique key, notify dedup | Canonical URL `/vehicles/item/{id}` | `search_parser.py`, `sqlite_store.py` |
| Feed buckets | `parse_search_page` / `parse_next_data` | pipeline cards | private + commercial + platinum + solo (+ boost in code) | `search_parser.py` |
| ScoredListing.decision | scoring engine | notify path | `notify` \| `skip` \| `rejected` | `models.py`, `scoring_engine.py` |
| TelegramPayload + template placeholders | renderer + `docs/telegram_message_template.md` | Telegram/email | Same listing text; no raw phone | template + `csv_export.CSV_COLUMNS` |
| CSV columns | `csv_export.CSV_COLUMNS` | `data/listings_export.csv` | Must stay aligned with message fields | `csv_export.py` |
| Privacy | detail parser | store, CSV, messages | `phone_available` boolean only | README, tests, parser |
| Collection compliance | browser/http clients | operator | No captcha/token/headless bypass | `PROJECT_STATUS.md`, `browser_client.py`, `fetch_page.js` |
| Node collector stdout | `fetch_page.js` | `BrowserYad2Client` | Last stdout line JSON: `title`, `listingCount`, `htmlPath` | `browser_client.py`, `fetch_page.js` |

## State, Lifecycle, and Recovery

- States/phases: CLI one-shot (`collect`, `run-once`) vs long-running `watch` loop; per-run SQLite `search_runs`; listing first_seen/last_seen; notification rows with `dry_run` flag; watch `notify_mode` `none` (seed) → `new_only`.
- Transition owners: `cli.py` owns command/notify_mode; `SQLiteStore` owns persistence; Node script owns in-page wait/scroll; `search_pages.py` owns pagination stop conditions.
- Cleanup/retry/rollback behavior: HTTP client retries with backoff and Retry-After; browser collector fails closed on Radware or zero listing cards (search); pagination stops after page-1 raise, later-page fetch failure, empty page, no new IDs, known page count, or max 30; watch cycle `RuntimeError` logs and retries after interval; KeyboardInterrupt stops watch; CSV export failure is warned, not fatal; SQLite migrations are additive (`original_ownership` column).
- Missing or ambiguous behavior: no automated rollback of a partial `run-once`; `save_listing` inserts additional detail/score rows on conflict rather than replacing details; no CI live-collection job; HTTP `--http` remains implemented though live HTTP is documented as unusable.

## Validation Model

| Change surface | Existing evidence | Required proof | Known gap |
| --- | --- | --- | --- |
| URL builder / search_groups | `tests/test_url_builder.py`, `tests/test_validators.py` | `validate-config` + `build-url`; pytest | Tests use deepcopy groups; live Yad2 4/4 cap is documented, not network-proven in CI |
| Search/detail parsers | `tests/test_search_parser.py`, `tests/test_detail_parser.py`, `samples/` | pytest on fixtures; live: `collect --browser` then `parse-search-sample` | Fixtures can lag live `__NEXT_DATA__` / selectors |
| Pagination | `tests/test_search_pages.py` | mocked page fetches | Live page count comes from feed JSON |
| Browser client | `tests/test_browser_client.py` | mocked node subprocess | Does not launch real Chrome in tests |
| CLI collect/watch | `tests/test_cli_collect.py`, `tests/test_cli_watch.py` | mocked clients | Live attach is operator-only |
| Scoring / keywords | `tests/test_scoring_engine.py`, `tests/test_keyword_matcher.py` | pytest | `notify_all_matches` currently true in config |
| Telegram/email | renderer/notifier tests | pytest mocks | No live Telegram/SMTP in tests |
| CSV | `tests/test_csv_export.py` | pytest | Operator file `data/listings_export.csv` is working data |
| Live Yad2 | `PROJECT_STATUS.md` 2026-08-15: 34 cards via CDP | `collect --browser` card count | Not reproducible in pytest |

Verified test command: `pytest tests/ -v` (`README.md`, `pyproject.toml` `[tool.pytest.ini_options] testpaths = ["tests"]`). Operator commands require `source .venv/bin/activate`.

## Documentation Model

- Canonical status/architecture docs: `PROJECT_STATUS.md` (operator procedures, live collection); `README.md` (setup, CLI, compliance, structure).
- Runbooks: `PROJECT_STATUS.md` sections “How to configure a new search”, “How to trigger a run”.
- Required update relationships: search-profile how-to vs actual `configs/search_profile_primary.json`; `--browser` / `PLAYWRIGHT_REUSE_TAB` instructions must not contradict `fetch_page.js` behavior; CLI flags in README must match `cli.py`; notification field changes must update `docs/telegram_message_template.md` and `CSV_COLUMNS`.
- Other docs: `docs/PROMPT_FOR_CLAUDE_CODE.md`, `README_ATTACH_TO_CLAUDE.md`, `docs/ATTACHMENT_CHECKLIST.md` are auxiliary attach notes, not runtime contracts.

## Existing Agent Ecosystem

| File | Apparent owner | Strength | Gap/duplication | Disposition candidate |
| --- | --- | --- | --- | --- |
| _(none under `.cursor/`)_ | n/a | n/a | No project workflow, rules, or specialist agents | Generate new factory-owned ecosystem |
| `.claude/settings.local.json` | user / Claude Code | Local Claude settings | Not a Cursor ecosystem | `USER_OWNED_PRESERVE`; do not adopt |

## Source Evidence

| ID | Evidence class | Relative path/section | Claim supported | Confidence |
| --- | --- | --- | --- | --- |
| E-001 | USER_STATED / VERIFIED_DOC | `PROJECT_STATUS.md` | Personal bot; `--browser` + CDP required for live data; no CLI filters; 34 cards on 2026-08-15; compliance | High |
| E-002 | VERIFIED_DOC | `README.md` | Setup, CLI catalog, pytest, privacy, compliance warning | High |
| E-003 | VERIFIED_CONFIG | `pyproject.toml` | Package `yad2-car-bot`, Python ≥3.10, pytest testpaths | High |
| E-004 | VERIFIED_CODE | `src/yad2_car_bot/cli.py` | Commands, notify_modes, pauses, watch defaults `--browser` | High |
| E-005 | VERIFIED_CONFIG | `configs/search_profile_primary.json` | Honda/Hyundai/Toyota/Mazda/Suzuki; four search_groups | High |
| E-006 | VERIFIED_CODE | `src/yad2_car_bot/url_builder.py` | Caps 4/4; cars fallback; `with_page` | High |
| E-007 | VERIFIED_CODE / VERIFIED_TEST | `src/yad2_car_bot/validators.py`, `tests/test_validators.py` | Group validation ERROR/WARNING | High |
| E-008 | VERIFIED_CODE / VERIFIED_TEST | `src/yad2_car_bot/browser_client.py`, `tests/test_browser_client.py` | Node spawn, Radware fail-closed, CDP flags | High |
| E-009 | VERIFIED_CODE | `js_browser/fetch_page.js` | Selectors, settle/scroll, `--reuse-tab`, `--page-kind` | High |
| E-010 | VERIFIED_CODE | `src/yad2_car_bot/http_client.py` | Polite HTTP retries; no Radware solver | High |
| E-011 | VERIFIED_CODE / VERIFIED_TEST | `src/yad2_car_bot/search_pages.py`, `tests/test_search_pages.py` | Pagination stops | High |
| E-012 | VERIFIED_CODE / VERIFIED_TEST | `src/yad2_car_bot/parsers/search_parser.py` | Feed buckets, canonical URLs | High |
| E-013 | VERIFIED_CODE / VERIFIED_TEST | `src/yad2_car_bot/parsers/detail_parser.py` | Technical + description; phone boolean | High |
| E-014 | VERIFIED_CODE | `src/yad2_car_bot/models.py` | Profile, card, detail, scored, payload models | High |
| E-015 | VERIFIED_CODE | `src/yad2_car_bot/config.py` | Loads primary profile only | High |
| E-016 | VERIFIED_CODE | `src/yad2_car_bot/storage/sqlite_store.py` | Schema, dedup, re-notify 10 pts / 5% | High |
| E-017 | VERIFIED_CODE / VERIFIED_TEST | `src/yad2_car_bot/scoring/scoring_engine.py` | Decisions; ownership filter; notify_all_matches | High |
| E-018 | VERIFIED_CONFIG | `configs/scoring_rules.json` | `notify_all_matches: true`, ownership filter enabled | High |
| E-019 | VERIFIED_CONFIG | `configs/listing_keyword_rules.json` | Hebrew hard/soft/positive terms | High |
| E-020 | VERIFIED_CODE | `src/yad2_car_bot/notify.py` | telegram/email/both; env vs `--notify` | High |
| E-021 | VERIFIED_DOC | `docs/telegram_message_template.md` | Message fields | High |
| E-022 | VERIFIED_CODE / VERIFIED_TEST | `src/yad2_car_bot/csv_export.py` | `CSV_COLUMNS` | High |
| E-023 | VERIFIED_TEST | `tests/` | Offline suite; mocked network/browser | High |
| E-024 | VERIFIED_CONFIG | `.env.example` | Env names only (no secrets copied) | High |
| E-025 | VERIFIED_CONFIG | `.gitignore` | `.env`, sqlite, `debug_snapshots/`, `.venv/`, `js_browser/node_modules/` | High |
| E-026 | VERIFIED_CONFIG | `js_browser/package.json` | playwright dependency; postinstall chromium | High |
| E-027 | VERIFIED_CODE | `conftest.py` | Adds `src/` to sys.path for tests | High |

## Contradictions and Staleness

- **Search brands:** `PROJECT_STATUS.md` manufacturer table lists Toyota/Hyundai/Mazda/Suzuki/Nissan and example groups mixing four manufacturers. Live `configs/search_profile_primary.json` has Honda (17), Hyundai (21), Toyota (19), Mazda (27), Suzuki (36) in four manufacturer-aligned groups. Code/config is authoritative for current search; the status doc is stale as a brand roster. Impact: workflow must not treat the status-doc table as the live profile.
- **`PLAYWRIGHT_REUSE_TAB`:** `README.md` setup example exports `PLAYWRIGHT_REUSE_TAB=true`. `PROJECT_STATUS.md` says not to set it unless the car-search tab already shows listing cards; homepage is insufficient. Code implements reuse-tab as optional. Impact: operator docs disagree; architect/planner must reconcile to code + status-doc caution.
- **`--http` usability:** README still lists `collect --http` as a live fetch path. `PROJECT_STATUS.md` and collect’s Radware exit treat live HTTP as failure. HTTP client remains implemented and unit-tested. Impact: `--http` is an offline/dev path, not the live operator path.
- **Watch vs collect defaults:** `watch` defaults `use_browser=True`; `collect`/`run-once` default to HTTP. Status doc says always `--browser` for live data.
- **URL test comment:** `tests/test_url_builder.py` comment names Toyota/Suzuki/Hyundai/Mazda and omits Honda, though assertions only require those IDs to be present (Honda 17 is also in `cars`). Low impact.
- **Feed buckets:** Status doc says private + commercial + platinum + solo. Code `_FEED_BUCKETS` also includes `boost`. Treat code as current.

## Candidate Decision Domains

- Request triage by observable change surface (config-only vs parser vs collector vs storage vs notify).
- Architecture of Python pipeline vs Node collector vs Yad2 HTML/JSON contracts.
- Independent challenge of collection-compliance, privacy, pagination/dedup, and live-vs-fixture proof.
- Implementation planning after gates, with `.venv` CLI and pytest evidence.
- Documentation alignment among `PROJECT_STATUS.md`, `README.md`, and live config.
- Optional extra specialist (parser-contract or collection-safety) vs folding those gates into architect + validation_planner.

## Assumptions and TO_VERIFY

- Assumption: Cursor in this workspace supports agent frontmatter `name`, `description`, and `tools: Read, Grep, Glob`, matching the factory example. Impact if wrong: agents may ignore `tools`. Verification: inspect generated agents in Cursor after install. (`TO_VERIFY`)
- Assumption: No hidden CI exists outside the repo. Impact if wrong: validation matrix would omit pipeline jobs. Verification: confirm no external CI. (`TO_VERIFY`)
- Assumption: Operator continues to use macOS Chrome at `/Applications/Google Chrome.app/...` as in status doc. Impact if wrong: runbook paths differ; code uses Playwright channel `chrome` by default. Verification: operator environment. (`TO_VERIFY`)
- Live Yad2 markup as of this factory run was not re-fetched; 2026-08-15 card-count remains the last documented live proof. (`TO_VERIFY` if generating parser-change plans)
