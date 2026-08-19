# Collection Evidence

## Workflow ID
[FI-YYYYMMDD-slug]

## Required?
[YES if CRITICAL_COLLECTION_OR_PRIVACY or collector/parser-live change; else N/A]

## Collection Mode
[`--browser` | `--http` (not live) | fixture-only]

## Chrome / CDP
- PLAYWRIGHT_CDP_URL set?:
- PLAYWRIGHT_REUSE_TAB set?: [must be unset unless listing cards already visible]
- Operator completed Yad2 verification manually?: [yes | no | not-needed]

## Commands Run
```text
source .venv/bin/activate
[exact commands]
```

## Results
- Listing cards reported:
- Group HTML paths (`search.html`, `search-2.html`, …):
- `parse-search-sample` outcome:
- Radware page detected?: [yes | no]
- Pagination pages fetched:

## Fixture vs Live
[samples/ vs debug_snapshots/ vs live attach]

## Compliance Check
- Verification automated?: [must be no]
- Headless bypass?: [must be no]
- Tokens forged?: [must be no]

## Blocker
[if live proof cannot be gathered: wait for debug Chrome on port 9222]
