# Stage 5 Prompt: Generate Scoped Project Rules

Generate `.cursor/rules/*.mdc` according to `rule_map.md`.

## Rule categories

Prefer a small layered set:

1. project core and invariants;
2. architecture and planning discipline;
3. validation and documentation obligations;
4. single-entry workflow routing;
5. optional domain-specific rules only when their scope and evidence are distinct.

## Metadata

Each rule must have valid YAML frontmatter:

- `description`: precise purpose;
- either `alwaysApply: true` for genuinely universal instructions;
- or a focused `globs` list for file-scoped instructions.

Avoid broad globs when a narrower scope is possible. Do not make every rule always apply.

## Content constraints

- State enforceable behavior, not explanatory essays.
- Use verified repository paths, commands, artifacts, and contract names only.
- Separate invariant protection from workflow routing.
- Do not duplicate agent methodologies or the complete skill workflow.
- Define what must not change silently.
- Define when real-artifact, staging, hardware, migration, replay, or integration evidence is required.
- Define when canonical docs must change.
- Keep rules concise enough to remain useful as persistent context.

## Existing rules

Classify existing rules as retain, refine, merge, deprecate, or conflict. Never delete or overwrite an unowned rule silently.

Validate each rule with `framework/checklists/rule_checklist.md`. Update `rule_map.md` with scope, evidence, overlaps, and ownership.
