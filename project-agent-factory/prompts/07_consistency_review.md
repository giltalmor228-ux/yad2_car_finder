# Stage 7 Prompt: Independent Consistency Review

Review the generated ecosystem as a system. Do not assume generation was correct.

## Required checks

### Structural

- expected directories and files exist;
- filenames match frontmatter names;
- YAML frontmatter is closed and parseable;
- every skill Markdown fence is closed;
- globs and relative paths are syntactically plausible;
- the manifest covers every factory-owned file.

### Referential

- every referenced agent exists;
- every referenced skill and template exists;
- workflow states and gate statuses use one canonical vocabulary;
- every handoff producer has a matching consumer;
- every exact path or command is evidence-backed;
- no unresolved template tokens remain in finished project-specific artifacts.

### Behavioral

- trivial changes can take a light path;
- architecture-sensitive changes cannot bypass architecture review;
- independent approval remains independent;
- planning cannot begin after `REVISE` or `BLOCKED`;
- revision loops terminate;
- blocked cases preserve state and required inputs;
- validation depth is proportional to actual project risk;
- documentation updates are part of completion when behavior changes.

### Quality

- roles have distinct ownership;
- descriptions contain reliable triggers;
- persistent rules are concise;
- the skill owns orchestration without duplicating agents;
- project terms are specific and correct;
- no unsupported model or tool assumption is embedded;
- no secrets or sensitive data are copied.

### Simulation

Route at least three scenarios through the ecosystem:

1. a trivial local change;
2. the project description's representative non-trivial request;
3. a failure-prone or contract-sensitive change.

For each scenario, show classification, path, artifacts, gates, stop behavior, validation evidence, and completion condition.

## Decision

Return one status:

- `PASS`
- `PASS_WITH_WARNINGS`
- `FAIL`

On `FAIL`, fix factory-owned artifacts and repeat the review. Do not weaken a requirement simply to pass.

Create `consistency_review.md` from its output template and complete `framework/checklists/final_review.md`.
