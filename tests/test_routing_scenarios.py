from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.validate_routing_skills import Validation, validate_links


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = json.loads((ROOT / "tests" / "routing_scenarios.json").read_text(encoding="utf-8"))
PUBLIC_SKILLS = (
    "ask-jeevan",
    "ship",
    "improve",
    "manage-public-presence",
)
PUBLIC_ROUTES = {f"/{name}" for name in PUBLIC_SKILLS if name != "ask-jeevan"}
DESTINATION_EVENTS = {
    "credential",
    "mfa",
    "permission_change",
    "scope_expansion",
    "consequential_approval",
}






class RoutingScenarioTests(unittest.TestCase):
    def test_ask_jeevan_scenarios_cover_route_and_precedence_invariants(self) -> None:
        seen_routes = {scenario["expected_route"] for scenario in SCENARIOS["ask_jeevan"]}
        self.assertEqual(seen_routes, PUBLIC_ROUTES)

        for scenario in SCENARIOS["ask_jeevan"]:
            with self.subTest(scenario=scenario["name"]):
                facts = scenario["facts"]
                expected = scenario["expected_route"]
                self.assertIn(expected, PUBLIC_ROUTES)
                if facts.get("controlled_public_identity") and not facts.get("live_wayfinding"):
                    self.assertEqual(expected, "/manage-public-presence")
                if facts.get("exact_revision_campaign") and not facts.get("lifecycle_rule_change"):
                    self.assertEqual(expected, "/improve")
                if facts.get("bounded_code_outcome") and len(facts) == 1:
                    self.assertEqual(expected, "/ship")


    def test_orchestrator_lifecycle_precedence(self) -> None:
        for scenario in SCENARIOS["orchestrator_precedence"]:
            with self.subTest(scenario=scenario["name"]):
                if scenario["lifecycle_rule_change"]:
                    self.assertEqual(scenario["expected_destination"], "lightfastai/orchestrator")
                elif scenario["exact_revision_campaign"]:
                    self.assertEqual(scenario["expected_destination"], "improve")



    def test_query_return_and_destination_approval_boundaries(self) -> None:
        for scenario in SCENARIOS["return_events"]:
            with self.subTest(scenario=scenario["name"]):
                kind = scenario["kind"]
                if kind == "result":
                    reconciled = bool(scenario["intent_matches"] and scenario["native_evidence"])
                    self.assertEqual(reconciled, scenario["expected_reconciled"])
                elif kind in DESTINATION_EVENTS:
                    self.assertEqual(scenario["expected_home"], "destination")
                else:
                    self.assertEqual(scenario["expected_home"], "query")


class PackageCompatibilityTests(unittest.TestCase):
    def test_link_validation_checks_angle_paths_but_ignores_fenced_examples(self) -> None:
        validation = Validation()
        validate_links(
            ROOT / "tests" / "example.md",
            "[missing guide](<references/missing guide.md>)",
            validation,
        )
        self.assertEqual(len(validation.errors), 1)

        fenced_validation = Validation()
        validate_links(
            ROOT / "tests" / "example.md",
            "```markdown\n[placeholder](<native link>)\n```",
            fenced_validation,
        )
        self.assertFalse(fenced_validation.errors)

    def test_repository_validator_accepts_schema_and_invocation_policy(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/validate_routing_skills.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(
        os.environ.get("LIGHTFAST_RUN_INSTALLER_TESTS") == "1",
        "set LIGHTFAST_RUN_INSTALLER_TESTS=1 to exercise the current Skills CLI",
    )
    def test_current_skills_cli_fresh_copy_install(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lightfast-skills-install-") as install_dir:
            install_root = Path(install_dir)
            (install_root / "package.json").write_text(
                json.dumps({"name": "lightfast-skills-install-test", "private": True}),
                encoding="utf-8",
            )
            command = [
                "npx",
                "--yes",
                "skills@latest",
                "add",
                str(ROOT),
                "--skill",
                *PUBLIC_SKILLS,
                "--agent",
                "codex",
                "--copy",
                "-y",
            ]
            installed = subprocess.run(
                command,
                cwd=install_root,
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(installed.returncode, 0, installed.stderr or installed.stdout)

            installed_skills = install_root / ".agents" / "skills"
            for name in PUBLIC_SKILLS:
                source = ROOT / "skills" / name
                destination = installed_skills / name
                self.assertTrue(destination.is_dir(), name)
                source_files = {
                    path.relative_to(source): path.read_bytes()
                    for path in source.rglob("*")
                    if path.is_file()
                }
                installed_files = {
                    path.relative_to(destination): path.read_bytes()
                    for path in destination.rglob("*")
                    if path.is_file()
                }
                self.assertEqual(installed_files, source_files, name)

            listed = subprocess.run(
                ["npx", "--yes", "skills@latest", "list", "--json"],
                cwd=install_root,
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(listed.returncode, 0, listed.stderr or listed.stdout)
            names = {entry["name"] for entry in json.loads(listed.stdout)}
            self.assertEqual(names, set(PUBLIC_SKILLS))


if __name__ == "__main__":
    unittest.main()
