# Stage 6 Prompt: Generate Handoff and State Templates

Generate the reference templates required by the workflow skill.

## Required baseline templates

- task brief;
- workflow state;
- architecture or design handoff;
- independent validation gate;
- planner handoff;
- final implementation packet.

Add a domain-specific template only when the framework specification proves a repeatable artifact need, such as a data-contract impact matrix, migration plan, threat review, hardware-run evidence sheet, or release-readiness gate.

## Template design rules

- Use stable Markdown headings.
- Include the workflow ID in every handoff.
- Use strict enumerated statuses where automation depends on them.
- Separate facts, assumptions, unknowns, evidence, conditions, and decisions.
- Include affected contracts and documentation impact where applicable.
- Include stop conditions and required proof.
- Keep placeholders explicit and machine-fillable.
- Avoid duplicating agent instructions inside templates.
- Ensure every template is both produced and consumed by named workflow stages.

## Traceability

Build a producer-consumer matrix. Fail the stage if a template has no producer, no consumer, or a heading required by an agent is missing.

Use the patterns under `framework/templates/` and the supplied project example as guidance, but tailor headings to the target project's risk model.
