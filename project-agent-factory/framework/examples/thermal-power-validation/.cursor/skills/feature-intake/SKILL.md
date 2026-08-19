---
name: feature-intake
description: Runs the complete pre-implementation workflow for non-trivial features, fixes, investigations, behavior changes, and refactors in the thermal, power, telemetry, and hardware-coupled validation repository. Use it to normalize one request, select the safe agent path, enforce architecture challenge and revision gates, and produce an implementation-ready packet.
---

# Feature Intake

## Purpose

Turn one natural-language request into a validated, planner-ready implementation package. Own request normalization, classification, specialist routing, architecture revision, gate enforcement, planner handoff, and final packet assembly.

Do not implement code.

## Required Input

Receive one main request describing a feature, fix, investigation, behavior change, or refactor.

Optional evidence may include logs, screenshots, plans, run directories, output artifacts, validation results, or relevant source files.

## Project Context to Read

Read these when present and relevant:

- `AGENTS.md`
- `docs/PROJECT_STATUS_DETAILED.md`
- `docs/AGENT_WORKFLOW.md`
- task-specific pipeline, artifact, or runbook documentation
- relevant source, configuration, tests, validators, and attached evidence

Do not scan unrelated large run artifacts. Do not copy secrets or sensitive data into workflow artifacts.

## References

Load only the reference needed for the current stage:

- `references/task-brief-template.md`: normalized request and success contract
- `references/workflow-state-template.md`: current stage, gate, blockers, and next owner
- `references/architect-handoff-template.md`: candidate design and invariants
- `references/validation-gate-template.md`: independent challenge and strict gate
- `references/planner-handoff-template.md`: approved design constraints for planning
- `references/final-packet-template.md`: final pre-implementation package

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

Use these exact values.

## Workflow

### 1. Initialize State

Create a workflow ID in the form `FI-YYYYMMDD-<short-task-slug>`.

Initialize from `workflow-state-template.md`:

```text
Current Stage: INTAKE
Architecture Revision: 0
Last Gate: NOT_RUN
Next Agent: workflow_triage
```

### 2. Create the Task Brief

Use `task-brief-template.md`.

- Preserve the user's original intent.
- Separate current behavior from expected behavior.
- Name affected runtime flows, artifacts, contracts, configs, validation, and docs only when evidence supports them.
- Separate explicit constraints, known evidence, assumptions, and unknowns.
- Make the success condition observable.

If a missing fact can materially alter hardware safety, artifact correctness, or workflow selection, set state to `BLOCKED` and request only that fact.

### 3. Classify the Request

Select exactly one path.

#### Architecture-Sensitive Path

Use when the request can affect:

- data collection or orchestration;
- telemetry assignment or synchronization;
- power segmentation or start/stop alignment;
- CSV schemas, keys, uniqueness, metadata propagation, or artifact consumers;
- Stage A or Stage B boundaries or outputs;
- validation logic or proof requirements;
- radar, oven, power analyzer, or other hardware lifecycle;
- runtime phases, transitions, timeouts, retries, cleanup, or recovery;
- large cross-module refactors.

Path:

```text
architect -> validation_planner -> planner
```

#### Planner-Only Path

Use when architecture is established, the change is bounded, contracts and metadata are unchanged, and runtime/hardware state behavior is unaffected.

Path:

```text
planner
```

#### Direct Implementation Allowed

Use only for trivial local changes with no behavior, contract, runtime, validation, or documentation impact. This skill stops with a compact task brief, targeted check, and direct-implementation recommendation.

### 4. Architecture Stage

For the architecture-sensitive path:

1. Set state to `ARCHITECTURE`.
2. Send the Task Brief and relevant evidence to `@architect`.
3. Require output in `architect-handoff-template.md` format.
4. Reject an architect output that omits artifact impact, runtime ownership, failure/recovery behavior, validation proof, or documentation impact.
5. Set `Architecture Revision` to 1 for the first complete candidate.

The architect result is a candidate, not approval.

### 5. Independent Validation Gate

1. Set state to `VALIDATION_GATE`.
2. Send the Task Brief, Architect Handoff, and source evidence to `@validation_planner`.
3. Require `validation-gate-template.md` and one exact gate value.
4. Do not let validation_planner silently redesign the proposal. Required corrections belong under revisions or conditions.

Handle the result:

- `APPROVED`: create the planner handoff.
- `APPROVED_WITH_CONDITIONS`: copy every condition verbatim into the planner handoff as mandatory.
- `REVISE`: execute the revision loop.
- `BLOCKED`: set state to `BLOCKED`, preserve missing inputs, and stop.

### 6. Architecture Revision Loop

Allow at most two architecture revisions.

For `REVISE`:

1. Set state to `REVISION`.
2. Return the previous Architect Handoff plus the complete Validation Gate to `@architect`.
3. Require explicit resolution of every required revision.
4. Increment `Architecture Revision`.
5. Return the revised handoff to `@validation_planner`.

If revision 2 does not receive `APPROVED` or `APPROVED_WITH_CONDITIONS`, set state to `BLOCKED`. Preserve unresolved revisions and exact evidence or decisions required to continue. Do not weaken the gate.

### 7. Planner Handoff

For a positive architecture gate, create `planner-handoff-template.md` from the final candidate and validation gate.

It must include:

- approved architecture;
- all mandatory gate conditions;
- affected files, functions, runtime phases, and artifacts;
- contract and metadata requirements;
- mandatory tests, validators, real-run or real-artifact proof;
- stop conditions;
- documentation requirements.

For planner-only work, produce the same handoff with `Validation Gate: NOT_REQUIRED` and evidence supporting that classification.

### 8. Planning Stage

1. Set state to `PLANNING`.
2. Send the Task Brief and Planner Handoff to `@planner`.
3. Require phases, exact affected paths where verified, dependencies, risks, per-phase validation, testing strategy, real-run proof, documentation updates, and measurable success criteria.
4. Reject a plan that drops a mandatory condition, mixes uncontrolled runtime and analysis changes, or relies only on unit tests when the risk exists in integration or real execution.

### 9. Assemble the Final Packet

Use `final-packet-template.md`.

Set `Ready for Implementation: YES` only when:

- the task brief is complete;
- required architecture has a positive gate;
- all conditions appear in the implementation plan;
- validation evidence and stop conditions are explicit;
- documentation impact is explicit;
- no critical blocker remains.

Otherwise set `Ready for Implementation: NO`, state to `BLOCKED`, and name the exact next input or decision.

### 10. Complete State

When ready, set:

```text
Current Stage: COMPLETE
Next Agent: none
Next Input: implementation may begin from the final packet
```

## Final Response

Return, in order:

1. Workflow State
2. Task Brief
3. Final approved architecture, if required
4. Validation Gate and conditions, if required
5. Final Implementation Plan
6. Required validation and documentation
7. Remaining non-blocking items
8. `Ready for Implementation: YES | NO`

End with one exact implementation prompt that includes the workflow ID and instructs the implementer to follow the final packet and stop conditions.
