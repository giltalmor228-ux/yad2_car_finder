# Factory Operating Model

## Separation of responsibilities

| Layer | Owns | Must not own |
| --- | --- | --- |
| Project rules | Persistent invariants, scoped obligations, routing policy | Full role methodology or multi-stage orchestration |
| Agents | Specialist analysis, decisions, challenges, output contracts | Shared policy copied across every role |
| Workflow skill | State, orchestration, delegation, revision loops, packet assembly | Deep specialist reasoning repeated from agent files |
| Skill references | Durable artifact shapes and focused domain references | Independent behavior or hidden workflow logic |
| Manifest | Generated ownership, evidence, versioning, conflicts | Project policy |
| Generation reports | Audit trail, assumptions, validation outcome | Runtime instructions for every future task |

## Preferred topology

The supplied ecosystem uses four roles:

- `workflow_triage`: classifies and normalizes;
- `architect`: proposes system design;
- `validation_planner`: independently challenges it;
- `planner`: turns approved design into an implementation plan.

This topology is strong when architecture errors are more expensive than an extra review step. It is not mandatory. A small library may merge triage into the skill and use architect plus planner. A regulated service might add a security/compliance gate. A data platform may justify a separate contract reviewer. Additions require a distinct decision boundary and a named handoff.

## Workflow weight

Use observable change characteristics:

| Class | Typical evidence | Safe path |
| --- | --- | --- |
| Trivial | local text/formatting, no behavior or contract change | direct implementation allowed with a targeted check |
| Local known-design | bounded code change, stable interface, no state or deployment impact | planner then implementation and validation |
| Architecture-sensitive | component boundary, data flow, public API, schema, migration, lifecycle, concurrency, or deployment change | architect, independent challenge, planner |
| Critical | security boundary, irreversible migration, hardware control, safety, compliance, high blast radius | expanded specialist gate plus real-environment proof |

Project-specific rules must replace these examples with the target's real triggers.

## State discipline

Recommended canonical states:

```text
INTAKE
ARCHITECTURE
VALIDATION_GATE
REVISION
PLANNING
COMPLETE
BLOCKED
```

Recommended gate vocabulary:

```text
APPROVED
APPROVED_WITH_CONDITIONS
REVISE
BLOCKED
```

Do not use near-synonyms such as `ACCEPTED`, `PASS`, and `NEEDS_WORK` inside the same generated workflow. Consistency status is separate and may use `PASS`, `PASS_WITH_WARNINGS`, and `FAIL`.

## Independence

The architecture challenger must receive the candidate architecture and source evidence. It should not be the first designer, should not silently repair the proposal, and should not approve based on elegance. Its output must identify exact proof and conditions.

## Completion

A pre-implementation skill is complete only when it produces a coherent task brief, approved design when required, mandatory gate conditions, implementation plan, validation plan, documentation impact, and a final readiness flag. It is blocked, not partially complete, when required safety or ownership input is missing.
