# Agent Workflow

Use `.cursor/skills/feature-intake/SKILL.md` as the single entry point for non-trivial changes.

The workflow classifies work into:

- direct implementation for trivial local changes;
- planner-only for bounded changes with established architecture;
- architect, validation planner, then planner for architecture-sensitive, runtime-sensitive, hardware-sensitive, or contract-sensitive changes.

The validation planner returns `APPROVED`, `APPROVED_WITH_CONDITIONS`, `REVISE`, or `BLOCKED`. Planning may begin only after a positive gate when the full path applies. Architecture revision is limited to two iterations before the workflow becomes blocked.

The final packet must identify required tests, real-artifact or real-run evidence, output inspection, stop conditions, and documentation updates.
