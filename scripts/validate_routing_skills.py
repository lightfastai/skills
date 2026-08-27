#!/usr/bin/env python3
"""Validate the public Lightfast routing skill family without dependencies."""

from __future__ import annotations

import json
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
PUBLIC_SKILLS = (
    "ask-jeevan",
    "navigate",
    "ship",
    "improve",
    "manage-public-presence",
)
ROUTING_SKILLS = PUBLIC_SKILLS[:-1]
INSTALL_COMMAND = f"npx skills add lightfastai/skills --skill {' '.join(PUBLIC_SKILLS)}"
SCENARIO_PATH = ROOT / "tests" / "routing_scenarios.json"


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
    prose = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", prose):
        target = target.strip()
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
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
    allow_implicit = agent.get("policy.allow_implicit_invocation", True)
    validation.require(
        allow_implicit is expected_implicit,
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
    texts = {name: validate_skill(name, validation)[0] for name in PUBLIC_SKILLS}

    ask_routes = set(re.findall(r"`(/[a-z][a-z0-9-]*)`", texts["ask-jeevan"]))
    validation.require(
        ask_routes == set(ROUTES),
        "ask-jeevan: public flow must contain exactly the four Lightfast core routes",
    )
    validation.require(
        "ask matt" not in texts["ask-jeevan"].lower() and "matt pocock" not in texts["ask-jeevan"].lower(),
        "ask-jeevan: upstream structural baselines must not become runtime dependencies",
    )
    validation.require(
        "references/conversation-task-locator.md" in texts["navigate"],
        "navigate: Find must point to the conversation and task locator contract",
    )

    scenario_text = read_text(SCENARIO_PATH, validation)
    try:
        scenarios = json.loads(scenario_text) if scenario_text else {}
    except json.JSONDecodeError as error:
        validation.errors.append(f"{SCENARIO_PATH.relative_to(ROOT)}: invalid JSON: {error}")
        scenarios = {}
    required_scenario_groups = {
        "ask_jeevan",
        "navigate",
        "conversation_task_locator",
        "orchestrator_precedence",
        "route_index",
        "route_index_history",
        "return_events",
    }
    validation.require(
        required_scenario_groups.issubset(scenarios),
        "routing fixtures must cover advisory responses, locator surfaces, frontier, precedence, Route Index, history, and returns",
    )
    scenario_names = [
        scenario["name"]
        for group, values in scenarios.items()
        if group != "route_index_history" and isinstance(values, list)
        for scenario in values
        if isinstance(scenario, dict) and "name" in scenario
    ]
    validation.require(len(scenario_names) == len(set(scenario_names)), "routing scenario names must be unique")

    runtime_docs = [SKILLS_ROOT / name / "SKILL.md" for name in ROUTING_SKILLS]
    for name in ROUTING_SKILLS:
        runtime_docs.extend(sorted((SKILLS_ROOT / name / "references").glob("*.md")))
    forbidden_runtime_links = ("docs/workbench", "docs/orchestrator-map", "/designs/", "/evaluations/")
    for path in runtime_docs:
        text = read_text(path, validation).lower()
        for forbidden in forbidden_runtime_links:
            validation.require(forbidden not in text, f"{path.relative_to(ROOT)}: runtime Workbench/Map lookup path {forbidden} is forbidden")

    readme = read_text(ROOT / "README.md", validation)
    for skill in PUBLIC_SKILLS:
        validation.require(f"skills/{skill}/" in readme, f"README: {skill} discovery entry is missing")
    validation.require(INSTALL_COMMAND in readme, "README: complete public route-set install command is missing")


def main() -> int:
    validation = Validation()
    validate_family(validation)
    if validation.errors:
        for error in sorted(set(validation.errors)):
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Validated 5 public skill packages, 4 core routes, and the deterministic routing contract fixtures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
