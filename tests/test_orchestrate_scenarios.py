import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACER = ROOT / "skills" / "orchestrate" / "scripts" / "trace.py"


def run_scenario(snapshot: dict) -> dict:
    completed = subprocess.run(
        [sys.executable, str(TRACER)],
        input=json.dumps(snapshot),
        capture_output=True,
        check=True,
        text=True,
    )
    return json.loads(completed.stdout)


def prepared_snapshot(intent: str = "coordinate", programme_state: str = "active") -> dict:
    return {
        "repository": {"coordination_only": True},
        "programme": {"issue": 41, "state": programme_state},
        "tickets": [
            {
                "issue": 42,
                "title": "Add audit log",
                "state": "ready",
                "blocked_by": [],
            }
        ],
        "tasks": [],
        "user_instruction": {"intent": intent},
    }


class OrchestrateScenarios(unittest.TestCase):
    def test_ready_ticket_produces_one_bounded_ask_matt_delegation(self) -> None:
        outcome = run_scenario(prepared_snapshot())

        self.assertEqual(outcome["decision"], "delegate")
        self.assertEqual(outcome["selected_ticket"], 42)
        self.assertEqual(len(outcome["requested_effects"]), 1)

        delegation = outcome["requested_effects"][0]
        self.assertEqual(delegation["effect"], "delegate")
        self.assertEqual(delegation["router"], "ask-matt")
        self.assertEqual(delegation["programme"], 41)
        self.assertEqual(delegation["issue"], 42)
        self.assertTrue(delegation["fresh_task"])
        self.assertEqual(delegation["scope"]["issues"], [42])
        self.assertFalse(outcome["root_mutation_permitted"])

    def test_direct_implementation_request_is_refused_with_delegated_next_action(
        self,
    ) -> None:
        outcome = run_scenario(prepared_snapshot(intent="implement"))

        self.assertEqual(outcome["decision"], "refuse-and-delegate")
        self.assertEqual(outcome["root_request"], "refused")
        self.assertEqual(outcome["selected_ticket"], 42)
        self.assertEqual(len(outcome["requested_effects"]), 1)
        self.assertEqual(outcome["requested_effects"][0]["router"], "ask-matt")
        self.assertFalse(outcome["root_mutation_permitted"])

    def test_non_active_programme_stops_without_delegation(self) -> None:
        outcome = run_scenario(prepared_snapshot(programme_state="waiting"))

        self.assertEqual(outcome["decision"], "stop")
        self.assertEqual(outcome["reason"], "no-active-programme")
        self.assertIsNone(outcome["selected_ticket"])
        self.assertEqual(outcome["requested_effects"], [])
        self.assertFalse(outcome["root_mutation_permitted"])


if __name__ == "__main__":
    unittest.main()
