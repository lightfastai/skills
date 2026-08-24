#!/usr/bin/env python3
"""Evaluate one provider-neutral orchestration snapshot."""

import json
import sys
from datetime import datetime
from typing import Any, Dict


CHECKPOINT_FIELDS = {
    "version",
    "state",
    "task_id",
    "branch",
    "pull_request",
    "attempt",
    "verified_commit",
    "blocker",
    "next_action",
    "updated_at",
}
CONFLICT_FIELDS = {"task_id", "branch", "pull_request", "verified_commit"}
LIFECYCLE_STATES = {"ready", "active", "waiting", "done"}
ASK_MATT_ROUTES = {
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
REPOSITORY_MUTATING_INTENTS = {
    "implementation",
    "prototype",
    "architecture",
    "codebase_health",
}


def parse_timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("invalid timestamp")
    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if timestamp.utcoffset() is None:
        raise ValueError("checkpoint and evidence timestamps require an offset")
    return timestamp


def is_commit(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def recover(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    tracker = snapshot["tracker"]
    programmes = [
        programme
        for programme in tracker["programmes"]
        if programme["state"] == "active"
    ]
    if len(programmes) != 1:
        raise ValueError("recovery requires exactly one active programme")

    programme = programmes[0]
    current_ticket = programme["current_ticket"]
    if current_ticket not in programme["tickets"]:
        raise ValueError("current ticket is not part of the active programme")
    tickets = [
        ticket
        for ticket in tracker["tickets"]
        if ticket["issue"] == current_ticket
    ]
    if len(tickets) != 1:
        raise ValueError("recovery requires exactly one current programme ticket")
    ticket = tickets[0]
    comments = ticket["checkpoint_comments"]
    if len(comments) != 1:
        raise ValueError("recovery requires exactly one checkpoint comment")
    comment = comments[0]
    checkpoint = comment["checkpoint"]
    missing_fields = CHECKPOINT_FIELDS.difference(checkpoint)
    unexpected_fields = set(checkpoint).difference(CHECKPOINT_FIELDS)
    if checkpoint.get("version") != 1:
        raise ValueError("recovery requires a version-one checkpoint")
    if missing_fields or unexpected_fields:
        raise ValueError("invalid version-one checkpoint fields")
    if checkpoint["state"] not in LIFECYCLE_STATES:
        raise ValueError("unknown checkpoint state")
    parse_timestamp(checkpoint["updated_at"])

    reconciled = dict(checkpoint)
    conflicts = []
    completion_proven = False
    completion_commit = None

    def apply_newer(evidence: Dict[str, Any], updated_at: str) -> None:
        checkpoint_updated_at = reconciled["updated_at"]
        evidence_time = parse_timestamp(updated_at)
        checkpoint_time = parse_timestamp(checkpoint_updated_at)
        for field, live_value in evidence.items():
            checkpoint_value = reconciled.get(field)
            if (
                field in CONFLICT_FIELDS
                and checkpoint_value is not None
                and live_value is not None
                and checkpoint_value != live_value
            ):
                conflicts.append(
                    {
                        "field": field,
                        "resolution": (
                            "live-newer"
                            if evidence_time > checkpoint_time
                            else "checkpoint-newer"
                            if evidence_time < checkpoint_time
                            else "unresolved"
                        ),
                    }
                )
        if evidence_time <= checkpoint_time:
            return
        for field, live_value in evidence.items():
            reconciled[field] = live_value
        reconciled["updated_at"] = updated_at

    task = None
    live_tasks = [task for task in snapshot["tasks"] if task["issue"] == ticket["issue"]]
    if live_tasks:
        task = max(
            live_tasks,
            key=lambda candidate: parse_timestamp(candidate["updated_at"]),
        )
        task_state = "waiting" if task["state"] == "failed" else "active"
        task_evidence = {
            "state": task_state,
            "task_id": task["id"],
        }
        if task.get("branch") is not None:
            task_evidence["branch"] = task["branch"]
        if task_state == "waiting":
            task_evidence.update(
                {
                    "blocker": task["blocker"],
                    "next_action": task["next_action"],
                }
            )
        else:
            task_evidence.update(
                {
                    "blocker": None,
                    "next_action": task.get("next_action", "watch active task"),
                }
            )
        apply_newer(task_evidence, task["updated_at"])

    live_branches = [
        branch
        for branch in snapshot["repository"].get("branches", [])
        if branch["issue"] == ticket["issue"]
    ]
    if live_branches:
        branch = max(
            live_branches,
            key=lambda candidate: parse_timestamp(candidate["updated_at"]),
        )
        apply_newer({"branch": branch["name"]}, branch["updated_at"])

    pull_request = None
    live_pull_requests = [
        pull_request
        for pull_request in snapshot["pull_requests"]
        if pull_request["issue"] == ticket["issue"]
    ]
    if live_pull_requests:
        pull_request = max(
            live_pull_requests,
            key=lambda candidate: parse_timestamp(candidate["updated_at"]),
        )
        apply_newer(
            {
                "state": "active",
                "branch": pull_request["branch"],
                "pull_request": pull_request["url"],
            },
            pull_request["updated_at"],
        )

        main = snapshot["repository"].get("main", {})
        verified_commit = main.get("verified_commit")
        verified_at = main.get("verified_at")
        merge_matches_main = (
            pull_request["state"] == "merged"
            and is_commit(verified_commit)
            and verified_commit == pull_request.get("merge_commit")
        )
        verification_recorded = (
            main.get("verification_evidence_recorded") is True
        )
        if merge_matches_main and verification_recorded and verified_at is not None:
            apply_newer({"verified_commit": verified_commit}, verified_at)

        if (
            merge_matches_main
            and verification_recorded
            and verified_at is not None
            and ticket.get("acceptance_criteria_checked") is True
            and ticket["state"] == "closed"
        ):
            completion_proven = True
            completion_commit = verified_commit
            done_at = max(
                (
                    pull_request["updated_at"],
                    verified_at,
                    ticket["closed_at"],
                ),
                key=parse_timestamp,
            )
            apply_newer(
                {
                    "state": "done",
                    "verified_commit": verified_commit,
                    "blocker": None,
                    "next_action": "none",
                },
                done_at,
            )

    checkpoint_done_confirmed = (
        completion_proven
        and reconciled["state"] == "done"
        and reconciled["verified_commit"] == completion_commit
    )
    if checkpoint["state"] == "done" and not checkpoint_done_confirmed:
        reconciled.update(
            {
                "state": "waiting",
                "blocker": "done checkpoint lacks required live completion evidence",
                "next_action": (
                    "reconcile merge, verification, acceptance, and issue evidence"
                ),
            }
        )
        conflicts.append(
            {"field": "state", "resolution": "live-evidence-required"}
        )

    repository_progress = any(
        branch.get("head_commit") for branch in live_branches
    ) or any(pull_request.get("head_commit") for pull_request in live_pull_requests)
    stale = bool(
        task is not None
        and task["state"] in {"lost", "unavailable"}
        and task.get("resumable") is False
        and not repository_progress
    )

    decision = "recover"
    notifications = []
    watch_cursor = (
        task.get("native_wait", {}).get("after_cursor")
        if task is not None
        else None
    )
    meaningful_transitions = {
        "lifecycle",
        "blocker",
        "pull_request",
        "checks",
        "verification",
    }
    events = snapshot.get("events", [])
    unseen_events = events
    if watch_cursor is not None:
        for index, event in enumerate(events):
            if event.get("cursor") == watch_cursor:
                unseen_events = events[index + 1 :]
    for event in unseen_events:
        if event.get("kind") in meaningful_transitions:
            notification = {"transition": event["kind"]}
            if "state" in event:
                notification["state"] = event["state"]
            notifications.append(notification)
        if event.get("cursor") is not None:
            watch_cursor = event["cursor"]
    recovery_effect = None
    failure_is_current = (
        task is not None
        and task["state"] == "failed"
        and task["id"] == checkpoint["task_id"]
        and parse_timestamp(task["updated_at"])
        >= parse_timestamp(checkpoint["updated_at"])
    )
    task_cannot_resume = bool(
        task is not None
        and task["state"] in {"failed", "lost", "unavailable"}
        and task.get("resumable") is False
    )
    duplicate_work = len(live_branches) > 1 or len(live_pull_requests) > 1
    def record_transition(evidence: Dict[str, Any]) -> None:
        observed_at = snapshot.get("observed_at", task["updated_at"])
        parse_timestamp(observed_at)
        reconciled.update(evidence)
        reconciled["updated_at"] = observed_at

    if duplicate_work and (failure_is_current or task_cannot_resume):
        record_transition(
            {
                "state": "waiting",
                "branch": checkpoint["branch"],
                "pull_request": checkpoint["pull_request"],
                "attempt": checkpoint["attempt"],
                "blocker": (
                    "multiple implementation branches or pull requests "
                    "prevent safe recovery"
                ),
                "next_action": "resolve duplicate branch or pull-request evidence",
            }
        )
        decision = "wait"
        notifications.append({"transition": "blocker", "state": "waiting"})
    elif (
        failure_is_current
        and checkpoint["attempt"] == 1
        and task.get("resumable") is True
    ):
        record_transition(
            {
                "state": "active",
                "attempt": 2,
                "blocker": None,
                "next_action": f"resume {task['id']}",
            }
        )
        decision = "recover-task"
        recovery_effect = {
            "effect": "resume-task",
            "task_id": task["id"],
            "issue": ticket["issue"],
            "reuse": {
                "checkpoint_comment": comment["id"],
                "branch": reconciled["branch"],
                "pull_request": reconciled["pull_request"],
            },
        }
        notifications.append({"transition": "recovery-attempt", "attempt": 2})
    elif (
        (failure_is_current or stale)
        and checkpoint["attempt"] == 1
        and task.get("resumable") is False
    ):
        record_transition(
            {
                "state": "active",
                "task_id": None,
                "attempt": 2,
                "blocker": None,
                "next_action": "await replacement task",
            }
        )
        decision = "replace-task"
        recovery_effect = {
            "effect": "replace-task",
            "router": "ask-matt",
            "workflow": "/implement",
            "issue": ticket["issue"],
            "replaces_task": task["id"],
            "attempt": 2,
            "reuse": {
                "checkpoint_comment": comment["id"],
                "branch": reconciled["branch"],
                "pull_request": reconciled["pull_request"],
            },
            "create_branch": False,
            "create_pull_request": False,
        }
        notifications.append({"transition": "recovery-attempt", "attempt": 2})
    elif (failure_is_current or stale) and checkpoint["attempt"] >= 2:
        record_transition(
            {
                "state": "waiting",
                "blocker": task.get(
                    "blocker", "task is unavailable and cannot resume"
                ),
                "next_action": task.get(
                    "next_action", "request human intervention"
                ),
            }
        )
        decision = "wait"
        notifications.append(
            {"transition": "recovery-exhausted", "attempt": checkpoint["attempt"]}
        )

    requested_effects = []
    if reconciled != checkpoint:
        requested_effects.append(
            {
                "effect": "update-checkpoint",
                "comment_id": comment["id"],
                "checkpoint": reconciled,
            }
        )

    if recovery_effect is not None:
        requested_effects.append(recovery_effect)

    if task is not None and task["state"] in {"running", "active"}:
        native_wait = task.get("native_wait")
        if native_wait is not None:
            decision = "watch"
            requested_effects.append(
                {
                    "effect": "wait-task",
                    "task_id": task["id"],
                    "after_cursor": watch_cursor,
                }
            )
            if pull_request is not None:
                requested_effects.append(
                    {
                        "effect": "watch-repository-checks",
                        "pull_request": pull_request["url"],
                        "head_commit": pull_request.get("head_commit"),
                    }
                )
    elif (
        decision == "recover"
        and task is not None
        and task["state"] in {"lost", "unavailable"}
        and repository_progress
        and pull_request is not None
    ):
        decision = "watch"
        requested_effects.append(
            {
                "effect": "watch-repository-checks",
                "pull_request": pull_request["url"],
                "head_commit": pull_request.get("head_commit"),
            }
        )

    return {
        "decision": decision,
        "programme": programme["issue"],
        "ticket": ticket["issue"],
        "lifecycle_state": reconciled["state"],
        "checkpoint_comment": comment["id"],
        "checkpoint": reconciled,
        "conflicts": conflicts,
        "notifications": notifications,
        "stale": stale,
        "root_mutation_permitted": False,
        "requested_effects": requested_effects,
    }


def trace(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    if "tracker" in snapshot:
        return recover(snapshot)

    programme = snapshot["programme"]
    if programme["state"] != "active":
        return {
            "decision": "stop",
            "reason": "no-active-programme",
            "selected_ticket": None,
            "root_mutation_permitted": False,
            "requested_effects": [],
        }

    active_tasks = [
        task
        for task in snapshot.get("tasks", [])
        if task.get("state") in {"running", "active"}
    ]
    active_mutating_tasks = [
        task
        for task in active_tasks
        if task.get("mutating") is True
        and task.get("lane") in {"delivery", "capability"}
    ]
    if active_mutating_tasks:
        return {
            "decision": "stop",
            "reason": "active-mutating-task",
            "selected_ticket": None,
            "root_mutation_permitted": False,
            "requested_effects": [],
        }
    concurrent_tasks_permitted = all(
        task.get("lane") == "research"
        and task.get("read_only") is True
        and task.get("approved") is True
        for task in active_tasks
    )
    if active_tasks and not concurrent_tasks_permitted:
        return {
            "decision": "stop",
            "reason": "concurrency-not-permitted",
            "selected_ticket": None,
            "root_mutation_permitted": False,
            "requested_effects": [],
        }

    frontier = [
        ticket
        for ticket in snapshot["tickets"]
        if ticket["state"] == "ready" and not ticket.get("blocked_by", [])
    ]
    if not frontier:
        raise ValueError("the coordination tracer requires a dependency frontier")

    approved_order = programme["approved_order"]
    frontier_by_issue = {ticket["issue"]: ticket for ticket in frontier}
    ordered_frontier_issues = [
        issue for issue in approved_order if issue in frontier_by_issue
    ]
    if not ordered_frontier_issues:
        raise ValueError("the dependency frontier requires approved order")

    override_issue = snapshot.get("user_instruction", {}).get("override_issue")
    override_ticket = frontier_by_issue.get(override_issue)
    override_gates = (override_ticket or {}).get("gates", {})
    override_is_safe = override_ticket is not None and not any(
        override_gates.get(gate)
        for gate in ("safety", "approval", "adr_conflict")
    )
    ticket = (
        override_ticket
        if override_is_safe
        else frontier_by_issue[ordered_frontier_issues[0]]
    )
    programme_issue = programme["issue"]
    ticket_issue = ticket["issue"]
    for gate in ("safety", "approval"):
        if ticket.get("gates", {}).get(gate):
            return {
                "decision": "stop",
                "reason": f"{gate}-gate",
                "selected_ticket": ticket_issue,
                "root_mutation_permitted": False,
                "requested_effects": [],
            }
    if ticket.get("gates", {}).get("adr_conflict"):
        return {
            "decision": "stop",
            "reason": "adr-conflict",
            "selected_ticket": ticket_issue,
            "root_mutation_permitted": False,
            "requested_effects": [
                {
                    "effect": "record-blocker",
                    "issue": ticket_issue,
                    "state": "waiting",
                    "gate": "adr",
                }
            ],
        }
    intent = snapshot.get("user_instruction", {}).get("intent", "coordinate")
    routed_intent = (
        ticket.get("intent", "implementation")
        if intent == "coordinate"
        else "implementation"
        if intent == "implement"
        else intent
    )
    if routed_intent not in ASK_MATT_ROUTES:
        raise ValueError("Ask Matt cannot route the requested intent")
    repository_mutating = routed_intent in REPOSITORY_MUTATING_INTENTS
    if repository_mutating and not snapshot["repository"].get(
        "isolated_workspaces", False
    ):
        return {
            "decision": "stop",
            "reason": "isolated-workspace-unavailable",
            "selected_ticket": ticket_issue,
            "root_mutation_permitted": False,
            "requested_effects": [],
        }
    direct_implementation = (
        snapshot.get("user_instruction", {}).get("intent") == "implement"
    )
    delegation = {
        "effect": "delegate",
        "router": "ask-matt",
        "intent": routed_intent,
        "workflow": ASK_MATT_ROUTES[routed_intent],
        "programme": programme_issue,
        "issue": ticket_issue,
        "fresh_task": True,
        "isolated_workspace": True,
        "task_title": f"[programme #{programme_issue}] {ticket['title']}",
        "scope": {"issues": [ticket_issue]},
        "read_before_edit": [
            "repository-instructions",
            "domain-vocabulary",
            "relevant-adrs",
            "complete-issue",
        ],
    }
    if repository_mutating:
        delegation["branch"] = {"issue_specific": True, "before_edit": True}
    if routed_intent == "implementation":
        delegation.update(
            {
                "implementation_contract": {
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
            }
        )
    return {
        "decision": "refuse-and-delegate" if direct_implementation else "delegate",
        "root_request": "refused" if direct_implementation else "coordination",
        "selected_ticket": ticket_issue,
        "decisive_evidence": {
            "dependency_frontier": sorted(frontier_by_issue),
            "approved_order": approved_order,
            "human_override": (
                "honored"
                if override_is_safe
                else "rejected"
                if override_issue is not None
                else None
            ),
        },
        "root_mutation_permitted": False,
        "requested_effects": [delegation],
    }


def main() -> None:
    try:
        snapshot = json.load(sys.stdin)
        json.dump(trace(snapshot), sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
    except (AttributeError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        print("invalid orchestration snapshot", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
