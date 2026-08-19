#!/usr/bin/env python3
"""Static validation for a generated Cursor agent ecosystem."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


FRONTMATTER_REQUIRED = {"name", "description"}
GATE_VALUES = {"APPROVED", "APPROVED_WITH_CONDITIONS", "REVISE", "BLOCKED"}


def frontmatter(path: Path) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, [f"{path}: missing opening YAML frontmatter"]
    try:
        end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return {}, [f"{path}: unclosed YAML frontmatter"]
    data: dict[str, str] = {}
    for line in lines[1:end]:
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", line)
        if match:
            data[match.group(1)] = match.group(2).strip()
    return data, errors


def markdown_fence_error(path: Path) -> str | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    count = sum(1 for line in lines if re.match(r"^\s*```", line))
    return None if count % 2 == 0 else f"{path}: unclosed Markdown code fence"


def validate(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    cursor = root / ".cursor"
    if not cursor.is_dir():
        return [f"{root}: missing .cursor directory"], warnings

    agents_dir = cursor / "agents"
    rules_dir = cursor / "rules"
    skills_dir = cursor / "skills"
    for directory in (agents_dir, rules_dir, skills_dir):
        if not directory.is_dir():
            errors.append(f"{root}: missing {directory.relative_to(root)}")

    agent_names: set[str] = set()
    for path in sorted(agents_dir.glob("*.md")) if agents_dir.is_dir() else []:
        data, fm_errors = frontmatter(path)
        errors.extend(fm_errors)
        missing = FRONTMATTER_REQUIRED - data.keys()
        if missing:
            errors.append(f"{path}: missing frontmatter keys {sorted(missing)}")
        name = data.get("name")
        if name:
            agent_names.add(name)
            if path.stem != name:
                errors.append(f"{path}: filename does not match agent name {name!r}")
        if "model" in data:
            warnings.append(f"{path}: hardcoded model requires target-policy verification")
        fence = markdown_fence_error(path)
        if fence:
            errors.append(fence)

    for path in sorted(rules_dir.glob("*.mdc")) if rules_dir.is_dir() else []:
        data, fm_errors = frontmatter(path)
        errors.extend(fm_errors)
        if "description" not in data:
            errors.append(f"{path}: missing rule description")
        if "alwaysApply" not in data and "globs" not in data:
            errors.append(f"{path}: rule needs alwaysApply or globs")
        fence = markdown_fence_error(path)
        if fence:
            errors.append(fence)

    skill_names: set[str] = set()
    for path in sorted(skills_dir.glob("*/SKILL.md")) if skills_dir.is_dir() else []:
        data, fm_errors = frontmatter(path)
        errors.extend(fm_errors)
        missing = FRONTMATTER_REQUIRED - data.keys()
        if missing:
            errors.append(f"{path}: missing skill frontmatter keys {sorted(missing)}")
        name = data.get("name")
        if name:
            skill_names.add(name)
            if path.parent.name != name:
                errors.append(f"{path}: skill directory does not match name {name!r}")
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count >= 500:
            errors.append(f"{path}: SKILL.md has {line_count} lines; must stay below 500")
        fence = markdown_fence_error(path)
        if fence:
            errors.append(fence)
        text = path.read_text(encoding="utf-8")
        for ref in re.findall(r"references/([A-Za-z0-9_.-]+\.md)", text):
            if not (path.parent / "references" / ref).is_file():
                errors.append(f"{path}: missing referenced template references/{ref}")

    all_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in cursor.rglob("*")
        if path.is_file() and path.suffix in {".md", ".mdc"}
    )
    if "workflow_triange" in all_text:
        errors.append(f"{root}: obsolete workflow_triange identifier remains")
    if "architect?s" in all_text:
        errors.append(f"{root}: malformed apostrophe remains")

    mentioned = set(re.findall(r"@([a-z][a-z0-9_-]+)", all_text))
    for name in sorted(mentioned - agent_names):
        warnings.append(f"{root}: @{name} is mentioned but has no local agent file")

    gate_mentions = {value for value in GATE_VALUES if value in all_text}
    if gate_mentions and gate_mentions != GATE_VALUES:
        warnings.append(f"{root}: partial canonical gate vocabulary: {sorted(gate_mentions)}")

    manifest_path = cursor / "agent-factory-manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{manifest_path}: invalid JSON: {exc}")
        else:
            required = {
                "schema_version", "factory_version", "generated_at", "operating_mode",
                "project_name", "workflow_entry_skill", "factory_owned_files",
                "preserved_files", "conflicts", "to_verify"
            }
            missing = required - manifest.keys()
            if missing:
                errors.append(f"{manifest_path}: missing fields {sorted(missing)}")
            for item in manifest.get("factory_owned_files", []):
                rel = item.get("path", "")
                owned_path = root / rel
                if not rel or not owned_path.is_file():
                    errors.append(f"{manifest_path}: owned path does not exist: {rel!r}")
                    continue
                expected_hash = item.get("sha256")
                if expected_hash:
                    actual_hash = hashlib.sha256(owned_path.read_bytes()).hexdigest()
                    if actual_hash != expected_hash:
                        errors.append(f"{manifest_path}: content hash is stale for {rel}")
    else:
        warnings.append(f"{root}: no agent-factory-manifest.json")

    if not agent_names:
        errors.append(f"{root}: no agents found")
    if not skill_names:
        errors.append(f"{root}: no skills found")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="Target project root containing .cursor")
    args = parser.parse_args()
    errors, warnings = validate(args.root.resolve())
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    print(f"RESULT: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
