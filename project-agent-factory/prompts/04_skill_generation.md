# Stage 4 Prompt: Generate the Workflow Skill

Generate the single-entry workflow skill defined by the framework specification under `.cursor/skills/<skill-name>/`.

## Purpose

The skill must accept one natural-language feature, fix, investigation, behavior change, migration, or refactor request and produce a durable pre-implementation package through the correct project-specific agent path.

## Required `SKILL.md` properties

- YAML frontmatter contains only `name` and a precise trigger-rich `description`, unless the target platform explicitly supports additional keys.
- The description states what the skill does and when it should trigger.
- The body is procedural, imperative, and under 500 lines.
- Detailed artifact shapes live in `references/`, one level below `SKILL.md`.
- The skill reads only the project context needed for the current task.
- The workflow has explicit states, gates, loops, termination rules, and blocked behavior.
- The skill does not implement code unless the framework explicitly defines an implementation skill. The default feature-intake workflow stops at an implementation-ready packet.

## Mandatory workflow behavior

1. Initialize a workflow ID and state.
2. Normalize the request into the task-brief template.
3. Classify risk using observable project-specific triggers.
4. Select the lightest safe path.
5. Invoke or instruct the required specialist sequence.
6. Persist every handoff in its reference template.
7. Enforce a bounded revision loop for rejected architecture.
8. Stop on missing safety-critical or ownership-critical input.
9. Prevent the planner from bypassing a required gate.
10. Assemble a final packet with `Ready for Implementation: YES | NO`.

## Revision-loop policy

Define a maximum architecture revision count, normally 2. A `REVISE` gate returns to the architecture owner with exact required revisions. A repeated failure at the limit becomes `BLOCKED`, preserving open questions and evidence needed to continue.

## References

Generate every artifact template named in the framework specification. Each reference must have one purpose, stable headings, and placeholders that the skill can fill unambiguously.

Validate using `framework/checklists/skill_checklist.md`. Record the workflow graph and all termination paths in `generation_report.md`.
