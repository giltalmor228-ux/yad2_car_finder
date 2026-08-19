# Project Status Detailed - Reference Excerpt

This compact document exists only to make the example ecosystem internally navigable. A real target repository's maintained status document must replace it.

## Architecture

The project is run-centric, artifact-driven, validation-first, hardware-coupled, and partially replayable offline. Major layers are collection/orchestration, telemetry and CPU synchronization, power processing, Stage A offline characterization, Stage B runtime analysis, and validation/reporting.

## Protected Behavior

- Runtime ownership and lifecycle transitions must be explicit.
- Artifact schemas, uniqueness keys, join semantics, and metadata propagation must not change silently.
- Hardware or runtime pipeline changes require proof beyond isolated unit tests.
- Documentation must describe validated behavior, not intended behavior that has not been proved.

## Canonical Artifacts

Representative contracts include `samples.csv`, `regime_variables.csv`, `regime_variables_model.csv`, `feature.csv`, and Stage A/Stage B outputs.

## Current Workflow Policy

Use `.cursor/skills/feature-intake/SKILL.md` for non-trivial work and follow `docs/AGENT_WORKFLOW.md`.
