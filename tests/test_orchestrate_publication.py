import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_orchestrate_scenarios import (
    active_work_snapshot,
    bootstrap_snapshot,
    checkpoint,
    delivered_work_snapshot,
    durable_snapshot,
    local_orchestration_contract,
    prepared_snapshot,
    run_scenario,
)


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_public_release.py"
COVERAGE = ROOT / "tests" / "orchestrate_prd_coverage.json"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_public_release", VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("publication validator is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CompleteReleaseScenarios(unittest.TestCase):
    def test_every_release_area_runs_through_the_public_orchestration_seam(
        self,
    ) -> None:
        recovery = durable_snapshot(checkpoint())

        scheduling = prepared_snapshot()
        scheduling["programme"]["approved_order"] = [43, 42]
        scheduling["tickets"].append(
            {
                "issue": 43,
                "title": "Release candidate",
                "state": "ready",
                "blocked_by": [],
            }
        )

        delegation = prepared_snapshot(intent="research")

        monitoring = active_work_snapshot(
            {
                "id": "task-8",
                "issue": 8,
                "state": "running",
                "resumable": True,
                "native_wait": {"after_cursor": "event-8"},
                "updated_at": "2026-08-24T10:05:00Z",
            }
        )
        monitoring["observed_at"] = "2026-08-24T10:06:00Z"

        merge = delivered_work_snapshot()

        approvals = prepared_snapshot()
        approvals["tickets"][0]["gates"] = {
            "credentials": {"scope": {"purpose": "release"}}
        }

        capability = prepared_snapshot(intent="coordinate")
        capability["stewardship"] = {
            "capability": {
                "category": "security_scanning",
                "reason": "protect public releases",
                "approved": False,
            }
        }

        research = prepared_snapshot(intent="coordinate")
        research["stewardship"] = {
            "research": {
                "question": "Has the release baseline changed?",
                "roadmap_decision": "release-policy",
                "urgency": "default",
                "approved": False,
            }
        }

        bootstrap = bootstrap_snapshot()

        migration = bootstrap_snapshot()
        migration["bootstrap"]["conventions"]["programme_discovery"] = {
            "satisfies_contract": True
        }
        migration["bootstrap"]["agent_instructions"] = {
            "discovers_contract": True
        }
        migration["bootstrap"]["local_contract"] = (
            local_orchestration_contract()
        )
        migration["bootstrap"]["capability_gaps"] = []
        migration["bootstrap"]["policy"] = {
            "published_version": 2,
            "adopted_version": 1,
            "change_ids": ["public-release-hardening"],
        }

        cases = {
            "recovery": (recovery, "recover"),
            "scheduling": (scheduling, "delegate"),
            "delegation": (delegation, "delegate"),
            "monitoring": (monitoring, "watch"),
            "merge": (merge, "merge"),
            "approvals": (approvals, "stop"),
            "capabilities": (capability, "propose-capability"),
            "research": (research, "record-research-radar"),
            "bootstrap": (bootstrap, "bootstrap-audit"),
            "migrations": (migration, "bootstrap-audit"),
        }

        outcomes = {}
        for area, (snapshot, expected_decision) in cases.items():
            with self.subTest(area=area):
                outcome = run_scenario(snapshot)
                outcomes[area] = outcome
                self.assertEqual(outcome["decision"], expected_decision)
                self.assertFalse(outcome["root_mutation_permitted"])

        self.assertEqual(
            outcomes["migrations"]["policy"]["status"],
            "migration-proposed",
        )


class PublicReleaseChecks(unittest.TestCase):
    def test_repository_publication_gate_passes(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "--root",
                str(ROOT),
                "--coverage",
                str(COVERAGE),
            ],
            capture_output=True,
            check=True,
            text=True,
        )
        report = json.loads(completed.stdout)

        self.assertEqual(
            report["skills"], ["manage-public-presence", "orchestrate"]
        )
        self.assertEqual(report["installable_names"], report["skills"])
        self.assertEqual(report["prd_user_stories"], list(range(1, 76)))
        self.assertEqual(report["violations"], [])

    def test_static_gate_rejects_each_sensitive_content_class(self) -> None:
        validator = load_validator()
        unsafe_samples = {
            "credential": "api_key = " + "sk" + "-release-secret-value",
            "bearer-credential": (
                "Authorization: Bearer " + "gh" + "p_releaseSecret123"
            ),
            "slack-credential": (
                "xox" + "b-123456789012-releaseSecretValue"
            ),
            "google-credential": (
                "AI" + "zaSyReleaseSecretValue1234567890"
            ),
            "npm-credential": "np" + "m_releaseSecretValue1234567890",
            "jwt-credential": (
                "eyJhbGciOiJIUzI1NiJ9."
                + "eyJzdWIiOiIxMjMifQ."
                + "releaseSig123"
            ),
            "generic-secret": "AWS_SECRET_ACCESS_KEY=releaseSecretValue123",
            "private-identifier": "task_id: 123e4567-e89b-12d3-a456-426614174000",
            "private-email": "owner@example.test",
            "internal-url": "https://release-service.internal/status",
            "private-network": "http://172.20.1.4/status",
            "loopback": "http://[::1]/status",
            "private-ipv6": "http://[fd00::42]/status",
            "corp-host": "https://release.corp/status",
            "single-label-host": "https://intranet/status",
            "copied-provider-response": 'provider_response = {"private": true}',
            "copied-provider-output": '{"request_id":"req_private"}',
            "copied-provider-object": (
                '{"id":"evt_private","object":"event",'
                '"data":{"account":"acct_private"}}'
            ),
            "project-specific": "Apply this only to Quasar releases.",
        }

        for expected_rule, sample in unsafe_samples.items():
            with self.subTest(rule=expected_rule):
                violations = validator.scan_text(
                    Path("skills/orchestrate/SKILL.md"), sample
                )
                normalized_rule = {
                    "bearer-credential": "credential",
                    "slack-credential": "credential",
                    "google-credential": "credential",
                    "npm-credential": "credential",
                    "jwt-credential": "credential",
                    "generic-secret": "credential",
                    "private-email": "private-identifier",
                    "private-network": "internal-url",
                    "loopback": "internal-url",
                    "private-ipv6": "internal-url",
                    "corp-host": "internal-url",
                    "single-label-host": "internal-url",
                    "copied-provider-output": "copied-provider-response",
                    "copied-provider-object": "copied-provider-response",
                }.get(expected_rule, expected_rule)
                self.assertIn(
                    normalized_rule,
                    {item["rule"] for item in violations},
                )

    def test_orchestrate_rejects_bundled_provider_commands(self) -> None:
        validator = load_validator()

        violations = validator.scan_text(
            Path("skills/orchestrate/scripts/example.py"),
            'command = "gh issue view 42"',
        )

        self.assertIn(
            "bundled-provider-integration",
            {item["rule"] for item in violations},
        )

        for provider_code in (
            "import github",
            'url = "https://api.github.com/repos/example/release"',
            'command = "curl https://api.github.com/repos/example/release"',
        ):
            with self.subTest(provider_code=provider_code):
                violations = validator.scan_text(
                    Path("skills/orchestrate/scripts/example.py"),
                    provider_code,
                )
                self.assertIn(
                    "bundled-provider-integration",
                    {item["rule"] for item in violations},
                )

    def test_configured_integrations_stay_outside_the_coordination_kernel(
        self,
    ) -> None:
        outcomes = []
        for resolver in ("installed-tracker-a", "installed-tracker-b"):
            snapshot = prepared_snapshot()
            snapshot["repository"]["configured_integrations"] = {
                "tracker": {
                    "resolver": resolver,
                    "source": "installed-skill",
                    "approved": True,
                    "capability": "tracker",
                }
            }
            outcome = run_scenario(snapshot)
            self.assertNotIn(resolver, json.dumps(outcome))
            self.assertEqual(
                outcome["decisive_evidence"]["configured_integrations"],
                ["tracker"],
            )
            outcomes.append(outcome)

        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(outcomes[0]["decision"], "delegate")

    def test_validator_fails_closed_for_an_unsafe_public_skill(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "skills" / "unsafe-skill"
            (skill / "agents").mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: unsafe-skill\n"
                "description: Demonstrate a public release.\n---\n"
                "Connect to https://release.internal with "
                "api_key = " + "sk" + "-release-secret-value.\n",
                encoding="utf-8",
            )
            (skill / "agents" / "openai.yaml").write_text(
                "interface:\n"
                '  display_name: "Unsafe Skill"\n'
                '  short_description: "Unsafe fixture"\n'
                '  default_prompt: "Use $unsafe-skill."\n',
                encoding="utf-8",
            )

            completed = subprocess.run(
                [sys.executable, str(VALIDATOR), "--root", str(root)],
                capture_output=True,
                check=False,
                text=True,
            )

        self.assertEqual(completed.returncode, 1)
        report = json.loads(completed.stdout)
        self.assertIn(
            "credential", {item["rule"] for item in report["violations"]}
        )
        self.assertIn(
            "internal-url", {item["rule"] for item in report["violations"]}
        )

    def test_validator_reports_malformed_skill_metadata_as_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skills" / "missing-entrypoint").mkdir(parents=True)

            completed = subprocess.run(
                [sys.executable, str(VALIDATOR), "--root", str(root)],
                capture_output=True,
                check=False,
                text=True,
            )

        self.assertEqual(completed.returncode, 1)
        report = json.loads(completed.stdout)
        self.assertIn(
            "metadata", {item["rule"] for item in report["violations"]}
        )

    def test_sensitive_content_in_any_skill_file_type_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "skills" / "unsafe-skill"
            (skill / "agents").mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: unsafe-skill\n"
                "description: Demonstrate a public release.\n---\nSafe.\n",
                encoding="utf-8",
            )
            (skill / "agents" / "openai.yaml").write_text(
                "interface:\n"
                '  display_name: "Unsafe Skill"\n'
                '  short_description: "Unsafe fixture"\n'
                '  default_prompt: "Use $unsafe-skill."\n',
                encoding="utf-8",
            )
            (skill / "references").mkdir()
            (skill / "references" / "leak.txt").write_text(
                "Authorization: Bearer " + "gh" + "p_releaseSecret123\n",
                encoding="utf-8",
            )
            (skill / "assets").mkdir()
            (skill / "assets" / "opaque.bin").write_bytes(b"\x00private")

            completed = subprocess.run(
                [sys.executable, str(VALIDATOR), "--root", str(root)],
                capture_output=True,
                check=False,
                text=True,
            )

        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn(
            "credential", {item["rule"] for item in report["violations"]}
        )
        self.assertIn(
            "unscannable-binary",
            {item["rule"] for item in report["violations"]},
        )

    def test_every_public_skill_installs_by_name_in_an_isolated_project(
        self,
    ) -> None:
        environment = os.environ.copy()
        environment["NO_COLOR"] = "1"
        for skill_name in ("manage-public-presence", "orchestrate"):
            with self.subTest(skill=skill_name), tempfile.TemporaryDirectory() as (
                directory
            ):
                project = Path(directory)
                subprocess.run(
                    ["git", "init", "-q"],
                    cwd=project,
                    check=True,
                )
                completed = subprocess.run(
                    [
                        "npx",
                        "--yes",
                        "skills",
                        "add",
                        str(ROOT),
                        "--skill",
                        skill_name,
                        "--agent",
                        "codex",
                        "--copy",
                        "--yes",
                    ],
                    cwd=project,
                    capture_output=True,
                    check=True,
                    env=environment,
                    text=True,
                )

                installed = project / ".agents" / "skills" / skill_name
                self.assertTrue((installed / "SKILL.md").is_file())
                self.assertIn("Local path validated", completed.stdout)

    def test_cleanliness_gate_rejects_uncommitted_release_artifacts(self) -> None:
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
            subprocess.run(
                ["git", "config", "user.email", "release@example.test"],
                cwd=repository,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Release Test"],
                cwd=repository,
                check=True,
            )
            marker = repository / "tracked.txt"
            marker.write_text("tracked\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=repository, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "fixture"],
                cwd=repository,
                check=True,
            )
            self.assertEqual(validator.cleanliness_violations(repository), [])

            (repository / "release.tmp").write_text("generated\n", encoding="utf-8")
            violations = validator.cleanliness_violations(repository)

        self.assertEqual(
            {item["rule"] for item in violations},
            {"repository-cleanliness"},
        )


if __name__ == "__main__":
    unittest.main()
