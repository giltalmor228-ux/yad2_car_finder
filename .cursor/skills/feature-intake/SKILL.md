---
name: feature-intake
description: Runs the pre-implementation workflow for Yad2 Car Finder features, fixes, investigations, and refactors. Use when changing search_groups, Playwright CDP collection, parsers, scoring, SQLite notify, Telegram/email, or CSV export. Normalizes one request, routes the lightest safe agent path, enforces architecture and collection/privacy gates, and produces an implementation-ready packet without writing product code.
---

# Feature Intake

## Purpose

Turn one natural-language request into a validated, planner-ready packet for this bot. Own normalization, risk classification, specialist routing, revision, and packet assembly.

Do not implement product code.

## Required Input

One request: feature, fix, investigation, behavior change, or refactor.

Optional evidence: HTML snapshots under `debug_snapshots/` or `samples/`, pytest output, CLI logs, config diffs. Never paste `.env` secrets.

## Context to Read

Read when relevant, do not scan the whole tree:

- `PROJECT_STATUS.md` (operator procedure; live `--browser`)
- `README.md` (setup/CLI; may disagree with status on `PLAYWRIGHT_REUSE_TAB` and `--http`)
- `configs/search_profile_primary.json` (live search; not the status-doc brand table)
- task-specific modules under `src/yad2_car_bot/`, `js_browser/fetch_page.js`, `tests/`
- attached snapshots

## References

Load only the file for the current stage:

- `references/task-brief-template.md`: normalized request
- `references/workflow-state-template.md`: stage, gate, next owner
- `references/architect-handoff-template.md`: candidate design
- `references/validation-gate-template.md`: independent gate
- `references/collection-evidence-template.md`: live Chrome / Radware / card counts (critical or collector/parser-live work)
- `references/planner-handoff-template.md`: constraints for planning
- `references/final-packet-template.md`: readiness packet

## Canonical States and Gates

Workflow states:

```text
INTAKE
ARCHITECTURE
VALIDATION_GATE
REVISION
PLANNING
COMPLETE
BLOCKED
```

Validation gates:

```text
APPROVED
APPROVED_WITH_CONDITIONS
REVISE
BLOCKED
```

Risk classes:

```text
TRIVIAL
LOCAL_KNOWN_DESIGN
ARCHITECTURE_SENSITIVE
CRITICAL_COLLECTION_OR_PRIVACY
```

Use these exact values. Planner-only work records `Validation Gate: NOT_REQUIRED` (not a gate status).

## Workflow

### 1. Initialize State

Create Workflow ID `FI-YYYYMMDD-<short-task-slug>`.

Initialize `workflow-state-template.md`:

```text
Current Stage: INTAKE
Architecture Revision: 0
Last Gate: NOT_RUN
Next Agent: workflow_triage
```

### 2. Task Brief

Fill `task-brief-template.md` via `@workflow_triage` (you may draft a brief for obvious `TRIVIAL` work).

Separate current vs expected behavior. Name contracts only with evidence. If `PROJECT_STATUS.md` and code/config disagree, record both; code/config is current behavior.

If one missing fact would change safety, collection compliance, or path selection, set `BLOCKED` and ask only that fact.

### 3. Classify and Route

Pick the **heaviest** matching class.

#### Critical collection or privacy

Triggers: Radware/verification, CDP, `PLAYWRIGHT_REUSE_TAB`, headless/token ideas, politeness pauses, raw phones, SQLite migrations, `--send` fail-closed.

Path:

```text
architect -> validation_planner -> planner
```

`collection-evidence-template.md` is mandatory. Designs that bypass verification or store phones → `BLOCKED`.

#### Architecture-sensitive

Triggers: CLI pipeline, URL/`search_groups` semantics, parsers, clients, `js_browser/fetch_page.js`, SQLite notify, notify channels, `CSV_COLUMNS`, pagination, watch `notify_mode`.

Path:

```text
architect -> validation_planner -> planner
```

#### Planner-only (`LOCAL_KNOWN_DESIGN`)

Triggers: keyword terms or score weights without decision-enum change; telegram wording without placeholder add/remove; profile ID edits that still pass existing validators and do not change URL param names.

Path:

```text
planner
```

Planner handoff uses `Validation Gate: NOT_REQUIRED` plus classification evidence.

#### Direct implementation (`TRIVIAL`)

Formatting/comments only. Stop with compact brief, targeted check, `Ready for Implementation: YES`.

### 4. Architecture

For architecture or critical paths:

1. Set `ARCHITECTURE`.
2. Send Task Brief to `@architect`.
3. Require `architect-handoff-template.md`.
4. Reject outputs that omit live vs fixture boundary, failure/recovery, or doc impact.
5. Set `Architecture Revision` to 1 on the first complete candidate.

The architect result is not approval.

### 5. Validation Gate

1. Set `VALIDATION_GATE`.
2. Send Task Brief, Architect Handoff, and evidence to `@validation_planner`.
3. Require `validation-gate-template.md` and one exact gate value.
4. Do not let validation_planner silently redesign. Fixes are conditions or revisions.

Handle:

- `APPROVED`: planner handoff
- `APPROVED_WITH_CONDITIONS`: copy every condition verbatim
- `REVISE`: revision loop
- `BLOCKED`: preserve missing inputs and stop

### 6. Revision Loop

At most **two** architecture revisions.

On `REVISE`:

1. Set `REVISION`.
2. Return prior handoff + full gate to `@architect`.
3. Require explicit resolution of every required revision.
4. Increment `Architecture Revision`.
5. Return to `@validation_planner`.

If revision 2 is not `APPROVED` or `APPROVED_WITH_CONDITIONS`, set `BLOCKED`. Do not weaken the gate.

### 7. Planner Handoff

Positive gate → `planner-handoff-template.md` with approved design, conditions, files, tests, live proof, docs, stops.

Planner-only → same template with `Validation Gate: NOT_REQUIRED`.

### 8. Planning

1. Set `PLANNING`.
2. Send Task Brief + Planner Handoff to `@planner`.
3. Reject plans that drop a condition, use `--http` as the live path, or rely only on pytest when risk is live markup/CDP.

### 9. Final Packet

Fill `final-packet-template.md`.

`Ready for Implementation: YES` only when:

- task brief complete;
- required architecture has a positive gate (or NOT_REQUIRED with evidence);
- all conditions appear in the plan;
- validation and docs are explicit;
- no critical blocker remains.

Otherwise `NO`, state `BLOCKED`, name the next input.

### 10. Complete

When ready:

```text
Current Stage: COMPLETE
Next Agent: none
Next Input: implementation may begin from the final packet
```

## Stop Conditions

- Verification bypass or raw phone storage requested → `BLOCKED`.
- Critical collection change without collection evidence and without operator Chrome → `BLOCKED`.
- `@planner` after `REVISE`/`BLOCKED` is forbidden.
- Do not implement code in this skill.

## Completion

Return, in order:

1. Workflow State
2. Task Brief
3. Approved architecture if required
4. Validation Gate and conditions if required
5. Collection evidence if required
6. Implementation plan
7. Required validation and documentation
8. Remaining non-blocking items
9. `Ready for Implementation: YES | NO`

End with one implementation prompt that includes the Workflow ID and instructs the implementer to follow the packet and stop conditions.
