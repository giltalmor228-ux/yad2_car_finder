# Validation Gate

## Workflow ID
[FI-YYYYMMDD-slug]

## Gate
[APPROVED | APPROVED_WITH_CONDITIONS | REVISE | BLOCKED]

## Requirement Coverage
[covered vs missing]

## Collection / Runtime Review
[HTTP vs `--browser`, CDP, reuse-tab, Node spawn, pagination, group/detail pauses, watch notify_mode]

## Parser / Contract Review
[`__NEXT_DATA__` buckets, selectors, canonical URLs, CSV columns, decision enum]

## Privacy / Compliance Review
[no verification bypass; phone_available only; no secrets in artifacts]

## Failure-Scenario Review
[Radware, zero cards, duplicate listing_id across groups, notify double-send, missing creds on `--send`]

## Required Conditions
[mandatory if APPROVED_WITH_CONDITIONS; else none]

## Required Revisions
[if REVISE]

## Missing Inputs
[if BLOCKED]

## Validation Evidence Required
- Unit:
- CLI:
- Live Chrome / snapshot:
- Docs:

## Gate Rationale
[why this status]
