# Reference Example Generation Notes

This example is derived from the supplied `.cursor` ecosystem and preserves its core architecture and filenames.

## Source-derived files

- agents: `architect.md`, `planner.md`, `validation_planner.md`, `workflow_triage.md`
- rules: `01-project-core.mdc` through `04-feature-intake-workflow.mdc`
- skill: `feature-intake/SKILL.md`
- references: the six supplied handoff and workflow templates

## Repairs and portability changes

- The supplied `SKILL.md` ended immediately after `Architecture Revision: 0` inside an unclosed code block. The example reconstructs the complete workflow from the agents, rules, and templates.
- The supplied `planner.md` also ended with an unclosed implementation-plan code block. The example closes it and adds explicit stop and handoff contracts.
- `workflow_triange` and `workflow_triange.md` were corrected to `workflow_triage`.
- The Markdown wrapper around the uploaded workflow-triage agent was removed.
- Malformed apostrophes were normalized.
- Hardcoded model declarations were removed because model identifiers and organization policy are environment-specific.
- The skill now has explicit routing, a two-revision limit, blocked behavior, readiness criteria, and final response contract.
- A concise project description and agent-workflow document were added so the example is self-explanatory.

No `.DS_Store` or AppleDouble metadata files are included because they are not project artifacts.
