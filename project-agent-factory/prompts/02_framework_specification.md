# Stage 2 Prompt: Framework Specification

Use `repository_summary.md` and the project description to define the complete agent-system contract before generating files.

## Design principle

Create a role only when it owns a distinct decision, analysis method, or gate that would otherwise be weak or overloaded. Create a rule only when persistent instruction is needed. Create a skill when a repeatable multi-step workflow benefits from reusable references or scripts.

## Required decisions

1. Define change-risk classes using project-specific triggers.
2. Define workflow paths from trivial/local to architecture-sensitive or safety-critical.
3. Define the minimum role topology.
4. Assign one accountable owner to every workflow responsibility.
5. Define required gates and strict status vocabulary.
6. Define artifacts passed between stages.
7. Define implementation stop conditions.
8. Define validation evidence by change category.
9. Define documentation-update rules.
10. Define tool least privilege and model policy.
11. Define existing-file ownership and migration decisions.

## Baseline responsibilities to cover

- entry-point triage and request normalization;
- architecture or system-design analysis where needed;
- independent challenge for high-risk designs;
- implementation planning after required approval;
- validation and completion evidence;
- documentation alignment.

These responsibilities need not map one-to-one to agents. Explain every merge, split, addition, or omission.

## Anti-pattern checks

Reject a design that:

- creates agents only by technology label;
- assigns overlapping final authority;
- uses subjective triggers such as “complex” without observable criteria;
- makes every task follow the heaviest path;
- lets the planner approve architecture it depends on;
- repeats the entire workflow in every agent and rule;
- treats unit tests as sufficient for changes whose risk exists only at integration or runtime;
- requires files or commands not proven to exist.

## Output

Create `framework_specification.md` using `outputs/framework_specification_template.md`. Also create `agent_catalog.md` and `rule_map.md` from their templates.

Freeze canonical names, gate statuses, workflow states, artifact names, and target paths. Later stages may not rename them silently. Any necessary change must update all three specification artifacts and be recorded in the generation report.
