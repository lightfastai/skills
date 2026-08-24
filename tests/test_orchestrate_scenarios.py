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


def prepared_snapshot(intent: str = "implementation", programme_state: str = "active") -> dict:
    return {
        "repository": {
            "coordination_only": True,
            "isolated_workspaces": True,
        },
        "programme": {
            "issue": 41,
            "state": programme_state,
            "approved_order": [42],
        },
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


def active_work_snapshot(task: dict, **overrides: object) -> dict:
    current = checkpoint(
        state="active",
        task_id="task-8",
        branch="feat/issue-8-durable-recovery",
        pull_request="https://example.test/pulls/18",
        next_action="watch task-8",
    )
    snapshot = durable_snapshot(current, tasks=[task])
    snapshot["repository"]["branches"] = [
        {
            "issue": 8,
            "name": current["branch"],
            "head_commit": "abc123",
            "updated_at": current["updated_at"],
        }
    ]
    snapshot["pull_requests"] = [
        {
            "issue": 8,
            "url": current["pull_request"],
            "branch": current["branch"],
            "state": "open",
            "head_commit": "abc123",
            "checks_state": "pending",
            "updated_at": current["updated_at"],
        }
    ]
    snapshot.update(overrides)
    return snapshot


class OrchestrateScenarios(unittest.TestCase):
    def test_active_work_uses_native_waits_without_noisy_notification(self) -> None:
        outcome = run_scenario(
            active_work_snapshot(
                {
                    "id": "task-8",
                    "issue": 8,
                    "state": "running",
                    "resumable": True,
                    "native_wait": {"after_cursor": "task-event-17"},
                    "elapsed_seconds": 864000,
                    "updated_at": "2026-08-24T10:00:00Z",
                }
            )
        )

        self.assertEqual(outcome["decision"], "watch")
        self.assertEqual(
            outcome["requested_effects"],
            [
                {
                    "effect": "wait-task",
                    "task_id": "task-8",
                    "after_cursor": "task-event-17",
                },
                {
                    "effect": "watch-repository-checks",
                    "pull_request": "https://example.test/pulls/18",
                    "head_commit": "abc123",
                },
            ],
        )
        self.assertEqual(outcome["notifications"], [])
        self.assertFalse(outcome["stale"])

    def test_first_failure_resumes_the_original_task(self) -> None:
        snapshot = active_work_snapshot(
            {
                "id": "task-8",
                "issue": 8,
                "state": "failed",
                "resumable": True,
                "failure": "execution host stopped unexpectedly",
                "blocker": "execution host stopped unexpectedly",
                "next_action": "recover task-8",
                "updated_at": "2026-08-24T10:05:00Z",
            }
        )
        snapshot["observed_at"] = "2026-08-24T10:06:00Z"

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "recover-task")
        self.assertEqual(outcome["lifecycle_state"], "active")
        self.assertEqual(outcome["checkpoint"]["attempt"], 2)
        self.assertEqual(outcome["checkpoint"]["task_id"], "task-8")
        self.assertEqual(
            outcome["requested_effects"],
            [
                {
                    "effect": "update-checkpoint",
                    "comment_id": "checkpoint-comment-8",
                    "checkpoint": outcome["checkpoint"],
                },
                {
                    "effect": "resume-task",
                    "task_id": "task-8",
                    "issue": 8,
                    "reuse": {
                        "checkpoint_comment": "checkpoint-comment-8",
                        "branch": "feat/issue-8-durable-recovery",
                        "pull_request": "https://example.test/pulls/18",
                    },
                },
            ],
        )
        self.assertEqual(
            outcome["notifications"],
            [{"transition": "recovery-attempt", "attempt": 2}],
        )

    def test_first_failure_creates_one_replacement_when_resumption_is_impossible(
        self,
    ) -> None:
        snapshot = active_work_snapshot(
            {
                "id": "task-8",
                "issue": 8,
                "state": "failed",
                "resumable": False,
                "blocker": "task host no longer exists",
                "next_action": "replace task-8",
                "updated_at": "2026-08-24T10:05:00Z",
            }
        )
        snapshot["observed_at"] = "2026-08-24T10:06:00Z"

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "replace-task")
        self.assertEqual(outcome["checkpoint"]["attempt"], 2)
        self.assertIsNone(outcome["checkpoint"]["task_id"])
        replacement = outcome["requested_effects"][1]
        self.assertEqual(
            replacement,
            {
                "effect": "replace-task",
                "router": "ask-matt",
                "workflow": "/implement",
                "issue": 8,
                "replaces_task": "task-8",
                "attempt": 2,
                "reuse": {
                    "checkpoint_comment": "checkpoint-comment-8",
                    "branch": "feat/issue-8-durable-recovery",
                    "pull_request": "https://example.test/pulls/18",
                },
                "create_branch": False,
                "create_pull_request": False,
            },
        )
        self.assertEqual(len(outcome["requested_effects"]), 2)

    def test_second_failure_stops_recovery_in_durable_waiting(self) -> None:
        snapshot = active_work_snapshot(
            {
                "id": "task-8-replacement",
                "issue": 8,
                "state": "failed",
                "resumable": True,
                "blocker": "replacement failed repository verification",
                "next_action": "request human intervention",
                "updated_at": "2026-08-24T10:08:00Z",
            }
        )
        current = snapshot["tracker"]["tickets"][1]["checkpoint_comments"][0][
            "checkpoint"
        ]
        current.update(
            {
                "task_id": "task-8-replacement",
                "attempt": 2,
                "updated_at": "2026-08-24T10:08:00Z",
            }
        )

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "wait")
        self.assertEqual(outcome["lifecycle_state"], "waiting")
        self.assertEqual(outcome["checkpoint"]["attempt"], 2)
        self.assertEqual(
            outcome["checkpoint"]["blocker"],
            "replacement failed repository verification",
        )
        self.assertEqual(
            outcome["checkpoint"]["next_action"], "request human intervention"
        )
        self.assertEqual(len(outcome["requested_effects"]), 1)
        self.assertEqual(outcome["requested_effects"][0]["effect"], "update-checkpoint")
        self.assertEqual(
            outcome["notifications"],
            [{"transition": "recovery-exhausted", "attempt": 2}],
        )

    def test_unresumable_task_without_repository_progress_is_stale(self) -> None:
        snapshot = active_work_snapshot(
            {
                "id": "task-8",
                "issue": 8,
                "state": "unavailable",
                "resumable": False,
                "updated_at": "2026-08-24T10:05:00Z",
            }
        )
        snapshot["repository"]["branches"] = []
        snapshot["pull_requests"] = []
        snapshot["observed_at"] = "2026-08-24T10:06:00Z"

        outcome = run_scenario(snapshot)

        self.assertTrue(outcome["stale"])
        self.assertEqual(outcome["decision"], "replace-task")
        self.assertEqual(outcome["requested_effects"][1]["effect"], "replace-task")

    def test_repository_progress_prevents_stale_replacement(self) -> None:
        outcome = run_scenario(
            active_work_snapshot(
                {
                    "id": "task-8",
                    "issue": 8,
                    "state": "unavailable",
                    "resumable": False,
                    "updated_at": "2026-08-24T10:05:00Z",
                }
            )
        )

        self.assertFalse(outcome["stale"])
        self.assertEqual(outcome["decision"], "watch")
        self.assertNotIn(
            "replace-task", [effect["effect"] for effect in outcome["requested_effects"]]
        )
        self.assertEqual(
            outcome["requested_effects"][-1],
            {
                "effect": "watch-repository-checks",
                "pull_request": "https://example.test/pulls/18",
                "head_commit": "abc123",
            },
        )

    def test_watch_notifies_only_meaningful_transitions(self) -> None:
        snapshot = active_work_snapshot(
            {
                "id": "task-8",
                "issue": 8,
                "state": "running",
                "resumable": True,
                "native_wait": {"after_cursor": "task-event-17"},
                "updated_at": "2026-08-24T10:00:00Z",
            }
        )
        snapshot["events"] = [
            {
                "kind": "checks",
                "state": "pending",
                "cursor": "task-event-17",
            },
            {
                "kind": "heartbeat",
                "elapsed_seconds": 3600,
                "cursor": "task-event-18",
            },
            {"kind": "checks", "state": "failed", "cursor": "task-event-19"},
        ]

        outcome = run_scenario(snapshot)

        self.assertEqual(
            outcome["notifications"],
            [{"transition": "checks", "state": "failed"}],
        )
        self.assertEqual(
            outcome["requested_effects"][-2]["after_cursor"], "task-event-19"
        )

        snapshot["tasks"][0]["native_wait"]["after_cursor"] = "task-event-19"
        replayed = run_scenario(snapshot)

        self.assertEqual(replayed["notifications"], [])

    def test_ambiguous_branch_or_pull_request_evidence_stops_recovery(self) -> None:
        snapshot = active_work_snapshot(
            {
                "id": "task-8",
                "issue": 8,
                "state": "unavailable",
                "resumable": False,
                "updated_at": "2026-08-24T10:05:00Z",
            }
        )
        snapshot["observed_at"] = "2026-08-24T10:07:00Z"
        snapshot["repository"]["branches"].append(
            {
                "issue": 8,
                "name": "feat/issue-8-competing",
                "head_commit": "def456",
                "updated_at": "2026-08-24T10:06:00Z",
            }
        )

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "wait")
        self.assertEqual(outcome["lifecycle_state"], "waiting")
        self.assertEqual(outcome["checkpoint"]["attempt"], 1)
        self.assertEqual(
            outcome["checkpoint"]["branch"], "feat/issue-8-durable-recovery"
        )
        self.assertEqual(
            outcome["checkpoint"]["blocker"],
            "multiple implementation branches or pull requests prevent safe recovery",
        )
        self.assertNotIn(
            "replace-task", [effect["effect"] for effect in outcome["requested_effects"]]
        )

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
        self.assertTrue(delegation["isolated_workspace"])
        self.assertEqual(delegation["task_title"], "[programme #41] Add audit log")
        self.assertEqual(delegation["scope"]["issues"], [42])
        self.assertEqual(
            delegation["read_before_edit"],
            [
                "repository-instructions",
                "domain-vocabulary",
                "relevant-adrs",
                "complete-issue",
            ],
        )
        self.assertEqual(
            delegation["branch"],
            {"issue_specific": True, "before_edit": True},
        )
        self.assertEqual(
            delegation["implementation_contract"],
            {
                "tdd": True,
                "review_axes": [
                    "repository-standards-and-security",
                    "issue-behavior-and-acceptance",
                ],
                "commit": True,
                "open_pull_request": True,
                "record_blocker_durably": True,
                "stop_before": ["merge", "ticket-selection"],
            },
        )
        self.assertFalse(outcome["root_mutation_permitted"])

    def test_native_dependency_frontier_uses_approved_order(self) -> None:
        snapshot = prepared_snapshot()
        snapshot["programme"]["approved_order"] = [44, 43, 42]
        snapshot["tickets"] = [
            {
                "issue": 42,
                "title": "Blocked first ticket",
                "state": "ready",
                "blocked_by": [40],
            },
            {
                "issue": 43,
                "title": "Eligible second ticket",
                "state": "ready",
                "blocked_by": [],
            },
            {
                "issue": 44,
                "title": "Approved first ticket",
                "state": "ready",
                "blocked_by": [],
            },
        ]

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["selected_ticket"], 44)
        self.assertEqual(outcome["decisive_evidence"]["dependency_frontier"], [43, 44])
        self.assertEqual(outcome["decisive_evidence"]["approved_order"], [44, 43, 42])

    def test_safe_human_override_takes_precedence_over_approved_order(self) -> None:
        snapshot = prepared_snapshot()
        snapshot["programme"]["approved_order"] = [42, 43]
        snapshot["tickets"].append(
            {
                "issue": 43,
                "title": "Explicitly selected ticket",
                "state": "ready",
                "blocked_by": [],
            }
        )
        snapshot["user_instruction"]["override_issue"] = 43

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["selected_ticket"], 43)
        self.assertEqual(outcome["decisive_evidence"]["human_override"], "honored")

    def test_human_override_cannot_bypass_hard_gates(self) -> None:
        for gate in ("dependency", "safety", "approval", "adr_conflict"):
            with self.subTest(gate=gate):
                snapshot = prepared_snapshot()
                snapshot["programme"]["approved_order"] = [42, 43]
                overridden = {
                    "issue": 43,
                    "title": "Unsafe override",
                    "state": "ready",
                    "blocked_by": [40] if gate == "dependency" else [],
                    "gates": {gate: True} if gate != "dependency" else {},
                }
                snapshot["tickets"].append(overridden)
                snapshot["user_instruction"]["override_issue"] = 43

                outcome = run_scenario(snapshot)

                self.assertEqual(outcome["selected_ticket"], 42)
                self.assertEqual(
                    outcome["decisive_evidence"]["human_override"],
                    "rejected",
                )

    def test_active_mutating_delivery_or_capability_task_blocks_delegation(self) -> None:
        for lane in ("delivery", "capability"):
            with self.subTest(lane=lane):
                snapshot = prepared_snapshot()
                snapshot["tasks"] = [
                    {
                        "id": "task-active",
                        "state": "running",
                        "lane": lane,
                        "mutating": True,
                    }
                ]

                outcome = run_scenario(snapshot)

                self.assertEqual(outcome["decision"], "stop")
                self.assertEqual(outcome["reason"], "active-mutating-task")
                self.assertEqual(outcome["requested_effects"], [])

    def test_only_approved_read_only_research_may_run_concurrently(self) -> None:
        allowed = prepared_snapshot()
        allowed["tasks"] = [
            {
                "id": "research-approved",
                "state": "running",
                "lane": "research",
                "read_only": True,
                "approved": True,
            }
        ]

        self.assertEqual(run_scenario(allowed)["decision"], "delegate")

        for unsafe_research in (
            {"read_only": True, "approved": False},
            {"read_only": False, "approved": True},
        ):
            with self.subTest(task=unsafe_research):
                denied = prepared_snapshot()
                denied["tasks"] = [
                    {
                        "id": "research-unsafe",
                        "state": "running",
                        "lane": "research",
                        **unsafe_research,
                    }
                ]

                outcome = run_scenario(denied)

                self.assertEqual(outcome["decision"], "stop")
                self.assertEqual(outcome["reason"], "concurrency-not-permitted")

    def test_selected_ticket_stops_at_adr_gate_and_records_blocker(self) -> None:
        snapshot = prepared_snapshot()
        snapshot["tickets"][0]["gates"] = {"adr_conflict": "ADR-0007"}

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "stop")
        self.assertEqual(outcome["reason"], "adr-conflict")
        self.assertEqual(
            outcome["requested_effects"],
            [
                {
                    "effect": "record-blocker",
                    "issue": 42,
                    "state": "waiting",
                    "gate": "adr",
                }
            ],
        )

    def test_selected_ticket_stops_at_safety_or_approval_gate(self) -> None:
        for gate in ("safety", "approval"):
            with self.subTest(gate=gate):
                snapshot = prepared_snapshot()
                snapshot["tickets"][0]["gates"] = {gate: True}

                outcome = run_scenario(snapshot)

                self.assertEqual(outcome["decision"], "stop")
                self.assertEqual(outcome["reason"], f"{gate}-gate")
                self.assertEqual(outcome["requested_effects"], [])

    def test_mutating_delegation_requires_an_isolated_workspace(self) -> None:
        snapshot = prepared_snapshot()
        snapshot["repository"]["isolated_workspaces"] = False

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "stop")
        self.assertEqual(outcome["reason"], "isolated-workspace-unavailable")
        self.assertEqual(outcome["requested_effects"], [])

    def test_other_repository_mutating_workflows_get_isolation_and_branch(self) -> None:
        for intent in ("prototype", "architecture", "codebase_health"):
            with self.subTest(intent=intent):
                unavailable = prepared_snapshot(intent=intent)
                unavailable["repository"]["isolated_workspaces"] = False

                stopped = run_scenario(unavailable)

                self.assertEqual(stopped["decision"], "stop")
                self.assertEqual(
                    stopped["reason"],
                    "isolated-workspace-unavailable",
                )

                delegated = run_scenario(prepared_snapshot(intent=intent))[
                    "requested_effects"
                ][0]
                self.assertEqual(
                    delegated["branch"],
                    {"issue_specific": True, "before_edit": True},
                )

    def test_ask_matt_routes_every_approved_intent(self) -> None:
        routes = {
            "implementation": "/implement",
            "diagnosis": "/diagnosing-bugs",
            "research": "/research",
            "prototype": "/prototype",
            "architecture": "/grill-with-docs",
            "wayfinding": "/wayfinder",
            "codebase_health": "/improve-codebase-architecture",
            "specification": "/to-spec",
            "ticketing": "/to-tickets",
        }

        for intent, workflow in routes.items():
            with self.subTest(intent=intent):
                outcome = run_scenario(prepared_snapshot(intent=intent))
                delegation = outcome["requested_effects"][0]

                self.assertEqual(delegation["router"], "ask-matt")
                self.assertEqual(delegation["intent"], intent)
                self.assertEqual(delegation["workflow"], workflow)

    def test_coordinate_instruction_routes_the_ticket_intent(self) -> None:
        snapshot = prepared_snapshot(intent="coordinate")
        snapshot["tickets"][0]["intent"] = "diagnosis"

        outcome = run_scenario(snapshot)

        delegation = outcome["requested_effects"][0]
        self.assertEqual(delegation["intent"], "diagnosis")
        self.assertEqual(delegation["workflow"], "/diagnosing-bugs")

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
