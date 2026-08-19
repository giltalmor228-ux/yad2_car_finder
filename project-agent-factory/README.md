# Project Agent Factory

Project Agent Factory is a reusable prompt-and-template system for generating a project-specific Cursor ecosystem from:

1. a repository plus a project description;
2. a repository without a complete description; or
3. a project description before the repository exists.

The generated system follows the same core pattern as the supplied reference ecosystem: specialist agents, scoped project rules, a single-entry workflow skill, durable handoff templates, validation gates, and a final implementation packet. It is intentionally evidence-driven. It must derive project language, boundaries, contracts, risks, and validation requirements from the target project instead of copying generic personas.

## Fastest usage

Copy this folder into or next to the target repository. In Cursor, attach or reference:

- `prompts/00_project_agent_factory.md`
- the target project's description, preferably based on `inputs/project-description.template.md`
- this factory folder if Cursor cannot already read it

Then send this short instruction:

```text
Execute the attached Project Agent Factory master prompt against this repository.
Use the attached project description as authoritative product context.
Build or safely upgrade the repository's project-specific .cursor ecosystem.
Run the complete consistency review and return the generation report.
```

The master prompt is the exact orchestration prompt. The numbered prompts are its stage contracts and can also be run separately for debugging or review.

## What the factory generates

The normal target layout is:

```text
.cursor/
├── agents/
│   ├── workflow_triage.md
│   ├── architect.md
│   ├── validation_planner.md
│   └── planner.md
├── rules/
│   ├── 01-project-core.mdc
│   ├── 02-architecture-and-planning.mdc
│   ├── 03-validation-and-doc-update.mdc
│   └── 04-feature-intake-workflow.mdc
├── skills/
│   └── feature-intake/
│       ├── SKILL.md
│       └── references/
│           ├── task-brief-template.md
│           ├── workflow-state-template.md
│           ├── architect-handoff-template.md
│           ├── validation-gate-template.md
│           ├── planner-handoff-template.md
│           └── final-packet-template.md
└── agent-factory-manifest.json
```

This is a baseline, not a forced agent count. The factory may add a domain specialist, security reviewer, migration reviewer, data-contract reviewer, or release/operations agent only when repository evidence proves that the role owns a distinct decision or gate. It may also remove an unnecessary baseline role, provided the workflow responsibilities remain covered.

## Inputs and precedence

When sources conflict, use this order:

1. explicit instructions in the current factory run;
2. project description and stated business constraints;
3. repository evidence, including code, tests, CI, schemas, configs, and current `.cursor` files;
4. maintained project documentation;
5. cautious inference, always labeled as an assumption.

Description-only mode may create a provisional ecosystem, but every repository-specific claim must be marked `TO_VERIFY` and the rules must avoid invented paths, commands, or contracts.

## Safety and ownership

- Do not implement the project's feature request. Generate the project workflow system only.
- Inventory an existing `.cursor` directory before writing.
- Never silently replace a user-owned file.
- Update a factory-owned file only when the manifest records it or the user explicitly requests adoption.
- If a filename conflicts with an unowned file, preserve it and generate a clearly named candidate plus a conflict entry in the report.
- Never add secrets, credentials, tokens, private endpoints, or copied sensitive runtime data.
- Avoid hardcoded model identifiers. Omit `model` by default unless the user provides an approved model policy.
- Keep agents read-only unless their role truly requires write or execution capabilities.

## Quality model

Every generated artifact must be:

- project-specific;
- evidence-linked;
- non-duplicative;
- operationally enforceable;
- explicit about inputs, outputs, stop conditions, and handoffs;
- compatible with the repository's actual technology and validation surface;
- concise enough to load efficiently.

The final review fails if the ecosystem only renames generic agents, invents paths or commands, duplicates the same workflow across rules and agents, or allows planning to bypass a required gate.

## Included reference example

`framework/examples/thermal-power-validation/` reconstructs the supplied thermal, power, and telemetry ecosystem in the exact `.cursor` hierarchy shown by the user. The uploaded `SKILL.md` ended mid-code-block, so the example contains a completed version and documents that repair in `GENERATION_NOTES.md`.

## Validation

Run:

```bash
python3 scripts/validate_factory.py
```

The validator checks required factory files, prompt numbering, YAML frontmatter basics, rule metadata, skill size and closure, unresolved template tokens in the finished example, manifest coverage, and cross-file references.

## Current Cursor conventions

This design follows Cursor's current official concepts for [subagents](https://cursor.com/docs/subagents), [project rules](https://cursor.com/docs/rules), and [Agent Skills](https://cursor.com/docs/skills). Exact tool and model availability can vary by Cursor version or organization policy, so generated frontmatter must be conservative and validated in the target environment.
