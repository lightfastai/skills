#!/usr/bin/env python3
"""Validate public skill packaging, documentation, and release safety."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


REQUIRED_PUBLICATION_CHECKS = {
    "metadata",
    "installability",
    "documentation",
    "provider-independence",
    "sensitive-content",
    "single-high-level-seam",
}
SECURITY_PATTERNS: Tuple[Tuple[str, re.Pattern], ...] = (
    (
        "credential",
        re.compile(
            r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|"
            r"password|private[_-]?key)\s*[:=]\s*[\"']?[^\s\"'<>]{8,}"
        ),
    ),
    (
        "credential",
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ),
    (
        "credential",
        re.compile(r"(?i)\bauthorization\s*:\s*bearer\s+\S+"),
    ),
    (
        "credential",
        re.compile(
            r"\b(?:gh[pousr]_[A-Za-z0-9]{12,}|glpat-[A-Za-z0-9_-]{12,}|"
            r"AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{12,}|"
            r"xox[baprs]-[A-Za-z0-9-]{12,}|AIza[A-Za-z0-9_-]{20,}|"
            r"npm_[A-Za-z0-9_-]{12,})\b"
        ),
    ),
    (
        "credential",
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\."
            r"[A-Za-z0-9_-]{8,}\b"
        ),
    ),
    (
        "credential",
        re.compile(
            r"(?i)\b[A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|PRIVATE_KEY|API_KEY)"
            r"[A-Z0-9_]*\s*[:=]\s*[\"']?[^\s\"'<>]{8,}"
        ),
    ),
    (
        "private-identifier",
        re.compile(
            r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
            r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b"
        ),
    ),
    (
        "private-identifier",
        re.compile(r"(?:^|[\s\"'])(?:/Users/|/home/)[^\s\"']+"),
    ),
    (
        "private-identifier",
        re.compile(
            r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"
        ),
    ),
    (
        "internal-url",
        re.compile(
            r"(?i)https?://(?:localhost|127\.0\.0\.1|10(?:\.\d{1,3}){3}|"
            r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}|"
            r"192\.168(?:\.\d{1,3}){2}|\[?::1\]?|"
            r"\[(?:f[cd][0-9a-f]{2}|fe[89ab])[0-9a-f:]*\]|"
            r"[^/\s]+\.(?:internal|local|corp|lan|intranet)|"
            r"[a-z0-9-]+(?::\d+)?/)"
        ),
    ),
    (
        "copied-provider-response",
        re.compile(r"(?i)\b(?:provider_response|raw_provider_response)\b"),
    ),
    (
        "copied-provider-response",
        re.compile(
            r"(?i)[\"'](?:request_id|response_headers|provider_request_id)"
            r"[\"']\s*:"
        ),
    ),
    (
        "copied-provider-response",
        re.compile(r"(?i)[\"']object[\"']\s*:\s*[\"'][^\"']+[\"']"),
    ),
    (
        "project-specific",
        re.compile(r"(?i)\b(?:quasar|pq-1)\b"),
    ),
)
PROVIDER_IMPLEMENTATION = re.compile(
    r"(?i)(?:"
    r"(?:^|[\s\"'`])(?:gh|glab|vercel|linear|hf|jira|aws|gcloud|az)\s+"
    r"(?:api|auth|issue|pr|project|deploy|env|repo|whoami|s3|lambda)\b|"
    r"\b(?:import|from)\s+(?:github|gitlab|boto3|google\.cloud|azure|"
    r"huggingface_hub|openai|anthropic)\b|"
    r"https?://(?:api\.)?(?:github\.com|gitlab\.com|linear\.app|"
    r"vercel\.com|huggingface\.co|atlassian\.net|amazonaws\.com|"
    r"googleapis\.com|openai\.com|anthropic\.com)(?:/|\b)"
    r")|https?://[^\s\"'`]+"
)


def violation(rule: str, path: Path) -> Dict[str, str]:
    return {"rule": rule, "path": path.as_posix()}


def scan_text(path: Path, text: str) -> List[Dict[str, str]]:
    """Return sanitized rule identifiers for unsafe public content."""
    violations = []
    for rule, pattern in SECURITY_PATTERNS:
        if pattern.search(text):
            violations.append(violation(rule, path))
    if (
        len(path.parts) >= 2
        and path.parts[0:2] == ("skills", "orchestrate")
        and PROVIDER_IMPLEMENTATION.search(text)
    ):
        violations.append(violation("bundled-provider-integration", path))
    return violations


def text_files(skill: Path) -> Iterable[Tuple[Path, Optional[str]]]:
    for path in sorted(skill.rglob("*")):
        if (
            path.is_file() and "__pycache__" not in path.parts
        ):
            content = path.read_bytes()
            if b"\x00" in content:
                yield path, None
                continue
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                yield path, None
                continue
            yield path, text


def frontmatter(path: Path) -> Optional[Dict[str, str]]:
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        return None
    try:
        end = lines.index("---", 1)
    except ValueError:
        return None
    values = {}
    for line in lines[1:end]:
        match = re.match(r"^(name|description):\s*(.+?)\s*$", line)
        if match:
            values[match.group(1)] = match.group(2).strip("\"'")
    return values


def validate_skill(root: Path, skill: Path) -> List[Dict[str, str]]:
    relative_skill = skill.relative_to(root)
    violations = []
    entrypoint = skill / "SKILL.md"
    metadata = skill / "agents" / "openai.yaml"
    if not entrypoint.is_file():
        return [violation("metadata", relative_skill / "SKILL.md")]

    values = frontmatter(entrypoint)
    if not values or values.get("name") != skill.name:
        violations.append(violation("metadata", entrypoint.relative_to(root)))
    elif not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill.name):
        violations.append(violation("metadata", entrypoint.relative_to(root)))
    if not values or not values.get("description"):
        violations.append(violation("metadata", entrypoint.relative_to(root)))

    if not metadata.is_file():
        violations.append(violation("metadata", metadata.relative_to(root)))
    else:
        metadata_text = metadata.read_text(encoding="utf-8")
        for required in (
            "interface:",
            "display_name:",
            "short_description:",
            "default_prompt:",
        ):
            if required not in metadata_text:
                violations.append(violation("metadata", metadata.relative_to(root)))
                break

    for path, text in text_files(skill):
        relative_path = path.relative_to(root)
        if text is None:
            violations.append(violation("unscannable-binary", relative_path))
        else:
            violations.extend(scan_text(relative_path, text))
    return violations


def validate_documentation(root: Path) -> List[Dict[str, str]]:
    readme = root / "README.md"
    orchestrate = root / "skills" / "orchestrate" / "SKILL.md"
    if not readme.is_file() or not orchestrate.is_file():
        return [violation("documentation", Path("README.md"))]
    public_docs = readme.read_text(encoding="utf-8").lower()
    skill_docs = orchestrate.read_text(encoding="utf-8").lower()
    concepts = (
        "first run",
        "coordination boundary",
        "durable",
        "repository contract",
        "approval",
    )
    violations = [
        violation("documentation", Path("README.md"))
        for concept in concepts
        if concept not in public_docs
    ]
    normalized_skill_docs = " ".join(skill_docs.split())
    if not (
        "installed skills or declared capabilities" in normalized_skill_docs
        and "configured tracker" in skill_docs
    ):
        violations.append(
            violation(
                "configured-integration-resolution",
                Path("skills/orchestrate/SKILL.md"),
            )
        )
    return violations


def validate_coverage(
    root: Path, coverage_path: Path
) -> Tuple[List[int], List[Dict[str, str]]]:
    violations = []
    try:
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
        areas = coverage["areas"]
    except (KeyError, OSError, TypeError, ValueError):
        return [], [violation("prd-coverage", coverage_path.relative_to(root))]

    stories = [story for area in areas for story in area.get("user_stories", [])]
    if sorted(stories) != list(range(1, 76)) or len(stories) != len(set(stories)):
        violations.append(violation("prd-coverage", coverage_path.relative_to(root)))

    scenario_source = (root / "tests" / "test_orchestrate_scenarios.py").read_text(
        encoding="utf-8"
    )
    scenario_names = set(
        re.findall(
            r"^\s+def (test_[a-z0-9_]+)\(",
            scenario_source,
            re.MULTILINE,
        )
    )
    referenced_scenarios = {
        name for area in areas for name in area.get("scenario_tests", [])
    }
    if not referenced_scenarios or not referenced_scenarios.issubset(scenario_names):
        violations.append(violation("prd-coverage", coverage_path.relative_to(root)))

    publication_checks = {
        name for area in areas for name in area.get("publication_checks", [])
    }
    if publication_checks != REQUIRED_PUBLICATION_CHECKS:
        violations.append(violation("prd-coverage", coverage_path.relative_to(root)))

    publication_source = (
        root / "tests" / "test_orchestrate_publication.py"
    ).read_text(encoding="utf-8")
    publication_names = set(
        re.findall(
            r"^\s+def (test_[a-z0-9_]+)\(",
            publication_source,
            re.MULTILINE,
        )
    )
    referenced_publication_tests = {
        name for area in areas for name in area.get("publication_tests", [])
    }
    if (
        not referenced_publication_tests
        or not referenced_publication_tests.issubset(publication_names)
    ):
        violations.append(violation("prd-coverage", coverage_path.relative_to(root)))

    if (
        "subprocess.run" not in scenario_source
        or "TRACER = ROOT" not in scenario_source
    ):
        violations.append(
            violation(
                "single-high-level-seam",
                Path("tests/test_orchestrate_scenarios.py"),
            )
        )
    return sorted(stories), violations


def cleanliness_violations(root: Path) -> List[Dict[str, str]]:
    completed = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
        capture_output=True,
        check=False,
        text=True,
    )
    if completed.returncode != 0 or completed.stdout.strip():
        return [violation("repository-cleanliness", Path("."))]
    return []


def validate(
    root: Path,
    coverage_path: Optional[Path],
    require_clean: bool = False,
) -> Dict[str, object]:
    skills_root = root / "skills"
    skills = (
        sorted(path for path in skills_root.iterdir() if path.is_dir())
        if skills_root.is_dir()
        else []
    )
    violations = []
    for skill in skills:
        violations.extend(validate_skill(root, skill))
    violations.extend(validate_documentation(root))

    stories = []
    if coverage_path is not None:
        stories, coverage_violations = validate_coverage(root, coverage_path)
        violations.extend(coverage_violations)
    if require_clean:
        violations.extend(cleanliness_violations(root))

    unique_violations = sorted(
        {json.dumps(item, sort_keys=True) for item in violations}
    )
    return {
        "skills": [skill.name for skill in skills],
        "installable_names": [
            skill.name
            for skill in skills
            if (frontmatter(skill / "SKILL.md") or {}).get("name") == skill.name
        ],
        "prd_user_stories": stories,
        "violations": [json.loads(item) for item in unique_violations],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--coverage", type=Path)
    parser.add_argument("--require-clean", action="store_true")
    arguments = parser.parse_args()

    root = arguments.root.resolve()
    coverage = arguments.coverage.resolve() if arguments.coverage else None
    report = validate(root, coverage, require_clean=arguments.require_clean)
    json.dump(report, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    raise SystemExit(1 if report["violations"] else 0)


if __name__ == "__main__":
    main()
