# Architect Handoff

## Workflow ID
[FI-YYYYMMDD-slug]

## Current State
[modules, live vs fixture, known doc/code conflicts]

## Requirements
[functional, politeness, fail-closed Radware, privacy]

## Candidate Architecture
[Python pipeline vs Node collector ownership; URL → HTML → cards → detail → score → SQLite → notify/CSV]

## Live vs Offline Boundary
[what pytest/samples can prove vs what needs `--browser`]

## System Invariants
[user-assisted collection; no raw phones; search_groups caps; canonical `/vehicles/item/{id}` unless evidence says otherwise]

## Artifact / Contract Impact
- Search URL params / search_groups:
- listing_id / listing_url:
- ScoredListing.decision:
- SQLite tables / should_notify:
- CSV_COLUMNS / telegram placeholders:

## Failure and Recovery Design
[Radware, zero cards, missing Node, pagination stop, watch cycle retry, CSV export warning]

## Risks and Trade-offs
[alternatives; recommendation]

## Validation Impact
[pytest files; CLI; live collect]

## Documentation Impact
[PROJECT_STATUS.md / README.md / telegram template / .env.example]

## Assumptions for Challenge
[items validation_planner must test]

## Open Questions
[unresolved]

## Status
CANDIDATE — not approved
