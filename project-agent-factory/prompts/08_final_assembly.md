# Stage 8 Prompt: Final Assembly and Handoff

Assemble the validated project-specific `.cursor` ecosystem and generation records.

## Preconditions

- consistency status is `PASS` or `PASS_WITH_WARNINGS`;
- no critical unresolved reference exists;
- no mandatory gate can be bypassed;
- all writes comply with the existing-file ownership policy.

## Finalize

1. Write new and factory-owned files to their canonical target paths.
2. Preserve user-owned files.
3. Write conflict candidates beside, not over, unowned conflicting files.
4. Create or update `.cursor/agent-factory-manifest.json`.
5. Complete `generation_report.md` with generated, updated, preserved, conflicting, and provisional files.
6. Include repository evidence and project-brief fingerprints when available, but never secrets or full sensitive contents.
7. Run the available structural validator and any target-specific checks.
8. Show the final tree.

## Manifest minimum fields

- schema version;
- factory version;
- generated timestamp;
- operating mode;
- project name;
- workflow entry skill;
- canonical agents and rules;
- each factory-owned file with path, role, source evidence, and content hash when tooling allows;
- preserved and conflict files;
- remaining `TO_VERIFY` items.

## Final generation report

State:

- what was inferred from the project brief;
- what was verified from code, tests, config, and docs;
- why each agent exists;
- why each mandatory gate exists;
- what changed from any previous ecosystem;
- what remains provisional;
- how to invoke the single-entry workflow;
- what evidence proves the generated system is internally consistent.

Do not claim the ecosystem is production-ready if critical `TO_VERIFY` items remain. Use `Ready for Use: YES`, `YES_WITH_WARNINGS`, or `NO`.
