# Consistency Review

## Decision

- Status: `PASS`
- Review iteration: 1
- Summary: Greenfield `.cursor` ecosystem matches the frozen specification. Four agents, four rules, one `feature-intake` skill, seven reference templates. Structural validator: 0 errors. Mandatory gates cannot be bypassed. Three simulated routes terminate correctly.

## Structural Findings

- Canonical directories exist: `.cursor/agents/`, `.cursor/rules/`, `.cursor/skills/feature-intake/references/`.
- Agent filenames match frontmatter `name` (`workflow_triage`, `architect`, `validation_planner`, `planner`).
- Skill directory name matches frontmatter `name` (`feature-intake`).
- YAML frontmatter is closed on all agents, rules, and `SKILL.md`.
- `SKILL.md` is 238 lines (limit 500).
- Markdown fences in generated files are balanced.
- Rules use `alwaysApply: true` (01, 04) or single-line `globs` arrays (02, 03).
- Manifest lists every factory-owned file with sha256; hashes match file bytes.
- `.claude/settings.local.json` preserved; no `.cursor` conflicts.

## Referential Findings

- `@workflow_triage`, `@architect`, `@validation_planner`, `@planner` all resolve to agent files.
- Skill references resolve: task-brief, workflow-state, architect-handoff, validation-gate, collection-evidence, planner-handoff, final-packet.
- Workflow states and gate statuses match the specification vocabulary.
- Producer-consumer: each template is produced and consumed by a named stage (see generation report matrix).
- CLI paths and commands are evidence-backed (`python -m yad2_car_bot.cli ...`, `pytest tests/ -v`, `source .venv/bin/activate`).
- No leftover factory tokens such as `<agent_name>`. Angle-bracket CLI placeholders (`<html>`, `<command>`, Workflow ID slug) are intentional.

## Behavioral Findings

- Trivial work can complete at intake without architect or planner.
- Architecture-sensitive and critical paths require architect then validation_planner before planner.
- `validation_planner` is forbidden from designing first; planner refuses `REVISE`/`BLOCKED`.
- Revision loop max 2 then `BLOCKED`.
- Critical collection requires `collection-evidence-template.md`; verification bypass and raw phones stop the workflow.
- Documentation updates are completion requirements when operator-visible behavior changes.
- Lightest-path rule uses heaviest matching risk class, so collection work cannot take the keyword-only path.

## Quality Findings

- Roles have distinct ownership (classify / candidate design / independent gate / plan).
- Descriptions include Yad2-specific triggers (search_groups, CDP, parsers, SQLite notify).
- Rules are short and do not copy the skill state machine.
- No `model` field. Tools limited to Read, Grep, Glob.
- No secrets copied from `.env`.
- Stale `PROJECT_STATUS.md` brand table vs live `configs/search_profile_primary.json` is recorded, not hidden.

## Scenario Simulations

| Scenario | Classification | Path | Gates | Termination | Result |
| --- | --- | --- | --- | --- | --- |
| Fix a comment in `scoring_engine.py` | `TRIVIAL` | Light / direct implementation | `NOT_REQUIRED` | `COMPLETE`, Ready YES, no architect | Pass |
| Restore listing-card detection after Yad2 markup change (representative) | `ARCHITECTURE_SENSITIVE` (critical if CDP/selectors/`fetch_page.js`) | architect → validation_planner → planner | Must be `APPROVED` or `APPROVED_WITH_CONDITIONS`; collection evidence if live selectors | Plan includes pytest parser tests + `collect --browser` + `parse-search-sample`; docs if operator steps change | Pass |
| Automate Radware / headless verification bypass (failure-prone) | `CRITICAL_COLLECTION_OR_PRIVACY` | architect may stop; validation_planner `BLOCKED` | `BLOCKED` | Planner never starts; packet Ready NO | Pass |

## Fixes Applied

- None after first review. Manifest was written after hashing so the validator warning “no manifest” is resolved on re-run.

## Warnings and TO_VERIFY

- Cursor tool-name and skill auto-discovery not executed inside the IDE (`TO_VERIFY`).
- No CI in-repo; validation matrix does not invent jobs (`TO_VERIFY` that none exist externally).
- Live markup not re-sampled in this factory run.
