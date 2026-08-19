#!/usr/bin/env python3
"""Validate the factory package and its reference ecosystem."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from validate_generated_ecosystem import validate as validate_ecosystem


ROOT = Path(__file__).resolve().parents[1]


REQUIRED = [
    "README.md",
    "inputs/project-description.template.md",
    *[f"prompts/{index:02d}_{name}.md" for index, name in enumerate([
        "project_agent_factory",
        "repository_analysis",
        "framework_specification",
        "agent_generation",
        "skill_generation",
        "rule_generation",
        "template_generation",
        "consistency_review",
        "final_assembly",
    ])],
    "framework/checklists/agent_checklist.md",
    "framework/checklists/skill_checklist.md",
    "framework/checklists/rule_checklist.md",
    "framework/checklists/final_review.md",
    "framework/schemas/agent-factory-manifest.schema.json",
    "framework/schemas/framework-specification.schema.json",
    "outputs/repository_summary_template.md",
    "outputs/framework_specification_template.md",
    "outputs/agent_catalog_template.md",
    "outputs/rule_map_template.md",
    "outputs/generation_report_template.md",
    "outputs/consistency_review_template.md",
]


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            errors.append(f"missing required factory file: {rel}")

    for schema in (ROOT / "framework" / "schemas").glob("*.json"):
        try:
            json.loads(schema.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON schema {schema.relative_to(ROOT)}: {exc}")

    master = ROOT / "prompts" / "00_project_agent_factory.md"
    if master.is_file():
        text = master.read_text(encoding="utf-8")
        for index in range(1, 9):
            prefix = f"{index:02d}_"
            if prefix not in text:
                errors.append(f"master prompt does not reference stage {prefix}")

    example = ROOT / "framework" / "examples" / "thermal-power-validation"
    example_errors, example_warnings = validate_ecosystem(example)
    errors.extend(example_errors)
    warnings.extend(example_warnings)

    prompt_files = sorted((ROOT / "prompts").glob("*.md"))
    if [p.name[:2] for p in prompt_files] != [f"{i:02d}" for i in range(9)]:
        errors.append("prompt files must be numbered continuously from 00 to 08")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    print(f"RESULT: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
