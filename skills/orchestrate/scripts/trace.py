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
            "branch": task.get("branch"),
        }
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

    requested_effects = []
    if reconciled != checkpoint:
        requested_effects.append(
            {
                "effect": "update-checkpoint",
                "comment_id": comment["id"],
                "checkpoint": reconciled,
            }
        )

    return {
        "decision": "recover",
        "programme": programme["issue"],
        "ticket": ticket["issue"],
        "lifecycle_state": reconciled["state"],
        "checkpoint_comment": comment["id"],
        "checkpoint": reconciled,
        "conflicts": conflicts,
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

    ready = [
        ticket
        for ticket in snapshot["tickets"]
        if ticket["state"] == "ready" and not ticket.get("blocked_by", [])
    ]
    if len(ready) != 1:
        raise ValueError("the coordination tracer requires exactly one ready ticket")

    ticket = ready[0]
    programme_issue = programme["issue"]
    ticket_issue = ticket["issue"]
    direct_implementation = (
        snapshot.get("user_instruction", {}).get("intent") == "implement"
    )
    return {
        "decision": "refuse-and-delegate" if direct_implementation else "delegate",
        "root_request": "refused" if direct_implementation else "coordination",
        "selected_ticket": ticket_issue,
        "root_mutation_permitted": False,
        "requested_effects": [
            {
                "effect": "delegate",
                "router": "ask-matt",
                "programme": programme_issue,
                "issue": ticket_issue,
                "fresh_task": True,
                "task_title": (
                    f"[programme #{programme_issue}] {ticket['title']}"
                ),
                "scope": {"issues": [ticket_issue]},
            }
        ],
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
