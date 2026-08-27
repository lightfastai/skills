from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = json.loads((ROOT / "tests" / "routing_scenarios.json").read_text(encoding="utf-8"))
PUBLIC_ROUTES = {"/ship", "/improve", "/manage-public-presence"}
DESTINATION_EVENTS = {
    "credential",
    "mfa",
    "permission_change",
    "scope_expansion",
    "consequential_approval",
}


def ask_jeevan_route(facts: dict[str, bool]) -> str:
    if facts.get("exact_revision_campaign", False):
        return "/improve"
    if facts.get("controlled_public_identity", False):
        return "/manage-public-presence"
    if facts.get("bounded_code_outcome", False):
        return "/ship"
    raise ValueError("No matching public outcome route")






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


    def test_orchestrator_lifecycle_precedence(self) -> None:
        for scenario in SCENARIOS["orchestrator_precedence"]:
            with self.subTest(scenario=scenario["name"]):
                self.assertEqual(orchestrator_destination(scenario), scenario["expected_destination"])



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
        ask_jeevan = (ROOT / "skills" / "ask-jeevan" / "SKILL.md").read_text(encoding="utf-8").lower()

        ask_invariants = (
            "stateless",
            "performs no effect",
            "return exactly these three lines",
        )

        for concept in ask_invariants:
            self.assertIn(concept, ask_jeevan, concept)

        ask_routes = set(re.findall(r"`(/[a-z][a-z0-9-]*)`", ask_jeevan))
        self.assertEqual(ask_routes, PUBLIC_ROUTES)
        self.assertNotIn("ask matt", ask_jeevan)
        self.assertNotIn("matt pocock", ask_jeevan)


if __name__ == "__main__":
    unittest.main()
