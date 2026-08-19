# Project Description: Thermal, Power, and Telemetry Validation Pipeline

## Project Identity

- Project name: BSR Thermal Power Standalone
- Purpose: Collect, align, characterize, and validate radar thermal, power, telemetry, and runtime behavior through run-centric artifacts.
- Primary users: System integration and validation engineers.
- Lifecycle stage: Active development and validation.

## Scope

The repository coordinates hardware-coupled collection and replayable offline analysis. Its major areas are data collection/orchestration, telemetry and CPU synchronization, power processing, offline characterization (Stage A), runtime analysis (Stage B), and validation/reporting.

Typical work includes new collection behavior, telemetry mapping, power segmentation, artifact-schema evolution, Stage A/Stage B features, validation improvements, and runtime/hardware fixes.

## System Context

Canonical package areas:

- `src/bsr_thermal_power_standalone/collection/`
- `src/bsr_thermal_power_standalone/telemetry_pipeline/`
- `src/bsr_thermal_power_standalone/power/`
- `src/bsr_thermal_power_standalone/analysis/`
- `src/bsr_thermal_power_standalone/utils/`

The system is hardware-coupled but partially replayable offline. Runtime concerns include radar connect/disconnect, oven and ambient control, per-setpoint state, power start/stop alignment, retries, cleanup, and output completeness.

## Critical Contracts

Artifact correctness is a primary system contract. Important surfaces include `samples.csv`, `regime_variables.csv`, `regime_variables_model.csv`, `feature.csv`, Stage A/Stage B outputs, metadata propagation, uniqueness keys, and merge behavior. These contracts must not change silently.

## Validation Model

Unit tests are necessary but insufficient for runtime pipeline changes. Depending on the change, completion may require validators, output inspection, real-artifact replay, or a real hardware run. Canonical status documentation must remain aligned with validated behavior.

## High-Risk Changes

- collection lifecycle and control timing;
- telemetry assignment and synchronization;
- segmentation and frame alignment;
- schema, key, uniqueness, and metadata changes;
- Stage A/Stage B boundary changes;
- hardware state transitions, timeouts, retries, or cleanup;
- cross-module refactors.

## Desired Ecosystem

Use `feature-intake` as the single entry point. Architecture-sensitive work must follow architect, independent validation challenge, and planner. Bounded known-design work may use planner-only. Trivial local work may proceed directly with a proportionate check.

## Representative Request

> Add adaptive per-setpoint collection duration so power capture and `samples.csv` remain aligned when oven stabilization finishes earlier or later than the static schedule.
