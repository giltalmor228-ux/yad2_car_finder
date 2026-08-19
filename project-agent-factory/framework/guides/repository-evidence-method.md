# Repository Evidence Method

## Purpose

Agent ecosystems become unreliable when they encode plausible but unverified repository details. The factory therefore builds a small evidence model before it writes instructions.

## Evidence ladder

Use the most direct relevant source:

1. executable code and public interface definitions;
2. tests that demonstrate intended behavior;
3. active build, CI, deployment, or runtime configuration;
4. maintained architecture, status, and runbook documents;
5. user-provided project description;
6. inference, clearly labeled.

The order is not absolute. A project brief can be authoritative about intended future behavior while code is authoritative about the current state. Record the distinction.

## Efficient discovery

- Start with a bounded file inventory.
- Exclude `.git`, dependencies, generated outputs, caches, and binary artifacts.
- Read manifests and entry points before implementation details.
- Search for contract names, output filenames, routes, schemas, state enums, validators, and test commands.
- Trace representative flows and record exact relative paths.
- Sample large domains instead of loading the entire repository.
- Treat stale or contradictory docs as findings, not facts to copy.

## Claim record

For each instruction that embeds project context, retain:

| Field | Meaning |
| --- | --- |
| Claim | The project-specific statement used by an agent or rule |
| Evidence class | Code, test, config, doc, user stated, inferred, or to verify |
| Source | Exact relative path and optionally symbol/section |
| Confidence | High, medium, or low |
| Impact if wrong | What workflow decision would fail |
| Verification | How to resolve uncertainty |

## Description-only mode

Do not invent a repository layout. Use conceptual components and phrases such as “the runtime entry point, once identified.” Add a verification checklist that replaces provisional terms with exact paths after repository access.

## Sensitive material

Evidence outputs should name configuration files and fields but must not reproduce credentials, tokens, private keys, personal data, or proprietary runtime payloads unnecessarily.
