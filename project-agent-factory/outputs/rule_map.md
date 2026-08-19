# Rule Map

| Order | Target file | Scope | Persistent obligation | Evidence IDs | Overlap check | Ownership action |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | `.cursor/rules/01-project-core.mdc` | `alwaysApply: true` | Read `PROJECT_STATUS.md` for operator procedure; use `.venv`; config-driven search; live data via `--browser`; no verification bypass; no raw phones; do not treat stale status-doc brand table as live `configs/search_profile_primary.json`; route non-trivial work through `feature-intake` | E-001, E-002, E-005, E-008, E-013, E-015 | Mentions intake routing at high level only; details live in rule 04 | `NEW` |
| 02 | `.cursor/rules/02-architecture-and-planning.mdc` | globs: Python src, `js_browser/**`, `configs/**`, `data/*.json`, models/CLI | Architect before changing pipeline/collector/parser/storage/notify contracts; planner only after positive gate when required | E-004, E-006, E-009, E-012, E-016, E-022 | Does not repeat skill state machine | `NEW` |
| 03 | `.cursor/rules/03-validation-and-doc-update.mdc` | globs: `src/**`, `tests/**`, `js_browser/**`, `configs/**`, `docs/**`, `PROJECT_STATUS.md`, `README.md` | pytest is necessary but not sufficient for live markup/CDP; required commands; docs that must change with behavior | E-001, E-002, E-023, E-021, E-022 | Evidence obligations only; no agent methods | `NEW` |
| 04 | `.cursor/rules/04-feature-intake-workflow.mdc` | `alwaysApply: true` | Single-entry skill; no gate bypass; planner-only when classification allows | factory spec | Does not duplicate specialist methods | `NEW` |

## Precedence and Interaction

- Rule 01 states product invariants every chat must not violate.
- Rule 02 applies when implementation files are in context: require the right specialist sequence.
- Rule 03 applies when code, tests, or canonical docs are in context: require commensurate proof and doc updates.
- Rule 04 is routing policy only. Orchestration lives in `.cursor/skills/feature-intake/SKILL.md`.

## Existing-Rule Disposition

- No existing `.cursor/rules/`. Nothing to retain, merge, or conflict.
- `.claude/settings.local.json` is not a Cursor rule; preserve only.
