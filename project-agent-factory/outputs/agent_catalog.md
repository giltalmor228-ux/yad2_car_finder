# Agent Catalog

| Agent | Target file | Decision ownership | Use when | Do not use when | Tools rationale | Evidence IDs | Handoff |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `workflow_triage` | `.cursor/agents/workflow_triage.md` | Risk class (`TRIVIAL` / `LOCAL_KNOWN_DESIGN` / `ARCHITECTURE_SENSITIVE` / `CRITICAL_COLLECTION_OR_PRIVACY`) and lightest safe path | Feature, fix, investigation, or refactor; user unsure if `--browser`, parsers, or SQLite are in play | Skill already in `ARCHITECTURE`+ with a named next agent; spelling-only edit already classified trivial | Read/Grep/Glob only: classify from repo evidence, no edits | E-001, E-004, E-005, E-008, E-012, E-016 | Task Brief + next prompt for `architect` or `planner` |
| `architect` | `.cursor/agents/architect.md` | Candidate design for pipeline, collector, Yad2 contracts, storage, notify/CSV | Architecture-sensitive or critical collection/privacy work | Trivial/local JSON weight tweaks; after a negative gate that needs revision of an existing candidate (then revise, still this role) | Read-only design; must not implement | E-004–E-016, E-020–E-022 | Architect Handoff → `validation_planner` |
| `validation_planner` | `.cursor/agents/validation_planner.md` | Independent gate; collection compliance; privacy; live vs fixture proof | Immediately after architect on architecture/critical paths | First-pass design; planner-only local scoring copy | Read-only challenge; must not silently redesign | E-001, E-008, E-009, E-011–E-013, E-016, E-023 | Validation Gate → `planner` or `architect` |
| `planner` | `.cursor/agents/planner.md` | Ordered implementation + validation/docs plan under approved constraints | Local known-design, or positive architecture gate | `REVISE`/`BLOCKED`; missing architect handoff when required | Read-only planning | E-002, E-003, E-023, E-001 | Implementation plan → feature-intake final packet |

## Role Boundary Notes

- `workflow_triage` must not emit a planner prompt that skips a required architecture gate.
- `architect` output is a candidate. Approval language is forbidden.
- `validation_planner` restates the design neutrally, then challenges; required fixes are conditions or revisions, not a substitute architecture.
- `planner` copies `APPROVED_WITH_CONDITIONS` items verbatim and refuses to drop live-Chrome evidence when the class is `CRITICAL_COLLECTION_OR_PRIVACY`.
- Collection-safety and parser-contract decisions are **checks inside** `architect` / `validation_planner`, not extra agents.

## Omitted or Merged Roles

- Parser-contract reviewer → merged into `architect` (design) and `validation_planner` (proof of `__NEXT_DATA__` / selectors / feed buckets).
- Collection-safety / compliance reviewer → merged into `validation_planner` plus `01-project-core.mdc`.
- Notification/privacy reviewer → merged into core rule + validation gate privacy section.
- Release/CI agent → omitted; no `.github/` workflows found.
- Implementation agent → omitted; intake stops at the final packet.
