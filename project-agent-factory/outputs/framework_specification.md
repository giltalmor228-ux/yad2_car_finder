# Framework Specification

## Project System Objective

Make non-trivial Yad2 Car Finder work repeatable: classify a request by observable risk, protect user-assisted collection, parser contracts, SQLite/notify/CSV behavior, and privacy, then emit a planner-ready packet with proportionate pytest and live-Chrome evidence. Do not implement product features during intake.

## Design Inputs

- Repository summary version: `project-agent-factory/outputs/repository_summary.md` (this factory run)
- Project description version: `PROJECT_STATUS.md` (last updated 2026-08-15; authoritative for operator intent and live-collection procedure)
- Existing ecosystem disposition: no `.cursor/` present → generate a new factory-owned baseline. Preserve `.claude/settings.local.json`.

## Change-Risk Taxonomy

| Class | Observable project-specific triggers | Required path | Required evidence |
| --- | --- | --- | --- |
| `TRIVIAL` | Comments, formatting, typo-only edits in non-operator docs; no CLI flag, parser, config schema, SQLite, notify, or selector change | Light Path (direct implementation allowed) | Targeted file review; run related pytest only if a test file was touched |
| `LOCAL_KNOWN_DESIGN` | Hebrew terms in `configs/listing_keyword_rules.json`; numeric weights in `configs/scoring_rules.json` without changing `ScoredListing.decision` vocabulary; caption wording in `docs/telegram_message_template.md` without adding/removing placeholders; test/fixture text that does not change parser selectors or `__NEXT_DATA__` paths; comments in a single scoring/keyword module | Planned Local Path (`planner` only) | `pytest tests/test_keyword_matcher.py tests/test_scoring_engine.py tests/test_telegram_renderer.py` as applicable; `python -m yad2_car_bot.cli validate-config` if JSON configs changed |
| `ARCHITECTURE_SENSITIVE` | Changes to CLI pipeline, `search_groups` / URL builder / validators, Pydantic models, config load paths, search/detail parsers, `search_pages` pagination, HTTP or browser client Python API, `js_browser/fetch_page.js`, SQLite schema or `should_notify`, notify channels, `CSV_COLUMNS`, watch/run-once `notify_mode` | Architecture-Sensitive Path | Architect handoff + independent gate; pytest for touched modules; `validate-config` / `build-url` if search contract changes; fixture `parse-search-sample` / `parse-detail-sample` if parsers change; update `PROJECT_STATUS.md` and/or `README.md` when operator-visible behavior changes |
| `CRITICAL_COLLECTION_OR_PRIVACY` | Live collection behavior; Radware/verification handling; CDP attach / `PLAYWRIGHT_REUSE_TAB` / headless or token logic; rate/politeness pauses; storing or sending seller phone numbers; irreversible SQLite migrations on `data/yad2_car_monitor.sqlite`; `--send` credential/fail-closed behavior | Critical Path (same specialists; extra proof) | Same as architecture-sensitive **plus** `collection-evidence-template.md`. Live proof: `source .venv/bin/activate` then `python -m yad2_car_bot.cli collect --browser --out debug_snapshots/search.html` (debug Chrome on port 9222) **or** explicit `BLOCKED` until the operator can run it. Never accept captcha/token/headless bypass as a solution. |

Use the **heaviest matching class**. Config-only edits to `configs/search_profile_primary.json` manufacturer/model IDs are `LOCAL_KNOWN_DESIGN` if validators and URL shape are unchanged; they become `ARCHITECTURE_SENSITIVE` if caps, URL param names, or group semantics change.

## Role Topology

| Role | Distinct decision ownership | Triggers | Primary output | Downstream consumer |
| --- | --- | --- | --- | --- |
| `workflow_triage` | Risk class, path selection, task-brief completeness | Non-trivial feature/fix/investigation/refactor; uncertain routing | Task brief + selected path + copy-ready next prompts | `feature-intake` skill; `architect` or `planner` |
| `architect` | Candidate design across Python pipeline, Node collector, Yad2 HTML/JSON, SQLite, notify/CSV | `ARCHITECTURE_SENSITIVE` or `CRITICAL_COLLECTION_OR_PRIVACY` | Architect handoff (candidate, not approval) | `validation_planner` |
| `validation_planner` | Independent sufficiency gate: collection compliance, privacy, parser/live proof, notify/dedup, docs | After every architect handoff | Validation gate with exact status | `planner` on positive gate; `architect` on `REVISE` |
| `planner` | Implementation plan that preserves mandatory conditions | `LOCAL_KNOWN_DESIGN`, or positive architecture gate | Planner handoff / implementation plan | `feature-intake` final packet |

## Responsibility Coverage

| Responsibility | Accountable role/stage | Supporting rule/skill | Notes |
| --- | --- | --- | --- |
| Triage | `workflow_triage` | `04-feature-intake-workflow.mdc`, `feature-intake` | Light path may skip specialists |
| Architecture/design | `architect` | `02-architecture-and-planning.mdc` | Candidate only |
| Independent challenge | `validation_planner` | `03-validation-and-doc-update.mdc` | Includes collection/privacy challenge; no separate fifth agent |
| Planning | `planner` | `02-architecture-and-planning.mdc` | Refuses `REVISE`/`BLOCKED` |
| Validation evidence | `validation_planner` defines; `planner` sequences | `03-validation-and-doc-update.mdc` | Unit tests insufficient for live markup/CDP |
| Documentation alignment | `planner` lists; completion requires it | `01-project-core.mdc`, `03-validation-and-doc-update.mdc` | `PROJECT_STATUS.md` vs `README.md` vs live config |

### Merge / omit rationale

- **No parser-contract agent:** parser/`__NEXT_DATA__`/selector risk is the main architecture surface; splitting it would duplicate `architect` and weaken a single gate.
- **No collection-safety agent:** compliance (“do not solve Radware/captchas, forge tokens, or headless-bypass”) is an independent **challenge**, owned by `validation_planner` with a dedicated evidence template.
- **No notify/privacy agent:** privacy is a core invariant (`01-project-core.mdc`) and a mandatory validation check.
- **Triage not merged into the skill alone:** routing mistakes are costly (HTTP vs browser, live vs fixture). A dedicated classifier produces copy-ready prompts.

## Workflow Paths

### Light Path

States: `INTAKE` → `COMPLETE`.
Owners: `feature-intake` (optionally consults `workflow_triage` if classification is uncertain).
Completion: compact task brief, `Validation Gate: NOT_REQUIRED`, `Ready for Implementation: YES` only if truly trivial. No planner packet required beyond the brief.

### Planned Local Path

States: `INTAKE` → `PLANNING` → `COMPLETE`.
Owners: `workflow_triage` then `planner`.
Handoff sets `Validation Gate: NOT_REQUIRED` with classification evidence.
Completion: planner plan + pytest commands for the local surface + docs impact if operator-visible copy changes.

### Architecture-Sensitive Path

States: `INTAKE` → `ARCHITECTURE` → `VALIDATION_GATE` → (`REVISION` ≤2) → `PLANNING` → `COMPLETE` or `BLOCKED`.
Owners: `architect` → `validation_planner` → `planner`.
Gates: `APPROVED` / `APPROVED_WITH_CONDITIONS` required before planning. `REVISE` returns to architect. After two failed revisions: `BLOCKED`.
Completion: final packet with conditions copied verbatim.

### Critical/Specialist Path

Same specialists and states as Architecture-Sensitive Path.
Additional: `collection-evidence-template.md` is mandatory. `validation_planner` must `BLOCKED` if the design automates verification, stores raw phones, or treats pytest fixtures as sufficient proof of live Yad2 markup/CDP attach.

## Canonical Vocabulary

- Workflow states: `INTAKE`, `ARCHITECTURE`, `VALIDATION_GATE`, `REVISION`, `PLANNING`, `COMPLETE`, `BLOCKED`
- Gate statuses: `APPROVED`, `APPROVED_WITH_CONDITIONS`, `REVISE`, `BLOCKED`
- Planner-only marker: `Validation Gate: NOT_REQUIRED` (not a gate status; does not replace the four gate values)
- Light-path marker: `DIRECT IMPLEMENTATION ALLOWED`
- Consistency statuses: `PASS`, `PASS_WITH_WARNINGS`, `FAIL`
- Readiness statuses: `YES`, `NO` (final packet `Ready for Implementation`); factory report `YES` / `YES_WITH_WARNINGS` / `NO`
- Risk classes: `TRIVIAL`, `LOCAL_KNOWN_DESIGN`, `ARCHITECTURE_SENSITIVE`, `CRITICAL_COLLECTION_OR_PRIVACY`

## Artifact Contracts

| Artifact | Producer | Consumer | Mandatory fields | Target template |
| --- | --- | --- | --- | --- |
| Workflow State | `feature-intake` | all stages | Workflow ID, Current Stage, Architecture Revision, Last Gate, Next Agent | `references/workflow-state-template.md` |
| Task Brief | `workflow_triage` (skill may draft on light path) | architect, planner, validation_planner | Workflow ID, request, current vs expected, affected contracts, success condition | `references/task-brief-template.md` |
| Architect Handoff | `architect` | `validation_planner`, later `planner` | candidate design, invariants, failure/recovery, live vs offline boundary, doc impact | `references/architect-handoff-template.md` |
| Validation Gate | `validation_planner` | skill, `planner` | exact Gate value, conditions/revisions, evidence | `references/validation-gate-template.md` |
| Collection Evidence | `validation_planner` or skill when class is critical or collection-touched | `planner`, final packet | mode, CDP/reuse-tab, commands, card counts, Radware, fixture vs live | `references/collection-evidence-template.md` |
| Planner Handoff | `feature-intake` from approved design; `planner` consumes and expands | `planner`, final packet | gate, mandatory conditions, files, validation, docs, stops | `references/planner-handoff-template.md` |
| Final Packet | `feature-intake` | implementer | Ready for Implementation YES/NO | `references/final-packet-template.md` |

## Validation Matrix

| Change category | Unit | Integration | Real artifact/environment | Manual inspection | Documentation |
| --- | --- | --- | --- | --- | --- |
| Keyword/scoring JSON | `test_keyword_matcher.py` / `test_scoring_engine.py` | `score-sample` optional | Not required | Sample listing JSON | Only if notify behavior changes vs `PROJECT_STATUS.md` |
| Telegram template wording | `test_telegram_renderer.py` | `render-telegram-sample` | Not required unless `--send` | Caption length | `docs/telegram_message_template.md` |
| Search profile IDs | `test_validators.py`, `validate-config` | `build-url` | Open printed URLs in debug Chrome if operator wants visual confirm | Status-doc brand table may be stale; do not “fix” live config to match stale docs without operator intent | `PROJECT_STATUS.md` if how-to examples change |
| URL builder / CLI | `test_url_builder.py`, CLI tests | `build-url` / mocked collect | Live `--browser` if query params change meaning | Compare URL to Yad2 | README CLI + `PROJECT_STATUS.md` |
| Parsers | parser tests + `samples/` | `parse-search-sample` on saved HTML | Live `collect --browser` then parse snapshot when selectors/`__NEXT_DATA__` change | Card count vs status-doc 34-card baseline is historical | `PROJECT_STATUS.md` parser/feed notes |
| Browser/Node collector | `test_browser_client.py` | mocked node JSON | Mandatory live attach for collector changes | Radware must remain unsolved | `PROJECT_STATUS.md` + README attach instructions |
| SQLite/notify | store/watch tests | `run-once --browser --dry-run` | Dry-run before `--send` | Dedup/re-notify | `PROJECT_STATUS.md` notify/watch |
| CSV columns | `test_csv_export.py` | `export-csv` | Inspect `data/listings_export.csv` header | Column order | README config table if listed |
| Privacy | `test_detail_parser.py` phone tests | renderer “no phone in text” | Never copy `.env` or phones into artifacts | — | README Privacy |

## Tool and Model Policy

- Supported tool convention: Cursor agent frontmatter `name`, `description`, and `tools` as used by the factory example (`Read`, `Grep`, `Glob`). Omit `model`. Do not add unverified keys such as `readonly` unless later verified.
- Least-privilege decisions: all four agents are read/search only. Implementation happens after the packet, in a normal coding agent, not inside intake agents.
- Approved model policy: none supplied → omit `model` on every agent.

## File Ownership and Migration

| Target path | Desired role | Current ownership | Action | Conflict policy |
| --- | --- | --- | --- | --- |
| `.cursor/agents/*.md` | factory-owned agents | missing | `NEW` | n/a |
| `.cursor/rules/*.mdc` | factory-owned rules | missing | `NEW` | n/a |
| `.cursor/skills/feature-intake/**` | factory-owned skill | missing | `NEW` | n/a |
| `.cursor/agent-factory-manifest.json` | factory ownership record | missing | `NEW` | n/a |
| `.claude/settings.local.json` | user Claude settings | user-owned | `USER_OWNED_PRESERVE` | do not overwrite |
| `PROJECT_STATUS.md`, `README.md`, configs, src | product | user/product | not generated | factory must not implement features |

## Stop Conditions

- Request requires captcha solving, token forging, or headless verification bypass → `BLOCKED`; do not plan it. Owner: `validation_planner` / skill.
- Architecture-sensitive work without architect handoff → `planner` stops.
- Gate `REVISE` or `BLOCKED` → `planner` stops; skill runs revision loop or preserves blockers.
- Live collection change without collection evidence and without operator ability to attach Chrome → `BLOCKED` with next input: CDP Chrome + `collect --browser` result.
- Missing fact that would change risk class (e.g. whether selectors change) → `workflow_triage` `BLOCKED` with one question.
- Revision 2 still not positively gated → `BLOCKED`.
- Doc/code search-roster conflict without operator choice → record conflict; do not silently rewrite `configs/search_profile_primary.json` to match stale `PROJECT_STATUS.md`.

## Assumptions and TO_VERIFY

- Cursor discovers project skills/agents from `.cursor/` without extra user wiring. Affected: usability. Verification: invoke `feature-intake` in a new chat.
- `tools: Read, Grep, Glob` are accepted. Affected: agent frontmatter. Verification: Cursor agent UI.
- No CI job exists to list in the validation matrix. Affected: `03-validation-and-doc-update.mdc`. Verification: confirm remotes/CI.
