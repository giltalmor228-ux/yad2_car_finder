# Task Brief

## Workflow ID
[FI-YYYYMMDD-slug]

## User Request
[original request, unmodified]

## Problem Type
[feature | bugfix | refactor | investigation]

## Risk Class
[TRIVIAL | LOCAL_KNOWN_DESIGN | ARCHITECTURE_SENSITIVE | CRITICAL_COLLECTION_OR_PRIVACY]

## Selected Path
[DIRECT IMPLEMENTATION ALLOWED | PLANNER ONLY | ARCHITECT -> VALIDATION_PLANNER -> PLANNER]

## Business / Operator Goal
[what the operator should observe]

## Current Observed Behavior
[code/config/docs evidence; note PROJECT_STATUS.md vs config conflicts]

## Expected Behavior
[required behavior]

## Affected Areas
- CLI / watch / notify_mode:
- Search profile / URL builder / validators:
- Collector (HTTP vs `--browser` / `js_browser/fetch_page.js`):
- Parsers / `__NEXT_DATA__` / selectors:
- Scoring / keywords:
- SQLite / notify / CSV:
- Docs:

## Contracts Touched
[listing_id, search_groups caps, decision enum, CSV_COLUMNS, telegram placeholders, phone_available, CDP flags]

## Explicit Constraints
[user constraints; compliance: no verification bypass; no raw phones]

## Known Evidence
[tests, snapshots, CLI output — no secrets]

## Unknowns and Assumptions
[questions; stale status-doc brand table vs live profile]

## Success Condition
[observable: validate-config, pytest, card count from parse-search-sample, dry-run]
