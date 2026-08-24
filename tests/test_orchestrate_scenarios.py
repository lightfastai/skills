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


def run_invalid_scenario(snapshot: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TRACER)],
        input=json.dumps(snapshot),
        capture_output=True,
        check=False,
        text=True,
    )


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


def durable_snapshot(current_checkpoint: dict, **overrides: object) -> dict:
    snapshot = {
        "repository": {
            "coordination_only": True,
            "contract": {"runtime_state": "ignored"},
            "branches": [],
            "main": {"verified_commit": None},
        },
        "tracker": {
            "programmes": [
                {
                    "issue": 6,
                    "state": "active",
                    "current_ticket": 8,
                    "tickets": [7, 8],
                },
            ],
            "tickets": [
                {
                    "issue": 7,
                    "state": "closed",
                    "checkpoint_comments": [
                        {
                            "id": "checkpoint-comment-7",
                            "checkpoint": checkpoint(
                                state="done",
                                verified_commit="prior123",
                                next_action="advance to issue #8",
                                updated_at="2026-08-24T10:12:00Z",
                            ),
                        }
                    ],
                },
                {
                    "issue": 8,
                    "state": "open",
                    "checkpoint_comments": [
                        {
                            "id": "checkpoint-comment-8",
                            "checkpoint": current_checkpoint,
                        }
                    ],
                }
            ],
        },
        "tasks": [],
        "pull_requests": [],
        "chat_history": None,
        "user_instruction": {"intent": "coordinate"},
    }
    snapshot.update(overrides)
    return snapshot


def checkpoint(**overrides: object) -> dict:
    value = {
        "version": 1,
        "state": "ready",
        "task_id": None,
        "branch": None,
        "pull_request": None,
        "attempt": 1,
        "verified_commit": None,
        "blocker": None,
        "next_action": "delegate issue #8",
        "updated_at": "2026-08-24T10:00:00Z",
    }
    value.update(overrides)
    return value


def completed_snapshot(
    *,
    acceptance_checked: bool = True,
    verification_evidence_recorded: bool = True,
) -> dict:
    snapshot = durable_snapshot(
        checkpoint(
            state="active",
            branch="feat/issue-8-durable-recovery",
            pull_request="https://example.test/pulls/18",
        )
    )
    snapshot["repository"]["main"] = {
        "verified_commit": "abc123",
        "verified_at": "2026-08-24T10:10:00Z",
        "verification_evidence_recorded": verification_evidence_recorded,
    }
    current_ticket = next(
        ticket for ticket in snapshot["tracker"]["tickets"] if ticket["issue"] == 8
    )
    current_ticket.update(
        {
            "state": "closed",
            "closed_at": "2026-08-24T10:11:00Z",
            "acceptance_criteria_checked": acceptance_checked,
        }
    )
    snapshot["pull_requests"] = [
        {
            "issue": 8,
            "url": "https://example.test/pulls/18",
            "branch": "feat/issue-8-durable-recovery",
            "state": "merged",
            "merge_commit": "abc123",
            "updated_at": "2026-08-24T10:09:00Z",
        }
    ]
    return snapshot


class OrchestrateScenarios(unittest.TestCase):
    def test_fresh_task_recovers_ready_programme_from_tracker_without_chat(self) -> None:
        outcome = run_scenario(durable_snapshot(checkpoint()))

        self.assertEqual(outcome["decision"], "recover")
        self.assertEqual(outcome["programme"], 6)
        self.assertEqual(outcome["ticket"], 8)
        self.assertEqual(outcome["lifecycle_state"], "ready")
        self.assertEqual(outcome["checkpoint_comment"], "checkpoint-comment-8")
        self.assertEqual(outcome["conflicts"], [])
        self.assertEqual(outcome["requested_effects"], [])
        self.assertFalse(outcome["root_mutation_permitted"])

    def test_checkpoint_rejects_unrecognized_fields_instead_of_republishing(
        self,
    ) -> None:
        unsafe_checkpoint = checkpoint(secret="must-not-be-copied")

        completed = run_invalid_scenario(durable_snapshot(unsafe_checkpoint))

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stderr, "invalid orchestration snapshot\n")
        self.assertNotIn("must-not-be-copied", completed.stderr)

    def test_checkpoint_rejects_unknown_lifecycle_state(self) -> None:
        completed = run_invalid_scenario(
            durable_snapshot(checkpoint(state="complete-ish"))
        )

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stderr, "invalid orchestration snapshot\n")

    def test_malformed_timestamp_is_rejected_without_private_diagnostics(self) -> None:
        completed = run_invalid_scenario(
            durable_snapshot(checkpoint(updated_at={"private": "value"}))
        )

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stderr, "invalid orchestration snapshot\n")
        self.assertNotIn(str(ROOT), completed.stderr)
        self.assertNotIn("private", completed.stderr)

    def test_newer_live_task_recovers_active_and_updates_checkpoint_in_place(
        self,
    ) -> None:
        tasks = [
            {
                "id": "task-8",
                "issue": 8,
                "state": "running",
                "branch": "feat/issue-8-durable-recovery",
                "next_action": "watch task-8",
                "updated_at": "2026-08-24T10:05:00Z",
            }
        ]

        outcome = run_scenario(
            durable_snapshot(
                checkpoint(
                    state="waiting",
                    blocker="task was temporarily unavailable",
                    next_action="retry task-8",
                ),
                tasks=tasks,
            )
        )

        self.assertEqual(outcome["lifecycle_state"], "active")
        self.assertEqual(outcome["checkpoint"]["task_id"], "task-8")
        self.assertEqual(
            outcome["checkpoint"]["branch"],
            "feat/issue-8-durable-recovery",
        )
        self.assertEqual(outcome["checkpoint"]["updated_at"], tasks[0]["updated_at"])
        self.assertIsNone(outcome["checkpoint"]["blocker"])
        self.assertEqual(outcome["checkpoint"]["next_action"], "watch task-8")
        self.assertEqual(outcome["conflicts"], [])
        self.assertEqual(
            outcome["requested_effects"],
            [
                {
                    "effect": "update-checkpoint",
                    "comment_id": "checkpoint-comment-8",
                    "checkpoint": outcome["checkpoint"],
                }
            ],
        )

    def test_reconciliation_compares_rfc3339_instants_not_timestamp_text(self) -> None:
        tasks = [
            {
                "id": "task-older",
                "issue": 8,
                "state": "running",
                "branch": "feat/older-task",
                "updated_at": "2026-08-24T10:00:00+01:00",
            },
            {
                "id": "task-newer",
                "issue": 8,
                "state": "running",
                "branch": "feat/issue-8-durable-recovery",
                "updated_at": "2026-08-24T09:30:00Z",
            }
        ]

        outcome = run_scenario(
            durable_snapshot(
                checkpoint(updated_at="2026-08-24T10:00:00+01:00"),
                tasks=tasks,
            )
        )

        self.assertEqual(outcome["lifecycle_state"], "active")
        self.assertEqual(outcome["checkpoint"]["task_id"], "task-newer")
        self.assertEqual(outcome["checkpoint"]["updated_at"], tasks[1]["updated_at"])

    def test_newer_failed_task_recovers_waiting_with_durable_blocker(self) -> None:
        tasks = [
            {
                "id": "task-8",
                "issue": 8,
                "state": "failed",
                "branch": "feat/issue-8-durable-recovery",
                "blocker": "required repository permission is unavailable",
                "next_action": "request repository permission",
                "updated_at": "2026-08-24T10:06:00Z",
            }
        ]

        outcome = run_scenario(
            durable_snapshot(
                checkpoint(state="active", task_id="task-8"),
                tasks=tasks,
            )
        )

        self.assertEqual(outcome["lifecycle_state"], "waiting")
        self.assertEqual(
            outcome["checkpoint"]["blocker"],
            "required repository permission is unavailable",
        )
        self.assertEqual(
            outcome["checkpoint"]["next_action"],
            "request repository permission",
        )
        self.assertEqual(
            outcome["requested_effects"][0]["comment_id"],
            "checkpoint-comment-8",
        )

    def test_newer_branch_and_pull_request_win_without_hiding_conflicts(self) -> None:
        stale = checkpoint(
            state="active",
            branch="feat/old-recovery",
            pull_request="https://example.test/pulls/old",
        )
        repository = {
            "coordination_only": True,
            "contract": {"runtime_state": "ignored"},
            "branches": [
                {
                    "issue": 8,
                    "name": "feat/issue-8-durable-recovery",
                    "updated_at": "2026-08-24T10:07:00Z",
                }
            ],
            "main": {"verified_commit": None},
        }
        pull_requests = [
            {
                "issue": 8,
                "url": "https://example.test/pulls/18",
                "branch": "feat/issue-8-durable-recovery",
                "state": "open",
                "updated_at": "2026-08-24T10:08:00Z",
            }
        ]

        outcome = run_scenario(
            durable_snapshot(
                stale,
                repository=repository,
                pull_requests=pull_requests,
            )
        )

        self.assertEqual(outcome["lifecycle_state"], "active")
        self.assertEqual(
            outcome["checkpoint"]["branch"],
            "feat/issue-8-durable-recovery",
        )
        self.assertEqual(
            outcome["checkpoint"]["pull_request"],
            "https://example.test/pulls/18",
        )
        self.assertEqual(
            outcome["conflicts"],
            [
                {
                    "field": "branch",
                    "resolution": "live-newer",
                },
                {
                    "field": "pull_request",
                    "resolution": "live-newer",
                },
            ],
        )

    def test_older_live_conflict_is_reported_without_replacing_checkpoint(self) -> None:
        durable = checkpoint(
            state="active",
            branch="feat/checkpoint-branch",
            updated_at="2026-08-24T10:10:00Z",
        )
        repository = {
            "coordination_only": True,
            "contract": {"runtime_state": "ignored"},
            "branches": [
                {
                    "issue": 8,
                    "name": "feat/older-live-branch",
                    "updated_at": "2026-08-24T10:05:00Z",
                }
            ],
            "main": {"verified_commit": None},
        }

        outcome = run_scenario(
            durable_snapshot(durable, repository=repository)
        )

        self.assertEqual(outcome["checkpoint"]["branch"], "feat/checkpoint-branch")
        self.assertEqual(
            outcome["conflicts"],
            [
                {
                    "field": "branch",
                    "resolution": "checkpoint-newer",
                }
            ],
        )
        self.assertEqual(outcome["requested_effects"], [])

    def test_checkpoint_cannot_claim_done_without_live_completion_proof(self) -> None:
        outcome = run_scenario(
            durable_snapshot(
                checkpoint(
                    state="done",
                    verified_commit="stale123",
                    next_action="none",
                )
            )
        )

        self.assertEqual(outcome["lifecycle_state"], "waiting")
        self.assertEqual(
            outcome["conflicts"],
            [{"field": "state", "resolution": "live-evidence-required"}],
        )
        self.assertIsNotNone(outcome["checkpoint"]["blocker"])
        self.assertEqual(
            outcome["requested_effects"][0]["comment_id"],
            "checkpoint-comment-8",
        )

    def test_newer_done_checkpoint_is_confirmed_by_older_live_completion_proof(
        self,
    ) -> None:
        snapshot = completed_snapshot()
        current_ticket = next(
            ticket
            for ticket in snapshot["tracker"]["tickets"]
            if ticket["issue"] == 8
        )
        current_ticket["checkpoint_comments"][0]["checkpoint"] = checkpoint(
            state="done",
            branch="feat/issue-8-durable-recovery",
            pull_request="https://example.test/pulls/18",
            verified_commit="abc123",
            next_action="none",
            updated_at="2026-08-24T10:12:00Z",
        )

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["lifecycle_state"], "done")
        self.assertEqual(outcome["conflicts"], [])
        self.assertEqual(outcome["requested_effects"], [])

    def test_newer_completion_proof_corrects_stale_done_checkpoint(self) -> None:
        snapshot = completed_snapshot()
        current_ticket = next(
            ticket
            for ticket in snapshot["tracker"]["tickets"]
            if ticket["issue"] == 8
        )
        current_ticket["checkpoint_comments"][0]["checkpoint"] = checkpoint(
            state="done",
            branch="feat/issue-8-durable-recovery",
            pull_request="https://example.test/pulls/18",
            verified_commit="stale123",
            next_action="none",
        )

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["lifecycle_state"], "done")
        self.assertEqual(outcome["checkpoint"]["verified_commit"], "abc123")
        self.assertIn(
            {"field": "verified_commit", "resolution": "live-newer"},
            outcome["conflicts"],
        )

    def test_merged_closed_and_verified_evidence_recovers_done(self) -> None:
        outcome = run_scenario(completed_snapshot())

        self.assertEqual(outcome["lifecycle_state"], "done")
        self.assertEqual(outcome["checkpoint"]["verified_commit"], "abc123")
        self.assertIsNone(outcome["checkpoint"]["blocker"])
        self.assertEqual(outcome["checkpoint"]["next_action"], "none")
        self.assertEqual(
            outcome["checkpoint"]["updated_at"],
            "2026-08-24T10:11:00Z",
        )
        self.assertEqual(
            outcome["requested_effects"][0]["comment_id"],
            "checkpoint-comment-8",
        )

    def test_completion_without_acceptance_and_verification_records_stays_active(
        self,
    ) -> None:
        outcome = run_scenario(
            completed_snapshot(
                acceptance_checked=False,
                verification_evidence_recorded=False,
            )
        )

        self.assertEqual(outcome["lifecycle_state"], "active")
        self.assertIsNone(outcome["checkpoint"]["verified_commit"])

    def test_null_commits_cannot_prove_completion(self) -> None:
        snapshot = completed_snapshot()
        snapshot["repository"]["main"]["verified_commit"] = None
        snapshot["pull_requests"][0]["merge_commit"] = None

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["lifecycle_state"], "active")
        self.assertIsNone(outcome["checkpoint"]["verified_commit"])

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
