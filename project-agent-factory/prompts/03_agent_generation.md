# Stage 3 Prompt: Generate Project-Specific Agents

Generate the agent files defined by the accepted framework specification under `.cursor/agents/` or as conflict candidates under the existing-file policy.

## Agent contract

Each agent must contain:

1. valid YAML frontmatter with a stable lowercase `name`, precise third-person `description`, and least-privilege `tools` when supported;
2. a project-specific role statement;
3. explicit trigger conditions and non-triggers;
4. required inputs and preconditions;
5. focused repository context supported by evidence;
6. a deterministic review or reasoning process;
7. project-specific risks, invariants, and failure modes;
8. a strict output format;
9. stop conditions and escalation rules;
10. the exact downstream handoff contract.

## Frontmatter policy

- Omit `model` unless the approved project input defines one.
- Do not guess tool names. Use the target's supported convention or omit unsupported keys.
- Review and planning agents should default to read-only tools.
- Do not give execution or write tools merely for convenience.
- Ensure the filename, `name`, references, and mentions match exactly.

## Content policy

- Use exact project vocabulary and verified relative paths sparingly.
- Refer to canonical rules and skill artifacts instead of duplicating them.
- Put shared behavior in rules, not every agent.
- Make decisions falsifiable. Specify evidence that would change a conclusion.
- An independent challenger must not design the first solution and must use a strict gate vocabulary.
- A planner must refuse to proceed when required approvals or inputs are absent.
- A triage agent must produce copy-ready next prompts but must not bypass workflow gates.

## Verification

Evaluate every generated agent with `framework/checklists/agent_checklist.md`. Record role-specific evidence, generated path, tool rationale, and any unverified claim in `agent_catalog.md` and `generation_report.md`.
