from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = json.loads((ROOT / "tests" / "routing_scenarios.json").read_text(encoding="utf-8"))
PUBLIC_ROUTES = {"/ship", "/improve", "/navigate", "/manage-public-presence"}
IDENTITY_FIELDS = ("route", "objective", "scope", "authority", "exact_revision")
LOCAL_AID_FIELDS = {"name", "task_id", "outcome_gist", "state"}
DESTINATION_EVENTS = {
    "credential",
    "mfa",
    "permission_change",
    "scope_expansion",
    "consequential_approval",
}


def ask_jeevan_route(facts: dict[str, bool]) -> str:
    if any(
        facts.get(flag, False)
        for flag in ("live_wayfinding", "destination_uncertain", "multi_context", "lifecycle_rule_change")
    ):
        return "/navigate"
    if facts.get("exact_revision_campaign", False):
        return "/improve"
    if facts.get("controlled_public_identity", False):
        return "/manage-public-presence"
    if facts.get("bounded_code_outcome", False):
        return "/ship"
    return "/navigate"


def compatible(query: dict[str, object], candidate: dict[str, object]) -> bool:
    return all(query.get(field) == candidate.get(field) for field in IDENTITY_FIELDS)


def choose_transition(scenario: dict[str, object]) -> dict[str, str]:
    mode = str(scenario["mode"])
    query = dict(scenario["query"])
    candidates = [dict(candidate) for candidate in scenario["candidates"]]
    compatible_candidates = [candidate for candidate in candidates if compatible(query, candidate)]
    index_state = "native" if query.get("multi_context") else "none"

    conflicts = [candidate for candidate in compatible_candidates if candidate.get("conflict")]
    frontier = [
        candidate
        for candidate in compatible_candidates
        if candidate.get("takeable") and not candidate.get("conflict")
    ]

    if mode == "find":
        if query.get("multi_context") and query.get("task_creation_authorized"):
            selected = frontier[0] if frontier else compatible_candidates[0]
            return {
                "action": "establish-index",
                "selected_name": str(selected["name"]),
                "route_index": index_state,
            }
        if frontier:
            return {
                "action": "recommend",
                "selected_name": str(frontier[0]["name"]),
                "route_index": index_state,
            }
        if conflicts:
            return {
                "action": "block",
                "selected_name": str(conflicts[0]["name"]),
                "route_index": index_state,
            }
        return {"action": "question", "selected_name": "", "route_index": index_state}

    existing_frontier = [candidate for candidate in frontier if candidate.get("existing")]
    if existing_frontier:
        return {
            "action": "resume",
            "selected_name": str(existing_frontier[0]["name"]),
            "route_index": index_state,
        }
    if conflicts:
        return {
            "action": "block",
            "selected_name": str(conflicts[0]["name"]),
            "route_index": index_state,
        }
    new_frontier = [candidate for candidate in frontier if not candidate.get("existing")]
    if new_frontier and query.get("task_creation_authorized"):
        return {
            "action": "create",
            "selected_name": str(new_frontier[0]["name"]),
            "route_index": index_state,
        }
    return {"action": "block", "selected_name": "", "route_index": index_state}


def orchestrator_destination(case: dict[str, object]) -> str:
    if case.get("lifecycle_rule_change"):
        return "lightfastai/orchestrator"
    if case.get("exact_revision_campaign"):
        return "improve"
    return "unresolved"


def event_home(kind: str) -> str:
    return "destination" if kind in DESTINATION_EVENTS else "query"


class RoutingScenarioTests(unittest.TestCase):
    def test_ask_jeevan_composed_flow_recommendations(self) -> None:
        for scenario in SCENARIOS["ask_jeevan"]:
            with self.subTest(scenario=scenario["name"]):
                route = ask_jeevan_route(scenario["facts"])
                self.assertEqual(route, scenario["expected_route"])
                self.assertIn(route, PUBLIC_ROUTES)

    def test_navigate_frontier_and_duplicate_prevention(self) -> None:
        for scenario in SCENARIOS["navigate"]:
            with self.subTest(scenario=scenario["name"]):
                self.assertEqual(choose_transition(scenario), scenario["expected"])
                for candidate in scenario["candidates"]:
                    self.assertTrue(candidate["name"])
                    self.assertNotEqual(candidate["name"], candidate["task_id"])
                    self.assertRegex(candidate["url"], r"^https://")

    def test_orchestrator_lifecycle_precedence(self) -> None:
        for scenario in SCENARIOS["orchestrator_precedence"]:
            with self.subTest(scenario=scenario["name"]):
                self.assertEqual(orchestrator_destination(scenario), scenario["expected_destination"])

    def test_route_index_and_consent_bound_local_aid(self) -> None:
        for scenario in SCENARIOS["route_index"]:
            with self.subTest(scenario=scenario["name"]):
                native_index = bool(scenario["multi_context"])
                local_aid = native_index and bool(scenario["local_consent"])
                self.assertEqual(native_index, scenario["expected_native_index"])
                self.assertEqual(local_aid, scenario["expected_local_aid"])
                if "local_entry" in scenario:
                    valid = set(scenario["local_entry"]) == LOCAL_AID_FIELDS
                    self.assertEqual(valid, scenario["expected_local_entry_valid"])

    def test_route_index_history_is_append_only(self) -> None:
        history = SCENARIOS["route_index_history"]
        events = list(history["events"])
        prior_events = events[:-1]
        prior_snapshot = [dict(event) for event in prior_events]
        updated_events = [*prior_events, events[-1]]

        self.assertEqual(prior_events, prior_snapshot)
        self.assertEqual(updated_events[: len(prior_events)], prior_snapshot)
        self.assertEqual(len(updated_events), history["expected_event_count"])
        self.assertEqual(updated_events[-1]["state"], history["expected_latest_state"])
        self.assertTrue(history["task_id"])

    def test_query_return_and_destination_approval_boundaries(self) -> None:
        for scenario in SCENARIOS["return_events"]:
            with self.subTest(scenario=scenario["name"]):
                kind = scenario["kind"]
                if kind == "result":
                    reconciled = bool(scenario["intent_matches"] and scenario["native_evidence"])
                    self.assertEqual(reconciled, scenario["expected_reconciled"])
                else:
                    self.assertEqual(event_home(kind), scenario["expected_home"])

    def test_skill_bodies_preserve_the_required_runtime_invariants(self) -> None:
        navigate = (ROOT / "skills" / "navigate" / "SKILL.md").read_text(encoding="utf-8").lower()
        ask_jeevan = (ROOT / "skills" / "ask-jeevan" / "SKILL.md").read_text(encoding="utf-8").lower()

        navigate_concepts = (
            "destination",
            "route; do not own",
            "human-readable name",
            "native identities",
            "route index",
            "append-only",
            "frontier",
            "takeable",
            "resumable",
            "routing fog",
            "not yet specified",
            "out of scope",
            "~/.codex/query/routes.md",
            "explicit user consent",
            "one bounded routing transition",
            "find a route",
            "advance a route",
            "scope expansion",
            "lightfastai/orchestrator",
            "workbench or orchestrator map",
            "native completion evidence",
        )
        ask_invariants = (
            "stateless",
            "performs no effect",
            "return exactly these three lines",
        )

        for concept in navigate_concepts:
            self.assertIn(concept, navigate, concept)
        for concept in ask_invariants:
            self.assertIn(concept, ask_jeevan, concept)

        ask_routes = set(re.findall(r"`(/[a-z][a-z0-9-]*)`", ask_jeevan))
        self.assertEqual(ask_routes, PUBLIC_ROUTES)
        self.assertNotIn("ask matt", ask_jeevan)
        self.assertNotIn("matt pocock", ask_jeevan)


if __name__ == "__main__":
    unittest.main()
