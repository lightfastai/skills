#!/usr/bin/env python3
"""Validate the public Lightfast routing skill family without dependencies."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills"
ROUTES = {
    "/ship": "$ship",
    "/improve": "$improve",
    "/navigate": "$navigate",
    "/manage-public-presence": "$manage-public-presence",
}
ROUTING_SKILLS = ("ask-jeevan", "navigate", "ship", "improve")
INSTALL_COMMAND = (
    "npx skills add lightfastai/skills --skill ask-jeevan navigate ship "
    "improve manage-public-presence"
)
ADAPTER_SECTIONS = (
    "Admission",
    "Destination discovery",
    "Bounded handoff",
    "Approval ownership",
    "Return events",
    "Completion evidence",
    "Recovery identity",
)


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)


def read_text(path: Path, validation: Validation) -> str:
    if not path.is_file():
        validation.errors.append(f"missing file: {path.relative_to(ROOT)}")
        return ""
    return path.read_text(encoding="utf-8")


def parse_frontmatter(path: Path, validation: Validation) -> tuple[dict[str, str], str]:
    text = read_text(path, validation)
    if not text:
        return {}, ""

    lines = text.splitlines()
    validation.require(lines[0] == "---", f"{path.relative_to(ROOT)}: frontmatter must start with ---")
    try:
        end = lines.index("---", 1)
    except ValueError:
        validation.errors.append(f"{path.relative_to(ROOT)}: frontmatter is not closed")
        return {}, text

    fields: dict[str, str] = {}
    for line_number, line in enumerate(lines[1:end], start=2):
        match = re.fullmatch(r"([a-z][a-z0-9-]*):\s+(.+)", line)
        if not match:
            validation.errors.append(
                f"{path.relative_to(ROOT)}:{line_number}: unsupported frontmatter syntax"
            )
            continue
        key, value = match.groups()
        validation.require(key not in fields, f"{path.relative_to(ROOT)}: duplicate frontmatter key {key}")
        fields[key] = value.strip('"')
    return fields, text


def parse_openai_yaml(path: Path, validation: Validation) -> dict[str, str | bool]:
    text = read_text(path, validation)
    if not text:
        return {}

    values: dict[str, str | bool] = {}
    section = ""
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        section_match = re.fullmatch(r"([a-z_]+):", line)
        if section_match:
            section = section_match.group(1)
            validation.require(section in {"interface", "policy"}, f"{path.relative_to(ROOT)}:{line_number}: unexpected section {section}")
            continue
        string_match = re.fullmatch(r'  ([a-z_]+): "([^"\\]*(?:\\.[^"\\]*)*)"', line)
        bool_match = re.fullmatch(r"  ([a-z_]+): (true|false)", line)
        if string_match:
            key, value = string_match.groups()
            values[f"{section}.{key}"] = value
        elif bool_match:
            key, value = bool_match.groups()
            values[f"{section}.{key}"] = value == "true"
        else:
            validation.errors.append(f"{path.relative_to(ROOT)}:{line_number}: invalid or unquoted YAML value")
    return values


def validate_links(path: Path, text: str, validation: Validation) -> None:
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        if re.match(r"^[a-z]+://", target):
            continue
        resolved = (path.parent / target.split("#", 1)[0]).resolve()
        validation.require(resolved.exists(), f"{path.relative_to(ROOT)}: broken link {target}")


def validate_skill(name: str, validation: Validation) -> tuple[str, dict[str, str | bool]]:
    skill_dir = SKILLS_ROOT / name
    skill_path = skill_dir / "SKILL.md"
    agent_path = skill_dir / "agents" / "openai.yaml"
    fields, skill_text = parse_frontmatter(skill_path, validation)
    agent = parse_openai_yaml(agent_path, validation)

    validation.require(fields.get("name") == name, f"{name}: frontmatter name must match the folder")
    validation.require(bool(fields.get("description")), f"{name}: description is required")
    validation.require("TODO" not in skill_text, f"{name}: unfinished TODO remains")
    validation.require(
        "disable-model-invocation" not in fields,
        f"{name}: unsupported disable-model-invocation frontmatter key is present",
    )

    expected_implicit = name != "ask-jeevan"
    validation.require(
        agent.get("policy.allow_implicit_invocation") is expected_implicit,
        f"{name}: openai.yaml implicit invocation policy is incorrect",
    )
    for key in ("display_name", "short_description", "default_prompt"):
        validation.require(f"interface.{key}" in agent, f"{name}: interface.{key} is required")
    short_description = agent.get("interface.short_description")
    if isinstance(short_description, str):
        validation.require(
            25 <= len(short_description) <= 64,
            f"{name}: short_description must be 25-64 characters",
        )
    default_prompt = agent.get("interface.default_prompt")
    if isinstance(default_prompt, str):
        validation.require(f"${name}" in default_prompt, f"{name}: default_prompt must mention ${name}")

    validate_links(skill_path, skill_text, validation)
    return skill_text, agent


def validate_family(validation: Validation) -> None:
    texts = {name: validate_skill(name, validation)[0] for name in ROUTING_SKILLS}

    ask_rows = dict(
        re.findall(r"^\| `(/[^`]+)` \|.*\| `(\$[^`]+)` \|$", texts["ask-jeevan"], re.MULTILINE)
    )
    validation.require(ask_rows == ROUTES, "ask-jeevan: v1 route map or next invocations differ from the approved four routes")
    validation.require("Return exactly these three lines" in texts["ask-jeevan"], "ask-jeevan: response must be one route, reason, and next invocation")

    navigate_dir = SKILLS_ROOT / "navigate"
    reference_paths = sorted((navigate_dir / "references").glob("*.md"))
    validation.require(
        [path.name for path in reference_paths] == ["advance-route.md", "find-route.md"],
        "navigate: references must contain exactly the two approved mode files",
    )
    for path in reference_paths:
        validate_links(path, read_text(path, validation), validation)
    validation.require("**route; do not own**" in texts["navigate"], "navigate: routing invariant is missing")
    validation.require("references/find-route.md" in texts["navigate"], "navigate: Find mode reference is not disclosed")
    validation.require("references/advance-route.md" in texts["navigate"], "navigate: Advance mode reference is not disclosed")

    for name in ("ask-jeevan", "ship", "improve"):
        validation.require(
            not (SKILLS_ROOT / name / "references").exists(),
            f"{name}: only navigate should use progressive references",
        )

    for adapter in ("ship", "improve"):
        text = texts[adapter]
        for section in ADAPTER_SECTIONS:
            validation.require(f"## {section}" in text, f"{adapter}: missing adapter section {section}")
        validation.require(f"lightfastai/{adapter}" in text, f"{adapter}: authoritative repository identity is missing")
        validation.require("exact revision" in text.lower(), f"{adapter}: exact destination revision discovery is missing")
        validation.require("Resume compatible work before creating" in text, f"{adapter}: continuation-first destination discovery is missing")

    runtime_docs = [SKILLS_ROOT / name / "SKILL.md" for name in ROUTING_SKILLS] + reference_paths
    forbidden_runtime_links = ("docs/workbench", "docs/orchestrator-map", "/designs/", "/evaluations/")
    for path in runtime_docs:
        text = read_text(path, validation).lower()
        for forbidden in forbidden_runtime_links:
            validation.require(forbidden not in text, f"{path.relative_to(ROOT)}: runtime Workbench/Map lookup path {forbidden} is forbidden")

    readme = read_text(ROOT / "README.md", validation)
    for skill in (*ROUTING_SKILLS, "manage-public-presence"):
        validation.require(f"skills/{skill}/" in readme, f"README: {skill} discovery entry is missing")
    validation.require(INSTALL_COMMAND in readme, "README: complete public route-set install command is missing")


def main() -> int:
    validation = Validation()
    validate_family(validation)
    if validation.errors:
        for error in sorted(set(validation.errors)):
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Validated 4 routing skills, 4 public routes, 2 Navigate modes, and 2 Orchestrator adapters.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
