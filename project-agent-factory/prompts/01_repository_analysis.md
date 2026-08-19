# Stage 1 Prompt: Repository and Project Analysis

Analyze the target repository and project brief without writing the final `.cursor` artifacts.

## Goals

- establish what the project actually does;
- identify its architecture and operating model;
- locate contracts, state transitions, boundaries, evidence sources, and failure-sensitive areas;
- inventory any existing agent ecosystem;
- separate verified facts from assumptions.

## Discovery order

1. Read the project description and explicit user constraints.
2. Inventory the repository at high level. Exclude generated, vendored, cache, binary, and large artifact directories unless directly relevant.
3. Read canonical entry points, manifests, package/build files, configuration, CI, tests, schema definitions, public interfaces, architecture/status docs, and runbooks.
4. Inspect `.cursor/`, `AGENTS.md`, and other AI instruction files if present.
5. Trace at least one representative runtime or data flow from input to output.
6. Trace validation from test command to evidence/artifact.
7. Identify contradictions, stale documentation, and missing proof.

## Evidence classes

Tag important claims as:

- `VERIFIED_CODE`
- `VERIFIED_TEST`
- `VERIFIED_CONFIG`
- `VERIFIED_DOC`
- `USER_STATED`
- `INFERRED`
- `TO_VERIFY`

Prefer symbols and focused excerpts over reading every file. Do not copy secrets or sensitive data into outputs.

## Required analysis

Document:

- project purpose and users;
- repository map and dominant technologies;
- runtime components and ownership;
- data, artifact, API, schema, or message flow;
- state machines and lifecycle transitions;
- offline versus runtime boundaries;
- external services, hardware, infrastructure, or deployment dependencies;
- contract surfaces and compatibility obligations;
- validation pyramid and real-environment proof requirements;
- failure, cleanup, rollback, migration, and recovery behavior;
- canonical docs and documentation obligations;
- high-risk change categories;
- existing `.cursor` files, apparent ownership, strengths, gaps, duplication, and conflicts.

## Output

Create `repository_summary.md` using `outputs/repository_summary_template.md`. Include a source-evidence table with exact relative paths and why each source matters.

Do not propose the final agent list yet. End with candidate decision domains and questions that the framework specification must resolve.
