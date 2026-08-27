from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Optional

from scripts.validate_routing_skills import PUBLIC_SKILLS, Validation, validate_links


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = json.loads((ROOT / "tests" / "routing_scenarios.json").read_text(encoding="utf-8"))
CORE_CAPABILITIES = {f"${name}" for name in PUBLIC_SKILLS if name != "ask-jeevan"}
IDENTITY_FIELDS = (
    "route",
    "objective",
    "scope",
    "authority",
    "exact_revision",
    "query_id",
    "destination_id",
    "native_artifacts",
)
LOCAL_AID_FIELDS = {"name", "task_id", "outcome_gist", "state"}
DESTINATION_EVENTS = {
    "credential",
    "mfa",
    "permission_change",
    "scope_expansion",
    "consequential_approval",
}


def compatible(query: dict[str, object], candidate: dict[str, object]) -> bool:
    """Compare only identities the Query has resolved; Find may begin without a route."""
    return all(
        query.get(field) in (None, "", []) or query.get(field) == candidate.get(field)
        for field in IDENTITY_FIELDS
    )


def selected_candidate(scenario: dict[str, object]) -> Optional[dict[str, object]]:
    selected_name = scenario["expected"]["selected_name"]
    if not selected_name:
        return None
    matches = [candidate for candidate in scenario["candidates"] if candidate["name"] == selected_name]
    if len(matches) != 1:
        return None
    return matches[0]


class RoutingScenarioTests(unittest.TestCase):
    def test_ask_jeevan_contract_covers_conversation_capabilities_and_routes(self) -> None:
        seen_core_capabilities = {
            scenario["expected"]["recommendations"][0]
            for scenario in SCENARIOS["ask_jeevan"]
            if scenario["expected"]["recommendations"]
            and scenario["expected"]["recommendations"][0] in CORE_CAPABILITIES
        }
        self.assertEqual(seen_core_capabilities, CORE_CAPABILITIES)
        seen_specialist_capabilities = {
            scenario["expected"]["recommendations"][0]
            for scenario in SCENARIOS["ask_jeevan"]
            if scenario["expected"]["recommendations"]
            and scenario["expected"]["recommendations"][0] not in CORE_CAPABILITIES
        }
        self.assertTrue(seen_specialist_capabilities)
        self.assertTrue(
            all(capability.startswith("$") for capability in seen_specialist_capabilities)
        )

        for scenario in SCENARIOS["ask_jeevan"]:
            with self.subTest(scenario=scenario["name"]):
                facts = scenario["facts"]
                expected = scenario["expected"]
                recommendations = expected["recommendations"]

                self.assertTrue(scenario["message"].strip())
                self.assertIn(
                    expected["action"],
                    {"conversation", "question", "recommend", "availability-gap"},
                )
                self.assertLessEqual(len(recommendations), 1)
                self.assertEqual(expected["action"] == "recommend", len(recommendations) == 1)

                if recommendations:
                    self.assertIn(
                        recommendations[0].removeprefix("$"),
                        scenario["available_capabilities"],
                    )

                if facts.get("greeting") or facts.get("ordinary_question"):
                    self.assertEqual(expected["action"], "conversation")
                if facts.get("materially_ambiguous"):
                    self.assertEqual(expected["action"], "question")
                    self.assertNotIn("$navigate", recommendations)
                if facts.get("lifecycle_rule_change") or facts.get("operational_wayfinding"):
                    self.assertEqual(recommendations, ["$navigate"])
                if facts.get("controlled_public_identity") and not facts.get("operational_wayfinding"):
                    self.assertEqual(recommendations, ["$manage-public-presence"])
                if facts.get("exact_revision_campaign") and not facts.get("lifecycle_rule_change"):
                    self.assertEqual(recommendations, ["$improve"])
                if facts.get("bounded_code_outcome") and len(facts) == 1:
                    if "ship" in scenario["available_capabilities"]:
                        self.assertEqual(recommendations, ["$ship"])
                    else:
                        self.assertEqual(expected["action"], "availability-gap")
                        self.assertEqual(expected["named_route"], "/ship")
                if facts.get("research_request"):
                    if "research" in scenario["available_capabilities"]:
                        self.assertEqual(recommendations, ["$research"])
                    else:
                        self.assertEqual(expected["action"], "availability-gap")
                if facts.get("exploratory_idea"):
                    self.assertEqual(recommendations, ["$grill-me"])
                if facts.get("question_shaped"):
                    self.assertEqual(expected["action"], "recommend")

    def test_navigate_scenarios_satisfy_frontier_invariants(self) -> None:
        allowed_actions = {"recommend", "establish-index", "resume", "create", "block", "question"}

        for scenario in SCENARIOS["navigate"]:
            with self.subTest(scenario=scenario["name"]):
                query = scenario["query"]
                expected = scenario["expected"]
                action = expected["action"]
                selected = selected_candidate(scenario)
                compatible_candidates = [
                    candidate for candidate in scenario["candidates"] if compatible(query, candidate)
                ]
                compatible_existing = [
                    candidate
                    for candidate in compatible_candidates
                    if candidate["existing"] and candidate["takeable"] and not candidate["conflict"]
                ]

                self.assertIn(action, allowed_actions)
                self.assertEqual(
                    expected["route_index"],
                    "native" if query["continuity_warrants_index"] else "none",
                )
                for candidate in scenario["candidates"]:
                    self.assertTrue(candidate["name"])
                    self.assertNotEqual(candidate["name"], candidate["task_id"])
                    self.assertTrue(candidate["url"].startswith("https://"))

                if action != "question":
                    self.assertIsNotNone(selected)
                    self.assertTrue(compatible(query, selected))

                if action == "resume":
                    self.assertTrue(selected["existing"] and selected["takeable"])
                    self.assertFalse(selected["conflict"])
                    self.assertEqual(selected, compatible_existing[0])
                elif action == "create":
                    self.assertFalse(selected["existing"])
                    self.assertTrue(selected["takeable"] and query["task_creation_authorized"])
                    self.assertFalse(
                        any(candidate["existing"] for candidate in compatible_candidates)
                    )
                    self.assertFalse(any(candidate["conflict"] for candidate in compatible_candidates))
                elif action == "block":
                    blocked_existing = bool(
                        selected["existing"]
                        and not selected["takeable"]
                        and selected.get("reopening_condition")
                    )
                    self.assertTrue(
                        selected["conflict"] or blocked_existing or not query["task_creation_authorized"]
                    )
                elif action == "recommend":
                    self.assertEqual(scenario["mode"], "find")
                    self.assertTrue(selected["takeable"] and not selected["conflict"])
                    self.assertFalse(query["continuity_warrants_index"])
                elif action == "establish-index":
                    self.assertEqual(scenario["mode"], "find")
                    self.assertTrue(query["continuity_warrants_index"])
                    self.assertTrue(query["task_creation_authorized"])

    def test_conversation_task_locator_preserves_surface_and_search_bounds(self) -> None:
        for scenario in SCENARIOS["conversation_task_locator"]:
            with self.subTest(scenario=scenario["name"]):
                request = scenario["request"]
                requested_surface = request["surface"]
                requested_partitions = request["partitions"]
                requested_access = scenario["surface_access"].get(requested_surface, {})
                accessible_partitions = [
                    partition
                    for partition in requested_partitions
                    if requested_access.get(partition, False)
                ]
                expected = scenario["expected"]
                calls = scenario["calls"]
                tool_schema = scenario["tool_schema"]

                for call in calls:
                    self.assertEqual(
                        call["surface"],
                        requested_surface,
                        "an adjacent native surface must never substitute for the requested one",
                    )
                    self.assertEqual(call["project"], request["project"])
                    self.assertIn(call["partition"], accessible_partitions)
                    if tool_schema["max_results"] is not None:
                        self.assertLessEqual(call["limit"], tool_schema["max_results"])

                successful_calls = [call for call in calls if "error" not in call["response"]]
                exhaustive_traversal_established = not request["all"]
                if (
                    request["all"]
                    and tool_schema["supports_cursor"]
                    and len(accessible_partitions) == len(requested_partitions)
                ):
                    exhaustive_traversal_established = True
                    for partition in requested_partitions:
                        partition_calls = [
                            call for call in successful_calls if call["partition"] == partition
                        ]
                        if not partition_calls or partition_calls[0]["cursor"] is not None:
                            exhaustive_traversal_established = False
                            continue

                        expected_cursor = None
                        for call in partition_calls:
                            if call["cursor"] != expected_cursor:
                                exhaustive_traversal_established = False
                            expected_cursor = call["response"]["next_cursor"]
                        if expected_cursor is not None:
                            exhaustive_traversal_established = False

                if not accessible_partitions:
                    self.assertEqual(expected["action"], "bounded-unavailable")
                    self.assertEqual(calls, [])
                    self.assertTrue(expected["partial"])
                else:
                    self.assertEqual(expected["action"], "report")
                    self.assertEqual(
                        expected["partial"],
                        len(accessible_partitions) != len(requested_partitions)
                        or (request["all"] and not exhaustive_traversal_established),
                    )
                    if (
                        request["all"]
                        and len(accessible_partitions) == len(requested_partitions)
                        and not tool_schema["supports_cursor"]
                    ):
                        self.assertTrue(expected["partial"])

                candidates = {candidate["id"]: candidate for candidate in scenario["candidates"]}
                self.assertEqual(len(candidates), len(scenario["candidates"]))
                for candidate in candidates.values():
                    self.assertTrue(candidate["name"])
                    self.assertNotEqual(candidate["name"], candidate["id"])
                    self.assertTrue(candidate["match_evidence"]["text"].strip())
                found_ids: list[str] = []
                for call in successful_calls:
                    for item_id in call["response"]["item_ids"]:
                        self.assertIn(item_id, candidates)
                        if item_id not in found_ids:
                            found_ids.append(item_id)

                direct_user_matches = [
                    item_id
                    for item_id in found_ids
                    if candidates[item_id]["metadata_match"]
                    and candidates[item_id]["match_evidence"]["role"] == "user"
                    and candidates[item_id]["match_evidence"]["source"] == "native_message"
                ]
                if request["requires_explicit_user_message"]:
                    self.assertEqual(expected["selected_ids"], direct_user_matches)
                self.assertEqual(
                    len(expected["selected_ids"]), len(set(expected["selected_ids"]))
                )

                for index, call in enumerate(calls):
                    response = call["response"]
                    if response.get("error") == "limit_exceeded":
                        self.assertLess(index + 1, len(calls))
                        corrected = calls[index + 1]
                        self.assertEqual(corrected["surface"], call["surface"])
                        self.assertEqual(corrected["project"], call["project"])
                        self.assertEqual(corrected["partition"], call["partition"])
                        self.assertEqual(corrected["cursor"], call["cursor"])
                        self.assertLessEqual(corrected["limit"], response["max_results"])
                        self.assertLess(corrected["limit"], call["limit"])

    def test_orchestrator_lifecycle_precedence(self) -> None:
        for scenario in SCENARIOS["orchestrator_precedence"]:
            with self.subTest(scenario=scenario["name"]):
                if scenario["lifecycle_rule_change"]:
                    self.assertEqual(scenario["expected_destination"], "lightfastai/orchestrator")
                elif scenario["exact_revision_campaign"]:
                    self.assertEqual(scenario["expected_destination"], "improve")

    def test_route_index_and_optional_consent_bound_local_aid(self) -> None:
        for scenario in SCENARIOS["route_index"]:
            with self.subTest(scenario=scenario["name"]):
                native_index = bool(scenario["continuity_warrants_index"])
                local_aid = bool(
                    native_index and scenario["local_consent"] and scenario["local_aid_selected"]
                )
                self.assertEqual(native_index, scenario["expected_native_index"])
                self.assertEqual(local_aid, scenario["expected_local_aid"])
                if native_index:
                    self.assertTrue(scenario["multi_context"])
                if "local_entry" in scenario:
                    valid = set(scenario["local_entry"]) == LOCAL_AID_FIELDS
                    self.assertEqual(valid, scenario["expected_local_entry_valid"])

    def test_route_index_history_is_append_only(self) -> None:
        history = SCENARIOS["route_index_history"]
        prior_events = history["prior_events"]
        after_append = history["after_append"]
        observation_ids = [event["observation_id"] for event in after_append]

        self.assertEqual(after_append[: len(prior_events)], prior_events)
        self.assertEqual(len(after_append), history["expected_event_count"])
        self.assertEqual(len(observation_ids), len(set(observation_ids)))
        self.assertEqual(after_append[-1]["state"], history["expected_latest_state"])
        self.assertTrue(history["task_id"])

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
