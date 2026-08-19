# Agent Design Guide

## When an agent is justified

Create a specialist agent when all are true:

- it owns a distinct decision or challenge;
- its reasoning benefits from isolated context;
- it has a recognizable trigger;
- its output is consumed by another stage or the user;
- combining it with another role would weaken independence or clarity.

Technology labels alone are insufficient. “Python expert” is normally less useful than “data-contract reviewer” if the project risk is schema and join-key integrity.

## Description quality

The frontmatter description is a discovery mechanism. It should state:

- what the agent does;
- project domains it protects;
- observable triggers;
- when in the workflow to use it.

Avoid “expert helper for many tasks” and project history that does not affect triggering.

## Body structure

Recommended sections:

1. Role and decision authority
2. Trigger and non-trigger conditions
3. Preconditions and inputs
4. Focused project context
5. Method
6. Invariants and failure modes
7. Required output
8. Gate or decision vocabulary
9. Stop conditions
10. Handoff

## Tool policy

Grant the narrowest capabilities that support the role. Architecture, validation planning, and implementation planning should normally read and search. An agent that is expected to edit or execute requires an explicit rationale and project authorization. Do not assume a tool name exists in every Cursor version.

## Project specificity test

Remove the project name from the file. If the agent would fit almost any repository unchanged, it is not specific enough. Improve it with verified boundaries, risks, artifacts, state transitions, test evidence, and documentation contracts. Do not solve this by adding long lists of paths.

## Output discipline

Use strict headings and enumerated decisions. A downstream role should not need to reinterpret prose to find mandatory conditions. Include exact stop behavior when inputs are missing or a gate is negative.
