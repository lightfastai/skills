#!/usr/bin/env python3
"""Evaluate one provider-neutral orchestration snapshot."""

import json
import sys
from typing import Any, Dict


def trace(snapshot: Dict[str, Any]) -> Dict[str, Any]:
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
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"invalid orchestration snapshot: {error}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
