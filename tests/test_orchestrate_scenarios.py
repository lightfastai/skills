import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACER = ROOT / "skills" / "orchestrate" / "scripts" / "trace.py"
POLICY_APPROVAL_GATES = (
    "credentials",
    "broad_permissions",
    "destructive_action",
    "legal_terms",
    "billing",
    "unverified_publisher",
    "material_scope_expansion",
)


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


def bootstrap_snapshot() -> dict:
    return {
        "repository": {
            "coordination_only": True,
            "isolated_workspaces": True,
        },
        "bootstrap": {
            "programme_issue": 6,
            "tracker": {"capability_tickets": []},
            "evidence": {
                name: {"present": True}
                for name in (
                    "repository_structure",
                    "tracker_state",
                    "agent_instructions",
                    "templates",
                    "ci",
                    "security",
                    "deployment",
                    "data",
                    "installed_skills",
                    "programme_evidence",
                )
            },
            "conventions": {
                "tracker": {"satisfies_contract": True},
                "checkpoint": {"satisfies_contract": True},
                "programme_discovery": {"satisfies_contract": False},
            },
            "local_contract": None,
            "agent_instructions": {"discovers_contract": False},
            "policy": {"published_version": 1, "adopted_version": None},
            "capability_gaps": [
                {
                    "category": "security_scanning",
                    "reason": "no repository security scan is configured",
                    "approved": False,
                }
            ],
        },
    }


def local_orchestration_contract(policy_version: int = 1) -> dict:
    return {
        "path": "docs/agents/orchestrate.md",
        "policy_version": policy_version,
        "content": {
            "orchestration-policy-version": {"version": policy_version},
            "verification": {
                "commands": ["python3 -m unittest"],
                "evidence": "passing exit status",
            },
            "programme-discovery": {
                "source": "configured-tracker",
                "active_selector": "one active programme",
            },
            "branch-and-merge-policy": {
                "branch_pattern": "feat/issue-{issue}",
                "merge_methods": ["repository-approved"],
            },
            "approval-limits": {"gates": ["credentials", "permissions"]},
            "skill-allowlist": {"skills": [], "publishers": []},
            "research-topics-and-schedules": {
                "topics": [],
                "cadences": {"default": "monthly"},
            },
            "exceptions": {"items": []},
        },
        "runtime_state_present": False,
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


def delivered_work_snapshot(**overrides: object) -> dict:
    snapshot = active_work_snapshot(
        {
            "id": "task-8",
            "issue": 8,
            "state": "delivered",
            "resumable": True,
            "updated_at": "2026-08-24T10:08:00Z",
        }
    )
    snapshot["observed_at"] = "2026-08-24T10:09:00Z"
    snapshot["repository"].update(
        {
            "merge_policy": {"permitted_methods": ["squash", "merge"]},
            "supported_merge_methods": ["merge", "squash", "rebase"],
        }
    )
    snapshot["repository"]["branches"][0].update(
        {"remote_commit": "abc123", "state": "clean"}
    )
    snapshot["pull_requests"][0].update(
        {
            "delivered": True,
            "required_checks": [{"name": "test", "state": "passed"}],
            "review": {"required": False, "approved": False},
            "mergeable": True,
        }
    )
    current_ticket = next(
        ticket for ticket in snapshot["tracker"]["tickets"] if ticket["issue"] == 8
    )
    current_ticket["acceptance_criteria_checked"] = True
    snapshot["workspaces"] = [
        {
            "issue": 8,
            "branch": "feat/issue-8-durable-recovery",
            "state": "isolated",
        }
    ]
    for key, value in overrides.items():
        snapshot[key] = value
    return snapshot


class OrchestrateScenarios(unittest.TestCase):
    def test_bootstrap_audits_evidence_and_reuses_only_satisfying_conventions(
        self,
    ) -> None:
        outcome = run_scenario(bootstrap_snapshot())

        self.assertEqual(outcome["decision"], "bootstrap-audit")
        self.assertEqual(
            outcome["audit"]["inspected"],
            [
                "repository_structure",
                "tracker_state",
                "agent_instructions",
                "templates",
                "ci",
                "security",
                "deployment",
                "data",
                "installed_skills",
                "programme_evidence",
            ],
        )
        self.assertEqual(outcome["audit"]["reused"], ["checkpoint", "tracker"])
        self.assertEqual(
            outcome["control_plane"]["missing"],
            ["agent-discovery", "local-contract", "programme-discovery"],
        )
        self.assertEqual(
            outcome["capability_gaps"],
            [
                {
                    "category": "security_scanning",
                    "reason": "repository capability gap: security_scanning",
                    "status": "proposal",
                }
            ],
        )
        self.assertFalse(outcome["root_mutation_permitted"])
        self.assertTrue(
            all(
                effect["effect"] != "delegate"
                for effect in outcome["requested_effects"]
            )
        )

        unavailable = bootstrap_snapshot()
        unavailable["bootstrap"]["evidence"]["security"] = {"present": False}
        unavailable["bootstrap"]["evidence"]["deployment"] = {"present": False}

        incomplete = run_scenario(unavailable)

        self.assertNotIn("security", incomplete["audit"]["inspected"])
        self.assertEqual(
            incomplete["audit"]["unavailable"], ["security", "deployment"]
        )

        unavailable["bootstrap"]["evidence"]["tracker_state"] = {
            "present": False
        }
        uncorroborated = run_scenario(unavailable)
        self.assertNotIn("tracker", uncorroborated["audit"]["reused"])
        self.assertIn("tracker", uncorroborated["control_plane"]["missing"])

    def test_policy_changes_produce_reviewable_migrations_without_rewrites(
        self,
    ) -> None:
        snapshot = bootstrap_snapshot()
        snapshot["bootstrap"]["conventions"]["programme_discovery"] = {
            "satisfies_contract": True
        }
        snapshot["bootstrap"]["agent_instructions"] = {
            "discovers_contract": True
        }
        snapshot["bootstrap"]["local_contract"] = local_orchestration_contract()
        snapshot["bootstrap"]["local_contract"]["local_decisions"] = [
            "repository-selected merge policy"
        ]
        snapshot["bootstrap"]["policy"] = {
            "published_version": 2,
            "adopted_version": 1,
            "change_ids": ["require-explicit-capability-approval"],
        }
        snapshot["bootstrap"]["capability_gaps"] = []

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["control_plane"]["missing"], [])
        self.assertEqual(
            outcome["policy"],
            {
                "published_version": 2,
                "adopted_version": 1,
                "status": "migration-proposed",
            },
        )
        self.assertEqual(
            outcome["requested_effects"],
            [
                {
                    "effect": "propose-policy-migration",
                    "path": "docs/agents/orchestrate.md",
                    "from_version": 1,
                    "to_version": 2,
                    "reviewable": True,
                    "silent_rewrite": False,
                    "preserve_local_decisions": True,
                    "preserve_runtime_state": True,
                    "change_ids": ["require-explicit-capability-approval"],
                    "approval_required": True,
                }
            ],
        )

    def test_bootstrap_delegates_one_capability_only_after_approval(self) -> None:
        snapshot = bootstrap_snapshot()
        snapshot["bootstrap"]["capability_gaps"] = [
            {
                "issue": 45,
                "title": "Add security scanning",
                "category": "security_scanning",
                "reason": "no repository security scan is configured",
                "approved": True,
            }
        ]
        snapshot["bootstrap"]["tracker"]["capability_tickets"] = [
            {"issue": 45, "state": "ready"}
        ]
        snapshot["approvals"] = {
            "bootstrap_capability": {
                "approved": True,
                "scope": {"issue": 45, "category": "security_scanning"},
            }
        }

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "bootstrap-delegate-capability")
        delegations = [
            effect
            for effect in outcome["requested_effects"]
            if effect["effect"] == "delegate"
        ]
        self.assertEqual(len(delegations), 1)
        delegation = delegations[0]
        self.assertEqual(delegation["router"], "ask-matt")
        self.assertEqual(delegation["workflow"], "/implement")
        self.assertEqual(delegation["scope"], {"issues": [45]})
        self.assertFalse(delegation["apply_in_root"])
        self.assertFalse(outcome["root_mutation_permitted"])

        snapshot["tasks"] = [
            {
                "id": "delivery-active",
                "state": "running",
                "lane": "delivery",
                "mutating": True,
            }
        ]
        stopped = run_scenario(snapshot)

        self.assertEqual(stopped["decision"], "stop")
        self.assertEqual(stopped["reason"], "active-mutating-task")
        self.assertFalse(
            any(
                effect["effect"] == "delegate"
                for effect in stopped["requested_effects"]
            )
        )

    def test_runtime_state_in_local_contract_is_reported_not_rewritten(self) -> None:
        snapshot = bootstrap_snapshot()
        snapshot["bootstrap"]["agent_instructions"] = {
            "discovers_contract": True
        }
        snapshot["bootstrap"]["local_contract"] = local_orchestration_contract()
        snapshot["bootstrap"]["local_contract"].update(
            {
                "runtime_state_present": True,
                "runtime_state": {"private_task": "must-not-be-copied"},
            }
        )

        outcome = run_scenario(snapshot)

        self.assertIn("local-contract", outcome["control_plane"]["missing"])
        self.assertNotIn("agent-discovery", outcome["control_plane"]["missing"])
        self.assertEqual(
            outcome["contract"],
            {
                "path": "docs/agents/orchestrate.md",
                "status": "runtime-state-present",
                "runtime_state_permitted": False,
            },
        )
        proposal = next(
            effect
            for effect in outcome["requested_effects"]
            if effect["effect"] == "propose-local-contract"
        )
        self.assertEqual(proposal["path"], "docs/agents/orchestrate.md")
        self.assertEqual(proposal["agent_discovery"], "AGENTS.md")
        self.assertFalse(proposal["runtime_state_permitted"])
        self.assertNotIn("must-not-be-copied", json.dumps(outcome))

    def test_bootstrap_does_not_delegate_an_untrusted_skill_publisher(self) -> None:
        snapshot = bootstrap_snapshot()
        snapshot["repository"]["public_skill_source_allowlist"] = [
            "public-registry/release-skill"
        ]
        snapshot["bootstrap"]["tracker"]["capability_tickets"] = [
            {"issue": 46, "state": "ready"}
        ]
        snapshot["bootstrap"]["capability_gaps"] = [
            {
                "issue": 46,
                "title": "Install release skill",
                "category": "installed_skill",
                "reason": "private-provider-response-must-not-leak",
                "approved": True,
                "installation": {
                    "publisher": "untrusted-lab",
                    "source": "public-registry/release-skill",
                    "version": "sha256:abc123",
                    "permissions": ["repository:read"],
                    "reason": "inspect release metadata",
                },
            }
        ]
        snapshot["approvals"] = {
            "bootstrap_capability": {
                "approved": True,
                "scope": {"issue": 46, "category": "installed_skill"},
            }
        }

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "stop")
        self.assertEqual(outcome["reason"], "publisher-approval-required")
        self.assertFalse(
            any(
                effect["effect"] == "delegate"
                for effect in outcome["requested_effects"]
            )
        )
        self.assertNotIn("private-provider-response", json.dumps(outcome))
        self.assertNotIn("public-registry", json.dumps(outcome))

    def test_agent_discovery_gap_preserves_an_adopted_local_contract(self) -> None:
        snapshot = bootstrap_snapshot()
        snapshot["bootstrap"]["conventions"]["programme_discovery"] = {
            "satisfies_contract": True
        }
        snapshot["bootstrap"]["local_contract"] = local_orchestration_contract()
        snapshot["bootstrap"]["policy"]["adopted_version"] = 1
        snapshot["bootstrap"]["capability_gaps"] = []

        outcome = run_scenario(snapshot)

        effects = outcome["requested_effects"]
        self.assertTrue(
            any(effect["effect"] == "propose-agent-discovery" for effect in effects)
        )
        self.assertFalse(
            any(effect["effect"] == "propose-local-contract" for effect in effects)
        )

        versionless = bootstrap_snapshot()
        versionless["bootstrap"]["local_contract"] = local_orchestration_contract()
        versionless["bootstrap"]["local_contract"]["policy_version"] = None
        versionless["bootstrap"]["local_contract"]["content"][
            "orchestration-policy-version"
        ] = {"version": None}
        invalid = run_scenario(versionless)
        self.assertIn("local-contract", invalid["control_plane"]["missing"])

    def test_pending_required_check_prevents_merge(self) -> None:
        snapshot = delivered_work_snapshot()
        snapshot["pull_requests"][0]["required_checks"][0]["state"] = "pending"

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "wait")
        self.assertEqual(outcome["delivery_gates"]["checks"], "pending")
        self.assertFalse(outcome["child_merge_authorized"])
        self.assertNotIn(
            "merge-pull-request",
            [effect["effect"] for effect in outcome["requested_effects"]],
        )

    def test_merged_pull_request_requires_independent_main_verification(self) -> None:
        snapshot = delivered_work_snapshot()
        snapshot["pull_requests"][0].update(
            {
                "state": "merged",
                "merge_commit": "merged456",
                "updated_at": "2026-08-24T10:10:00Z",
            }
        )

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "verify-main")
        self.assertIn(
            {
                "effect": "verify-main",
                "branch": "main",
                "commit": "merged456",
                "independent": True,
            },
            outcome["requested_effects"],
        )
        self.assertNotIn(
            "release-workspace",
            [effect["effect"] for effect in outcome["requested_effects"]],
        )

    def test_failed_main_verification_records_waiting_without_closure(self) -> None:
        snapshot = delivered_work_snapshot()
        snapshot["pull_requests"][0].update(
            {
                "state": "merged",
                "merge_commit": "merged456",
                "updated_at": "2026-08-24T10:10:00Z",
            }
        )
        snapshot["repository"]["main"] = {
            "verified_commit": None,
            "verification": {
                "commit": "merged456",
                "state": "failed",
                "evidence_recorded": True,
                "observed_at": "2026-08-24T10:11:00Z",
            },
        }

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "wait")
        self.assertEqual(outcome["lifecycle_state"], "waiting")
        self.assertEqual(
            outcome["checkpoint"]["blocker"],
            "merged main verification failed",
        )
        self.assertEqual(
            outcome["checkpoint"]["next_action"],
            "repair merged main and rerun independent verification",
        )
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

    def test_verified_merged_work_requests_full_evidence_ticket_closure(self) -> None:
        snapshot = delivered_work_snapshot()
        snapshot["pull_requests"][0].update(
            {
                "state": "merged",
                "merge_commit": "merged456",
                "updated_at": "2026-08-24T10:10:00Z",
            }
        )
        snapshot["repository"]["main"] = {
            "verified_commit": "merged456",
            "verified_at": "2026-08-24T10:11:00Z",
            "verification_evidence_recorded": True,
        }

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "close-ticket")
        self.assertEqual(outcome["lifecycle_state"], "active")
        self.assertEqual(outcome["checkpoint"]["verified_commit"], "merged456")
        self.assertIn(
            {
                "effect": "close-ticket",
                "issue": 8,
                "closure_evidence": {
                    "pull_request": "https://example.test/pulls/18",
                    "merge_commit": "merged456",
                    "verified_main_commit": "merged456",
                    "verification_evidence_recorded": True,
                    "acceptance_criteria_checked": True,
                },
            },
            outcome["requested_effects"],
        )
        self.assertNotIn(
            "release-workspace",
            [effect["effect"] for effect in outcome["requested_effects"]],
        )

    def test_done_records_closure_and_releases_only_proven_workspace(self) -> None:
        snapshot = delivered_work_snapshot()
        snapshot["pull_requests"][0].update(
            {
                "state": "merged",
                "merge_commit": "merged456",
                "updated_at": "2026-08-24T10:10:00Z",
            }
        )
        snapshot["repository"]["main"] = {
            "verified_commit": "merged456",
            "verified_at": "2026-08-24T10:11:00Z",
            "verification_evidence_recorded": True,
        }
        current_ticket = next(
            ticket
            for ticket in snapshot["tracker"]["tickets"]
            if ticket["issue"] == 8
        )
        current_ticket.update(
            {"state": "closed", "closed_at": "2026-08-24T10:12:00Z"}
        )

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "done")
        self.assertEqual(outcome["lifecycle_state"], "done")
        self.assertEqual(outcome["checkpoint"]["verified_commit"], "merged456")
        self.assertEqual(
            outcome["closure_evidence"],
            {
                "pull_request": "https://example.test/pulls/18",
                "merge_commit": "merged456",
                "verified_main_commit": "merged456",
                "verification_evidence_recorded": True,
                "acceptance_criteria_checked": True,
                "issue_closed": True,
            },
        )
        self.assertIn(
            {
                "effect": "release-workspace",
                "issue": 8,
                "branch": "feat/issue-8-durable-recovery",
                "proof": {
                    "remote_commit": "abc123",
                    "merged_commit": "merged456",
                    "verified_main_commit": "merged456",
                },
            },
            outcome["requested_effects"],
        )

    def test_each_failed_delivery_gate_independently_prevents_merge(self) -> None:
        scenarios = {
            "failing-check": (
                lambda snapshot: snapshot["pull_requests"][0][
                    "required_checks"
                ][0].update({"state": "failed"}),
                ("checks", "failed"),
            ),
            "acceptance": (
                lambda snapshot: next(
                    ticket
                    for ticket in snapshot["tracker"]["tickets"]
                    if ticket["issue"] == 8
                ).update({"acceptance_criteria_checked": False}),
                ("acceptance", "failed"),
            ),
            "review": (
                lambda snapshot: snapshot["pull_requests"][0].update(
                    {"review": {"required": True, "approved": False}}
                ),
                ("review", "required"),
            ),
            "conflict": (
                lambda snapshot: snapshot["pull_requests"][0].update(
                    {"mergeable": False}
                ),
                ("branch", "conflicting"),
            ),
            "unsupported-method": (
                lambda snapshot: snapshot["repository"].update(
                    {"supported_merge_methods": ["rebase"]}
                ),
                ("merge_policy", "unsupported"),
            ),
        }

        for name, (mutate, expected_gate) in scenarios.items():
            with self.subTest(name=name):
                snapshot = delivered_work_snapshot()
                mutate(snapshot)

                outcome = run_scenario(snapshot)

                gate, state = expected_gate
                self.assertEqual(outcome["decision"], "wait")
                self.assertEqual(outcome["delivery_gates"][gate], state)
                self.assertNotIn(
                    "merge-pull-request",
                    [
                        effect["effect"]
                        for effect in outcome["requested_effects"]
                    ],
                )

    def test_ready_delivery_uses_first_permitted_supported_merge_method(self) -> None:
        snapshot = delivered_work_snapshot()
        snapshot["repository"]["merge_policy"]["permitted_methods"] = [
            "rebase",
            "squash",
        ]
        snapshot["repository"]["supported_merge_methods"] = ["squash", "merge"]

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "merge")
        self.assertEqual(
            outcome["delivery_gates"],
            {
                "acceptance": "passed",
                "review": "passed",
                "checks": "passed",
                "branch": "passed",
                "merge_policy": "passed",
            },
        )
        self.assertFalse(outcome["child_merge_authorized"])
        self.assertIn(
            {
                "effect": "merge-pull-request",
                "pull_request": "https://example.test/pulls/18",
                "head_commit": "abc123",
                "method": "squash",
                "actor": "root-orchestrator",
            },
            outcome["requested_effects"],
        )

    def test_done_does_not_release_workspace_without_remote_commit_proof(self) -> None:
        snapshot = delivered_work_snapshot()
        snapshot["repository"]["branches"][0].pop("remote_commit")
        snapshot["pull_requests"][0].update(
            {
                "state": "merged",
                "merge_commit": "merged456",
                "updated_at": "2026-08-24T10:10:00Z",
            }
        )
        snapshot["repository"]["main"] = {
            "verified_commit": "merged456",
            "verified_at": "2026-08-24T10:11:00Z",
            "verification_evidence_recorded": True,
        }
        current_ticket = next(
            ticket
            for ticket in snapshot["tracker"]["tickets"]
            if ticket["issue"] == 8
        )
        current_ticket.update(
            {"state": "closed", "closed_at": "2026-08-24T10:12:00Z"}
        )

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["lifecycle_state"], "done")
        self.assertNotIn(
            "release-workspace",
            [effect["effect"] for effect in outcome["requested_effects"]],
        )

    def test_unknown_gate_evidence_and_missing_head_prevent_merge(self) -> None:
        scenarios = {
            "checks": (
                lambda snapshot: snapshot["pull_requests"][0].pop(
                    "required_checks"
                ),
                ("checks", "unknown"),
            ),
            "review": (
                lambda snapshot: snapshot["pull_requests"][0].pop("review"),
                ("review", "unknown"),
            ),
            "head": (
                lambda snapshot: snapshot["pull_requests"][0].pop(
                    "head_commit"
                ),
                ("branch", "unknown"),
            ),
        }

        for name, (mutate, expected_gate) in scenarios.items():
            with self.subTest(name=name):
                snapshot = delivered_work_snapshot()
                mutate(snapshot)

                outcome = run_scenario(snapshot)

                gate, state = expected_gate
                self.assertEqual(outcome["decision"], "wait")
                self.assertEqual(outcome["delivery_gates"][gate], state)
                self.assertNotIn(
                    "merge-pull-request",
                    [
                        effect["effect"]
                        for effect in outcome["requested_effects"]
                    ],
                )

    def test_newer_successful_verification_wins_over_stale_failure(self) -> None:
        snapshot = delivered_work_snapshot()
        snapshot["pull_requests"][0].update(
            {
                "state": "merged",
                "merge_commit": "merged456",
                "updated_at": "2026-08-24T10:10:00Z",
            }
        )
        snapshot["repository"]["main"] = {
            "verified_commit": "merged456",
            "verified_at": "2026-08-24T10:12:00Z",
            "verification_evidence_recorded": True,
            "verification": {
                "commit": "merged456",
                "state": "failed",
                "evidence_recorded": True,
                "observed_at": "2026-08-24T10:11:00Z",
            },
        }

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "close-ticket")
        self.assertEqual(outcome["lifecycle_state"], "active")
        self.assertIsNone(outcome["checkpoint"]["blocker"])

    def test_workspace_release_proof_must_match_the_workspace_branch(self) -> None:
        snapshot = delivered_work_snapshot()
        snapshot["workspaces"][0]["branch"] = "feat/unrelated"
        snapshot["pull_requests"][0].update(
            {
                "state": "merged",
                "merge_commit": "merged456",
                "updated_at": "2026-08-24T10:10:00Z",
            }
        )
        snapshot["repository"]["main"] = {
            "verified_commit": "merged456",
            "verified_at": "2026-08-24T10:11:00Z",
            "verification_evidence_recorded": True,
        }
        current_ticket = next(
            ticket
            for ticket in snapshot["tracker"]["tickets"]
            if ticket["issue"] == 8
        )
        current_ticket.update(
            {"state": "closed", "closed_at": "2026-08-24T10:12:00Z"}
        )

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["lifecycle_state"], "done")
        self.assertNotIn(
            "release-workspace",
            [effect["effect"] for effect in outcome["requested_effects"]],
        )

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

    def test_active_work_hard_gate_updates_existing_checkpoint_before_action(
        self,
    ) -> None:
        snapshot = active_work_snapshot(
            {
                "id": "task-8",
                "issue": 8,
                "state": "running",
                "resumable": True,
                "native_wait": {"after_cursor": "task-event-17"},
                "updated_at": "2026-08-24T10:05:00Z",
            }
        )
        snapshot["observed_at"] = "2026-08-24T10:06:00Z"
        current_ticket = snapshot["tracker"]["tickets"][1]
        current_ticket["gates"] = {
            "credentials": {"scope": {"credential": "private-name"}}
        }

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "wait")
        self.assertEqual(outcome["lifecycle_state"], "waiting")
        self.assertEqual(
            outcome["checkpoint"]["blocker"],
            "credential access requires explicit approval",
        )
        self.assertEqual(
            outcome["checkpoint"]["next_action"],
            "approve the credential purpose and least-privilege access scope",
        )
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
        self.assertNotIn("private-name", json.dumps(outcome))

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

    def test_human_override_cannot_bypass_specific_policy_gates(self) -> None:
        gated_requests = {
            "ready_for_human": True,
            "adr_conflict": "ADR-0007",
            "paid_model_run": {
                "manifest": {
                    "models": ["model-a"],
                    "max_calls": 2,
                    "estimated_cost": {"amount": 1, "currency": "USD"},
                }
            },
            **{
                gate: {"scope": {"request": gate}}
                for gate in POLICY_APPROVAL_GATES
            },
        }
        for gate, request in gated_requests.items():
            with self.subTest(gate=gate):
                snapshot = prepared_snapshot()
                snapshot["programme"]["approved_order"] = [42, 43]
                snapshot["tickets"].append(
                    {
                        "issue": 43,
                        "title": "Policy-gated override",
                        "state": "ready",
                        "blocked_by": [],
                        "gates": {gate: request},
                    }
                )
                snapshot["user_instruction"].update(
                    {"override_issue": 43, "proceed": True}
                )

                outcome = run_scenario(snapshot)

                self.assertEqual(outcome["selected_ticket"], 42)
                self.assertEqual(
                    outcome["decisive_evidence"]["human_override"], "rejected"
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
                    "blocker": "selected work conflicts with ADR-0007",
                    "next_action": (
                        "approve a revision or exception to ADR-0007 before delegation"
                    ),
                }
            ],
        )

    def test_adr_path_is_reduced_to_a_safe_decision_identifier(self) -> None:
        snapshot = prepared_snapshot()
        snapshot["tickets"][0]["gates"] = {
            "adr_conflict": "docs/adr/0007-private-detail.md"
        }

        outcome = run_scenario(snapshot)

        blocker = outcome["requested_effects"][0]
        self.assertEqual(blocker["blocker"], "selected work conflicts with ADR-0007")
        self.assertNotIn("private-detail", json.dumps(outcome))

    def test_private_adr_like_value_is_not_copied_to_checkpoint(self) -> None:
        snapshot = prepared_snapshot()
        snapshot["tickets"][0]["gates"] = {
            "adr_conflict": "ADR-customerSecret42"
        }

        outcome = run_scenario(snapshot)

        self.assertNotIn("customerSecret42", json.dumps(outcome))
        self.assertEqual(
            outcome["requested_effects"][0]["blocker"],
            "selected work conflicts with the applicable ADR",
        )

    def test_selected_ticket_stops_at_safety_or_approval_gate(self) -> None:
        for gate in ("safety", "approval"):
            with self.subTest(gate=gate):
                snapshot = prepared_snapshot()
                snapshot["tickets"][0]["gates"] = {gate: True}

                outcome = run_scenario(snapshot)

                self.assertEqual(outcome["decision"], "stop")
                self.assertEqual(outcome["reason"], f"{gate}-gate")
                self.assertEqual(len(outcome["requested_effects"]), 1)
                blocker = outcome["requested_effects"][0]
                self.assertEqual(blocker["effect"], "record-blocker")
                self.assertEqual(blocker["state"], "waiting")
                self.assertTrue(blocker["blocker"])
                self.assertTrue(blocker["next_action"])

    def test_ready_for_human_is_an_unconditional_durable_pause(self) -> None:
        snapshot = prepared_snapshot()
        snapshot["tickets"][0]["gates"] = {"ready_for_human": True}
        snapshot["approvals"] = {"ready_for_human": {"approved": True}}

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "stop")
        self.assertEqual(outcome["reason"], "ready-for-human")
        self.assertEqual(
            outcome["requested_effects"],
            [
                {
                    "effect": "record-blocker",
                    "issue": 42,
                    "state": "waiting",
                    "gate": "ready-for-human",
                    "blocker": "ticket is labelled ready-for-human",
                    "next_action": (
                        "a human must complete or reclassify the ticket and "
                        "record the decision"
                    ),
                }
            ],
        )

    def test_ready_for_human_label_is_normalized_as_a_hard_pause(self) -> None:
        snapshot = prepared_snapshot()
        snapshot["tickets"][0]["labels"] = ["ready-for-human"]

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["reason"], "ready-for-human")
        self.assertEqual(outcome["requested_effects"][0]["state"], "waiting")

    def test_paid_model_run_without_approval_and_bounded_manifest_pauses(self) -> None:
        snapshot = prepared_snapshot()
        snapshot["tickets"][0]["gates"] = {
            "paid_model_run": {
                "manifest": {
                    "models": ["secret-provider-model"],
                    "estimated_cost": {"amount": 5, "currency": "USD"},
                }
            }
        }

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "stop")
        self.assertEqual(outcome["reason"], "paid-model-approval-required")
        blocker = outcome["requested_effects"][0]
        self.assertEqual(blocker["gate"], "paid-model-run")
        self.assertEqual(
            blocker["blocker"],
            "paid model run lacks an approved bounded manifest",
        )
        self.assertEqual(
            blocker["next_action"],
            (
                "approve a manifest naming models, a maximum call or token "
                "limit, and estimated cost"
            ),
        )
        self.assertNotIn("secret-provider-model", json.dumps(outcome))

    def test_approved_bounded_paid_model_manifest_allows_delegation(self) -> None:
        manifest = {
            "models": ["model-a"],
            "max_tokens": 1000,
            "estimated_cost": {"amount": 5, "currency": "USD"},
        }
        snapshot = prepared_snapshot()
        snapshot["tickets"][0]["gates"] = {
            "paid_model_run": {"manifest": manifest}
        }
        snapshot["approvals"] = {
            "paid_model_run": {"approved": True, "manifest": manifest}
        }

        self.assertEqual(run_scenario(snapshot)["decision"], "delegate")

    def test_paid_model_approval_with_insufficient_scope_pauses(self) -> None:
        requested = {
            "models": ["model-a", "model-b"],
            "max_calls": 10,
            "estimated_cost": {"amount": 5, "currency": "USD"},
        }
        approved = {
            "models": ["model-a"],
            "max_calls": 10,
            "estimated_cost": {"amount": 5, "currency": "USD"},
        }
        snapshot = prepared_snapshot()
        snapshot["tickets"][0]["gates"] = {
            "paid_model_run": {"manifest": requested}
        }
        snapshot["approvals"] = {
            "paid_model_run": {"approved": True, "manifest": approved}
        }

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "stop")
        self.assertEqual(outcome["reason"], "paid-model-approval-required")

    def test_paid_manifest_rejects_blank_names_and_invalid_declared_limits(
        self,
    ) -> None:
        invalid_manifests = (
            {
                "models": ["   "],
                "max_calls": 1,
                "estimated_cost": {"amount": 1, "currency": "USD"},
            },
            {
                "models": ["model-a"],
                "max_calls": 1,
                "estimated_cost": {"amount": 1, "currency": "   "},
            },
            {
                "models": ["model-a"],
                "max_calls": 1,
                "max_tokens": -1,
                "estimated_cost": {"amount": 1, "currency": "USD"},
            },
        )
        for manifest in invalid_manifests:
            with self.subTest(manifest=manifest):
                snapshot = prepared_snapshot()
                snapshot["tickets"][0]["gates"] = {
                    "paid_model_run": {"manifest": manifest}
                }
                snapshot["approvals"] = {
                    "paid_model_run": {"approved": True, "manifest": manifest}
                }

                self.assertEqual(run_scenario(snapshot)["decision"], "stop")

    def test_sensitive_and_privileged_actions_require_scoped_approval(self) -> None:
        for gate in POLICY_APPROVAL_GATES:
            with self.subTest(gate=gate):
                snapshot = prepared_snapshot()
                snapshot["tickets"][0]["gates"] = {
                    gate: {"scope": {"request": "sensitive-value"}}
                }

                outcome = run_scenario(snapshot)

                self.assertEqual(outcome["decision"], "stop")
                self.assertEqual(
                    outcome["reason"],
                    f"{gate.replace('_', '-')}-approval-required",
                )
                blocker = outcome["requested_effects"][0]
                self.assertEqual(blocker["state"], "waiting")
                self.assertTrue(blocker["blocker"])
                self.assertTrue(blocker["next_action"])
                self.assertNotIn("sensitive-value", json.dumps(outcome))

    def test_exact_scoped_approvals_allow_privileged_actions(self) -> None:
        for gate in POLICY_APPROVAL_GATES:
            with self.subTest(gate=gate):
                scope = {"request": f"approved-{gate}"}
                snapshot = prepared_snapshot()
                snapshot["tickets"][0]["gates"] = {gate: {"scope": scope}}
                snapshot["approvals"] = {
                    gate: {"approved": True, "scope": scope}
                }

                self.assertEqual(run_scenario(snapshot)["decision"], "delegate")

    def test_empty_or_content_free_scope_is_not_an_approval_boundary(self) -> None:
        for scope in (
            {},
            {"resources": []},
            "all",
            True,
            0,
            -1,
            {"resources": "all"},
        ):
            with self.subTest(scope=scope):
                snapshot = prepared_snapshot()
                snapshot["tickets"][0]["gates"] = {
                    "broad_permissions": {"scope": scope}
                }
                snapshot["approvals"] = {
                    "broad_permissions": {"approved": True, "scope": scope}
                }

                outcome = run_scenario(snapshot)

                self.assertEqual(outcome["decision"], "stop")
                self.assertEqual(
                    outcome["reason"],
                    "broad-permissions-approval-required",
                )

    def test_non_finite_values_are_not_bounded_approval_evidence(self) -> None:
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                scope = {"limit": value}
                snapshot = prepared_snapshot()
                snapshot["tickets"][0]["gates"] = {
                    "billing": {"scope": scope}
                }
                snapshot["approvals"] = {
                    "billing": {"approved": True, "scope": scope}
                }

                self.assertEqual(run_scenario(snapshot)["decision"], "stop")

                manifest = {
                    "models": ["model-a"],
                    "max_calls": 1,
                    "estimated_cost": {"amount": value, "currency": "USD"},
                }
                snapshot = prepared_snapshot()
                snapshot["tickets"][0]["gates"] = {
                    "paid_model_run": {"manifest": manifest}
                }
                snapshot["approvals"] = {
                    "paid_model_run": {"approved": True, "manifest": manifest}
                }

                self.assertEqual(run_scenario(snapshot)["decision"], "stop")

    def test_large_integer_bounds_remain_exact_without_numeric_overflow(self) -> None:
        large_bound = 10**1000
        scope = {"limit": large_bound}
        snapshot = prepared_snapshot()
        snapshot["tickets"][0]["gates"] = {"billing": {"scope": scope}}
        snapshot["approvals"] = {
            "billing": {"approved": True, "scope": scope}
        }

        self.assertEqual(run_scenario(snapshot)["decision"], "delegate")

        manifest = {
            "models": ["model-a"],
            "max_calls": 1,
            "estimated_cost": {"amount": large_bound, "currency": "USD"},
        }
        snapshot = prepared_snapshot()
        snapshot["tickets"][0]["gates"] = {
            "paid_model_run": {"manifest": manifest}
        }
        snapshot["approvals"] = {
            "paid_model_run": {"approved": True, "manifest": manifest}
        }

        self.assertEqual(run_scenario(snapshot)["decision"], "delegate")

    def test_boolean_values_cannot_match_numeric_approval_bounds(self) -> None:
        snapshot = prepared_snapshot()
        snapshot["tickets"][0]["gates"] = {
            "billing": {"scope": {"limit": 1}}
        }
        snapshot["approvals"] = {
            "billing": {"approved": True, "scope": {"limit": True}}
        }

        self.assertEqual(run_scenario(snapshot)["decision"], "stop")

        requested = {
            "models": ["model-a"],
            "max_calls": 1,
            "estimated_cost": {"amount": 0, "currency": "USD"},
        }
        approved = {
            "models": ["model-a"],
            "max_calls": True,
            "estimated_cost": {"amount": False, "currency": "USD"},
        }
        snapshot = prepared_snapshot()
        snapshot["tickets"][0]["gates"] = {
            "paid_model_run": {"manifest": requested}
        }
        snapshot["approvals"] = {
            "paid_model_run": {"approved": True, "manifest": approved}
        }

        self.assertEqual(run_scenario(snapshot)["decision"], "stop")

    def test_empty_gate_payloads_fail_closed(self) -> None:
        for gate in ("paid_model_run", *POLICY_APPROVAL_GATES):
            with self.subTest(gate=gate):
                snapshot = prepared_snapshot()
                snapshot["tickets"][0]["gates"] = {gate: {}}

                self.assertEqual(run_scenario(snapshot)["decision"], "stop")

    def test_general_proceed_and_narrow_approval_do_not_expand_scope(self) -> None:
        snapshot = prepared_snapshot()
        snapshot["tickets"][0]["gates"] = {
            "material_scope_expansion": {
                "scope": {"issues": [42, 43], "change": "new-service"}
            }
        }
        snapshot["approvals"] = {
            "material_scope_expansion": {
                "approved": True,
                "scope": {"issues": [42]},
            }
        }
        snapshot["user_instruction"]["proceed"] = True

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "stop")
        self.assertEqual(
            outcome["reason"], "material-scope-expansion-approval-required"
        )

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

    def test_capability_gaps_become_bounded_proposals_without_root_implementation(
        self,
    ) -> None:
        categories = (
            "ci",
            "security_scanning",
            "datasets",
            "experiment_tracking",
            "deployment",
            "provider_integration",
        )
        for category in categories:
            with self.subTest(category=category):
                snapshot = prepared_snapshot(intent="coordinate")
                snapshot["stewardship"] = {
                    "capability": {
                        "category": category,
                        "reason": "close a roadmap capability gap",
                        "approved": False,
                    }
                }

                outcome = run_scenario(snapshot)

                self.assertEqual(outcome["decision"], "propose-capability")
                self.assertFalse(outcome["root_mutation_permitted"])
                self.assertEqual(
                    outcome["requested_effects"],
                    [
                        {
                            "effect": "create-capability-ticket",
                            "programme": 41,
                            "category": category,
                            "reason": "close a roadmap capability gap",
                            "bounded": True,
                        }
                    ],
                )

    def test_approved_capability_ticket_is_delegated_once_and_never_mid_ticket(
        self,
    ) -> None:
        snapshot = prepared_snapshot(intent="coordinate")
        snapshot["stewardship"] = {
            "capability": {
                "issue": 45,
                "title": "Add security scanning",
                "category": "security_scanning",
                "reason": "protect the release pipeline",
                "approved": True,
            }
        }

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "delegate-capability")
        self.assertFalse(outcome["root_mutation_permitted"])
        delegation = outcome["requested_effects"][0]
        self.assertEqual(delegation["router"], "ask-matt")
        self.assertEqual(delegation["workflow"], "/implement")
        self.assertEqual(delegation["lane"], "capability")
        self.assertEqual(delegation["scope"], {"issues": [45]})
        self.assertFalse(delegation["apply_in_root"])

        snapshot["stewardship"]["delivery_ticket_active"] = True
        stopped = run_scenario(snapshot)

        self.assertEqual(stopped["decision"], "stop")
        self.assertEqual(stopped["reason"], "active-delivery-ticket")
        self.assertEqual(stopped["requested_effects"], [])

    def test_skill_capability_records_provenance_and_gates_untrusted_publishers(
        self,
    ) -> None:
        snapshot = prepared_snapshot(intent="coordinate")
        snapshot["repository"]["skill_publisher_allowlist"] = ["trusted-lab"]
        snapshot["repository"]["public_skill_source_allowlist"] = [
            "registry.example/release-skill"
        ]
        snapshot["stewardship"] = {
            "capability": {
                "issue": 46,
                "title": "Install release skill",
                "category": "installed_skill",
                "reason": "make releases reproducible",
                "approved": True,
                "installation": {
                    "publisher": "trusted-lab",
                    "source": "registry.example/release-skill",
                    "version": "sha256:abc123",
                    "permissions": ["repository:read"],
                    "reason": "inspect release metadata",
                    "provider_response": "must-not-be-copied",
                },
            }
        }

        outcome = run_scenario(snapshot)

        delegation = outcome["requested_effects"][0]
        self.assertEqual(
            delegation["capability_provenance"],
            {
                "publisher": "trusted-lab",
                "source": "registry.example/release-skill",
                "version": "sha256:abc123",
                "permissions": ["repository:read"],
                "reason": "inspect release metadata",
            },
        )
        self.assertNotIn("must-not-be-copied", json.dumps(outcome))
        self.assertTrue(delegation["implementation_contract"]["tdd"])
        self.assertEqual(
            delegation["implementation_contract"]["stop_before"],
            ["merge", "ticket-selection"],
        )

        snapshot["stewardship"]["capability"]["installation"]["publisher"] = (
            "unknown-publisher"
        )
        stopped = run_scenario(snapshot)

        self.assertEqual(stopped["decision"], "stop")
        self.assertEqual(stopped["reason"], "publisher-approval-required")
        self.assertEqual(stopped["requested_effects"][0]["gate"], "publisher")
        self.assertNotIn("registry.example", json.dumps(stopped))

        approved_scope = {
            "publisher": "unknown-publisher",
            "source": "registry.example/release-skill",
            "version": "sha256:abc123",
            "permissions": ["repository:read"],
            "reason": "inspect release metadata",
        }
        snapshot["approvals"] = {
            "unverified_publisher": {
                "approved": True,
                "scope": approved_scope,
            }
        }
        approved = run_scenario(snapshot)

        self.assertEqual(approved["decision"], "delegate-capability")
        self.assertEqual(
            approved["requested_effects"][0]["capability_provenance"][
                "publisher"
            ],
            "unknown-publisher",
        )

        snapshot["stewardship"]["capability"]["installation"].pop("version")
        snapshot["stewardship"]["capability"]["installation"]["publisher"] = (
            "trusted-lab"
        )
        without_available_version = run_scenario(snapshot)

        self.assertEqual(without_available_version["decision"], "delegate-capability")
        self.assertNotIn(
            "version",
            without_available_version["requested_effects"][0][
                "capability_provenance"
            ],
        )

        snapshot["stewardship"]["capability"]["approved"] = False
        proposal = run_scenario(snapshot)

        self.assertEqual(proposal["decision"], "propose-capability")
        self.assertEqual(
            proposal["requested_effects"][0]["capability_provenance"],
            without_available_version["requested_effects"][0][
                "capability_provenance"
            ],
        )

        snapshot["repository"]["public_skill_source_allowlist"] = []
        unsafe_source = run_invalid_scenario(snapshot)

        self.assertEqual(unsafe_source.returncode, 2)
        self.assertNotIn("registry.example", unsafe_source.stderr)

    def test_research_radar_links_roadmap_decisions_to_urgency_cadences(
        self,
    ) -> None:
        cadences = {
            "decision_active": "weekly",
            "default": "monthly",
            "slow_moving": "quarterly",
        }
        for urgency, cadence in cadences.items():
            with self.subTest(urgency=urgency):
                snapshot = prepared_snapshot(intent="coordinate")
                snapshot["stewardship"] = {
                    "research": {
                        "question": "Has the reproducible baseline changed?",
                        "roadmap_decision": "decision-42-serving-target",
                        "urgency": urgency,
                        "approved": False,
                    }
                }

                outcome = run_scenario(snapshot)

                self.assertEqual(outcome["decision"], "record-research-radar")
                self.assertFalse(outcome["root_mutation_permitted"])
                self.assertEqual(
                    outcome["requested_effects"],
                    [
                        {
                            "effect": "record-research-radar",
                            "programme": 41,
                            "question": "Has the reproducible baseline changed?",
                            "roadmap_decision": "decision-42-serving-target",
                            "cadence": cadence,
                            "create_schedule": False,
                        }
                    ],
                )

        snapshot = prepared_snapshot(intent="coordinate")
        snapshot["repository"]["research_cadences"] = {
            "decision_active": "biweekly"
        }
        snapshot["stewardship"] = {
            "research": {
                "question": "Has the reproducible baseline changed?",
                "roadmap_decision": "decision-42-serving-target",
                "urgency": "decision_active",
                "approved": False,
            }
        }

        outcome = run_scenario(snapshot)

        self.assertEqual(
            outcome["requested_effects"][0]["cadence"], "biweekly"
        )

    def test_approved_research_is_fresh_read_only_and_may_run_with_delivery(
        self,
    ) -> None:
        snapshot = prepared_snapshot(intent="coordinate")
        snapshot["tasks"] = [
            {
                "id": "delivery-active",
                "state": "running",
                "lane": "delivery",
                "mutating": True,
            }
        ]
        snapshot["stewardship"] = {
            "research": {
                "issue": 47,
                "title": "Recheck serving baseline",
                "question": "Has the reproducible baseline changed?",
                "roadmap_decision": "decision-42-serving-target",
                "urgency": "decision_active",
                "approved": True,
                "read_only": True,
            }
        }

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "delegate-research")
        delegation = outcome["requested_effects"][0]
        self.assertEqual(delegation["router"], "ask-matt")
        self.assertEqual(delegation["workflow"], "/research")
        self.assertTrue(delegation["fresh_task"])
        self.assertTrue(delegation["read_only"])
        self.assertEqual(
            delegation["research_contract"],
            {
                "roadmap_decision": "decision-42-serving-target",
                "cadence": "weekly",
                "sources": "primary",
                "reproducible_evidence": "where-possible",
                "synthesis": "delta-against-recorded-understanding",
            },
        )
        self.assertNotIn("branch", delegation)

        snapshot["stewardship"]["research"]["read_only"] = False
        stopped = run_scenario(snapshot)

        self.assertEqual(stopped["decision"], "stop")
        self.assertEqual(stopped["reason"], "active-mutating-task")

        snapshot["stewardship"]["research"]["read_only"] = True
        snapshot["tasks"] = [
            {
                "id": "unsafe-research-active",
                "state": "running",
                "lane": "research",
                "read_only": False,
                "approved": True,
            }
        ]
        stopped = run_scenario(snapshot)

        self.assertEqual(stopped["decision"], "stop")
        self.assertEqual(stopped["reason"], "concurrency-not-permitted")

    def test_material_research_delta_creates_decision_ticket_without_architecture_change(
        self,
    ) -> None:
        snapshot = prepared_snapshot(intent="coordinate")
        snapshot["stewardship"] = {
            "research_result": {
                "research_issue": 47,
                "roadmap_decision": "decision-42-serving-target",
                "delta_synthesis": "The reproducible baseline moved materially.",
                "material": True,
            }
        }

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "propose-decision-ticket")
        self.assertFalse(outcome["architecture_mutation_permitted"])
        self.assertFalse(outcome["root_mutation_permitted"])
        self.assertEqual(
            outcome["requested_effects"],
            [
                {
                    "effect": "create-decision-ticket",
                    "programme": 41,
                    "research_issue": 47,
                    "roadmap_decision": "decision-42-serving-target",
                    "delta_synthesis": (
                        "The reproducible baseline moved materially."
                    ),
                    "mutate_architecture": False,
                }
            ],
        )

    def test_persistent_external_changes_require_exact_approval_then_delegate(
        self,
    ) -> None:
        for kind in (
            "external_schedule",
            "external_service",
            "persistent_automation",
        ):
            with self.subTest(kind=kind):
                snapshot = prepared_snapshot(intent="coordinate")
                scope = {"kind": kind, "resource": "research-radar"}
                snapshot["stewardship"] = {
                    "persistent_change": {
                        "issue": 48,
                        "title": "Automate research radar",
                        "kind": kind,
                        "scope": scope,
                    }
                }

                stopped = run_scenario(snapshot)

                self.assertEqual(stopped["decision"], "stop")
                self.assertEqual(
                    stopped["reason"], "persistent-change-approval-required"
                )
                blocker = stopped["requested_effects"][0]
                self.assertEqual(blocker["effect"], "record-blocker")
                self.assertEqual(blocker["gate"], "persistent-change")

                snapshot["approvals"] = {
                    "persistent_change": {
                        "approved": True,
                        "scope": scope,
                    }
                }
                outcome = run_scenario(snapshot)

                self.assertEqual(outcome["decision"], "delegate-capability")
                delegation = outcome["requested_effects"][0]
                self.assertEqual(delegation["workflow"], "/implement")
                self.assertEqual(delegation["lane"], "capability")
                self.assertEqual(
                    delegation["persistent_change"],
                    {"kind": kind, "scope": scope, "approved": True},
                )
                self.assertFalse(delegation["apply_in_root"])

                snapshot["stewardship"]["delivery_ticket_active"] = True
                mid_ticket = run_scenario(snapshot)

                self.assertEqual(mid_ticket["decision"], "stop")
                self.assertEqual(mid_ticket["reason"], "active-delivery-ticket")

                snapshot["stewardship"].pop("delivery_ticket_active")
                mismatched_kind = (
                    "external_service"
                    if kind != "external_service"
                    else "external_schedule"
                )
                snapshot["stewardship"]["persistent_change"]["scope"] = {
                    "kind": mismatched_kind,
                    "resource": "research-radar",
                }
                invalid = run_invalid_scenario(snapshot)

                self.assertEqual(invalid.returncode, 2)

    def test_stewardship_delegations_enforce_policy_and_isolation_gates(
        self,
    ) -> None:
        capability = prepared_snapshot(intent="coordinate")
        capability["repository"]["isolated_workspaces"] = False
        capability["stewardship"] = {
            "capability": {
                "issue": 45,
                "title": "Add security scanning",
                "category": "security_scanning",
                "reason": "protect releases",
                "approved": True,
            }
        }

        stopped = run_scenario(capability)

        self.assertEqual(stopped["decision"], "stop")
        self.assertEqual(stopped["reason"], "isolated-workspace-unavailable")

        research = prepared_snapshot(intent="coordinate")
        research["stewardship"] = {
            "research": {
                "issue": 47,
                "title": "Recheck baseline",
                "question": "Did the baseline change?",
                "roadmap_decision": "decision-42-serving-target",
                "urgency": "decision_active",
                "approved": True,
                "read_only": True,
                "gates": {"ready_for_human": True},
            }
        }

        stopped = run_scenario(research)

        self.assertEqual(stopped["decision"], "stop")
        self.assertEqual(stopped["reason"], "ready-for-human")
        self.assertEqual(stopped["requested_effects"][0]["gate"], "ready-for-human")

        research["stewardship"]["research"]["gates"] = {}
        research["repository"]["isolated_workspaces"] = False
        stopped = run_scenario(research)

        self.assertEqual(stopped["decision"], "stop")
        self.assertEqual(stopped["reason"], "isolated-workspace-unavailable")

    def test_research_exception_does_not_mask_multiple_mutating_tasks(self) -> None:
        snapshot = prepared_snapshot(intent="coordinate")
        snapshot["tasks"] = [
            {
                "id": f"delivery-{index}",
                "state": "running",
                "lane": "delivery",
                "mutating": True,
            }
            for index in (1, 2)
        ]
        snapshot["stewardship"] = {
            "research": {
                "issue": 47,
                "title": "Recheck baseline",
                "question": "Did the baseline change?",
                "roadmap_decision": "decision-42-serving-target",
                "urgency": "decision_active",
                "approved": True,
                "read_only": True,
            }
        }

        outcome = run_scenario(snapshot)

        self.assertEqual(outcome["decision"], "stop")
        self.assertEqual(outcome["reason"], "multiple-mutating-tasks")


if __name__ == "__main__":
    unittest.main()
