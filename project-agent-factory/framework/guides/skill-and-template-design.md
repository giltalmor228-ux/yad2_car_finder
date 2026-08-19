# Skill and Template Design Guide

## Skill scope

The workflow skill is a compact execution manual. Its frontmatter should make triggering reliable, while its body owns state and orchestration. Keep detailed artifact forms and domain reference material outside `SKILL.md`.

## Progressive disclosure

- Frontmatter: name and trigger-rich description.
- `SKILL.md`: essential workflow, state transitions, routing, loops, stop conditions.
- `references/`: templates and focused project knowledge loaded only when needed.

Keep references one level below the skill. Every reference should be named directly by `SKILL.md` with guidance on when to load it.

## Workflow invariants

- One request produces one workflow ID.
- State is updated after every stage.
- Architecture-sensitive work cannot reach planning without a positive gate.
- `APPROVED_WITH_CONDITIONS` conditions are mandatory planner input.
- `REVISE` returns to architecture and increments the revision count.
- Revision count is bounded.
- `BLOCKED` preserves missing inputs and the exact next action.
- Final readiness is explicit.

## Template contract

A template is an interface between stages. It should contain data, not methodology. Good fields separate current state, desired behavior, evidence, assumptions, decisions, conditions, validation, documentation, and remaining unknowns.

## Producer-consumer requirement

Each template needs:

- exactly one primary producing stage;
- at least one consumer;
- headings required by the consumer;
- an identifier that links it to workflow state.

Orphan templates and hidden handoff formats are defects.
