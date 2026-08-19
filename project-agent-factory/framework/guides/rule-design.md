# Rule Design Guide

## What belongs in rules

- repository-wide invariants;
- scoped coding or validation obligations;
- behavior that must persist across relevant chats;
- routing requirements that protect mandatory gates;
- documentation completion policy.

## What does not

- long project explanations;
- full agent methods;
- complete multi-stage workflow instructions;
- speculative paths or commands;
- one-off task context;
- repeated copies of the same prohibition.

## Scope selection

Use `alwaysApply: true` only for universal core behavior. Use `globs` for rules tied to implementation areas. Scope architecture rules to source, schema, infrastructure, and relevant docs. Scope validation rules to code, tests, pipelines, or artifacts they govern.

## Layering

Numbered files make precedence and purpose visible. A practical baseline is core, architecture/planning, validation/docs, and workflow routing. Add a domain rule only if it cannot be expressed clearly without becoming noisy for unrelated files.

## Enforceability

Prefer “If a change modifies the event schema, require backward-compatibility evidence and update the schema reference” over “Be careful with schemas.” Name the condition, obligation, evidence, and completion impact.
