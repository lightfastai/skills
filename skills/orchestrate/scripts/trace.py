#!/usr/bin/env python3
"""Evaluate one provider-neutral orchestration snapshot."""

import json
import math
import re
import sys
from datetime import datetime
from typing import Any, Dict, Optional


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
APPROVAL_GATES = {
    "credentials": (
        "credential access requires explicit approval",
        "approve the credential purpose and least-privilege access scope",
    ),
    "broad_permissions": (
        "broad permissions require explicit approval",
        "approve the exact permissions and bounded resources",
    ),
    "destructive_action": (
        "a destructive action requires explicit approval",
        "approve the exact destructive action and recovery boundary",
    ),
    "legal_terms": (
        "legal terms require explicit human approval",
        "have an authorized human accept the identified legal terms",
    ),
    "billing": (
        "a billing action requires explicit approval",
        "approve the exact billing action and spending boundary",
    ),
    "unverified_publisher": (
        "an unverified publisher requires explicit approval",
        "verify or explicitly approve the publisher and requested capability",
    ),
    "material_scope_expansion": (
        "the requested work materially expands the selected issue",
        "approve the exact expanded scope and update the selected issue",
    ),
}
CAPABILITY_CATEGORIES = {
    "ci",
    "security_scanning",
    "datasets",
    "experiment_tracking",
    "deployment",
    "provider_integration",
    "installed_skill",
}
RESEARCH_CADENCES = {
    "decision_active": "weekly",
    "default": "monthly",
    "slow_moving": "quarterly",
}
BOOTSTRAP_EVIDENCE = (
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
MINIMUM_CONTROL_PLANE = {
    "tracker",
    "checkpoint",
    "programme-discovery",
    "local-contract",
    "agent-discovery",
}
LOCAL_CONTRACT_PATH = "docs/agents/orchestrate.md"
LOCAL_CONTRACT_SECTIONS = (
    "orchestration-policy-version",
    "verification",
    "programme-discovery",
    "branch-and-merge-policy",
    "approval-limits",
    "skill-allowlist",
    "research-topics-and-schedules",
    "exceptions",
)


def parse_timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("invalid timestamp")
    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if timestamp.utcoffset() is None:
        raise ValueError("checkpoint and evidence timestamps require an offset")
    return timestamp


def is_commit(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def record_blocker(
    issue: int, gate: str, blocker: str, next_action: str
) -> Dict[str, Any]:
    return {
        "effect": "record-blocker",
        "issue": issue,
        "state": "waiting",
        "gate": gate,
        "blocker": blocker,
        "next_action": next_action,
    }


def capability_delegation(
    programme_issue: int,
    issue: int,
    title: str,
    **extra: Any,
) -> Dict[str, Any]:
    delegation = {
        "effect": "delegate",
        "router": "ask-matt",
        "intent": "implementation",
        "workflow": "/implement",
        "lane": "capability",
        "programme": programme_issue,
        "issue": issue,
        "fresh_task": True,
        "isolated_workspace": True,
        "task_title": f"[programme #{programme_issue}] {title}",
        "scope": {"issues": [issue]},
        "read_before_edit": [
            "repository-instructions",
            "domain-vocabulary",
            "relevant-adrs",
            "complete-issue",
        ],
        "apply_in_root": False,
        "branch": {"issue_specific": True, "before_edit": True},
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
    delegation.update(extra)
    return delegation


def is_finite_nonnegative_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return value >= 0
    return isinstance(value, float) and math.isfinite(value) and value >= 0


def json_equal_strict(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            json_equal_strict(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            json_equal_strict(left_item, right_item)
            for left_item, right_item in zip(left, right)
        )
    return left == right


def is_bounded_scope(value: Any) -> bool:
    if isinstance(value, dict):
        return bool(value) and all(
            isinstance(key, str)
            and bool(key.strip())
            and is_bounded_scope(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return bool(value) and all(is_bounded_scope(item) for item in value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        return bool(normalized) and normalized not in {"*", "all", "unbounded"}
    if isinstance(value, bool):
        return False
    return is_finite_nonnegative_number(value)


def policy_pause(
    ticket: Dict[str, Any], approvals: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    gates = ticket.get("gates", {})
    issue = ticket["issue"]
    if gates.get("ready_for_human") or "ready-for-human" in ticket.get(
        "labels", []
    ):
        return {
            "reason": "ready-for-human",
            "effect": record_blocker(
                issue,
                "ready-for-human",
                "ticket is labelled ready-for-human",
                (
                    "a human must complete or reclassify the ticket and record "
                    "the decision"
                ),
            ),
        }

    if "adr_conflict" in gates:
        decision_id = gates["adr_conflict"]
        decision_number = (
            re.search(r"(?:^ADR-|/)(\d{4})(?:[-.]|$)", decision_id, re.IGNORECASE)
            if isinstance(decision_id, str)
            else None
        )
        safe_id = (
            f"ADR-{decision_number.group(1)}"
            if decision_number is not None
            else "the applicable ADR"
        )
        return {
            "reason": "adr-conflict",
            "effect": record_blocker(
                issue,
                "adr",
                f"selected work conflicts with {safe_id}",
                f"approve a revision or exception to {safe_id} before delegation",
            ),
        }

    if "paid_model_run" in gates:
        paid_run = gates["paid_model_run"]
        manifest = (
            paid_run.get("manifest", {}) if isinstance(paid_run, dict) else {}
        )
        model_names = manifest.get("models")
        maxima = [
            manifest[name]
            for name in ("max_calls", "max_tokens")
            if name in manifest
        ]
        cost = manifest.get("estimated_cost")
        bounded = bool(
            isinstance(model_names, list)
            and model_names
            and all(
                isinstance(model, str) and bool(model.strip())
                for model in model_names
            )
            and maxima
            and all(
                isinstance(maximum, int)
                and not isinstance(maximum, bool)
                and maximum > 0
                for maximum in maxima
            )
            and isinstance(cost, dict)
            and is_finite_nonnegative_number(cost.get("amount"))
            and isinstance(cost.get("currency"), str)
            and bool(cost["currency"].strip())
        )
        approval = approvals.get("paid_model_run", {})
        if not isinstance(approval, dict):
            approval = {}
        approved = bool(
            bounded
            and approval.get("approved") is True
            and json_equal_strict(approval.get("manifest"), manifest)
        )
        if not approved:
            return {
                "reason": "paid-model-approval-required",
                "effect": record_blocker(
                    issue,
                    "paid-model-run",
                    "paid model run lacks an approved bounded manifest",
                    (
                        "approve a manifest naming models, a maximum call or "
                        "token limit, and estimated cost"
                    ),
                ),
            }

    for gate, (blocker, next_action) in APPROVAL_GATES.items():
        if gate not in gates:
            continue
        request = gates[gate]
        requested_scope = request.get("scope") if isinstance(request, dict) else None
        approval = approvals.get(gate, {})
        if not isinstance(approval, dict):
            approval = {}
        if not (
            isinstance(requested_scope, dict)
            and is_bounded_scope(requested_scope)
            and approval.get("approved") is True
            and json_equal_strict(approval.get("scope"), requested_scope)
        ):
            return {
                "reason": f"{gate.replace('_', '-')}-approval-required",
                "effect": record_blocker(
                    issue, gate.replace("_", "-"), blocker, next_action
                ),
            }
    return None


def delegation_pause(
    ticket: Dict[str, Any], approvals: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    pause = policy_pause(ticket, approvals)
    if pause is not None:
        return pause
    for gate in ("safety", "approval"):
        if not ticket.get("gates", {}).get(gate):
            continue
        blocker, next_action = (
            (
                "requested action is blocked by repository safety policy",
                "remove the unsafe action or approve a policy-compliant alternative",
            )
            if gate == "safety"
            else (
                "repository policy requires explicit approval",
                "record the exact approval and its bounded scope",
            )
        )
        return {
            "reason": f"{gate}-gate",
            "effect": record_blocker(
                ticket["issue"], gate, blocker, next_action
            ),
        }
    return None


def stopped_delegation(
    issue: Optional[int], reason: str, effects: Optional[list] = None
) -> Dict[str, Any]:
    return {
        "decision": "stop",
        "reason": reason,
        "selected_ticket": issue,
        "root_mutation_permitted": False,
        "requested_effects": effects or [],
    }


def valid_local_contract_content(content: Any, policy_version: int) -> bool:
    if (
        not isinstance(policy_version, int)
        or isinstance(policy_version, bool)
        or policy_version <= 0
        or not isinstance(content, dict)
        or not set(LOCAL_CONTRACT_SECTIONS).issubset(content)
    ):
        return False
    try:
        return bool(
            content["orchestration-policy-version"] == {"version": policy_version}
            and content["verification"]["commands"]
            and content["verification"]["evidence"]
            and content["programme-discovery"]["source"]
            and content["programme-discovery"]["active_selector"]
            and content["branch-and-merge-policy"]["branch_pattern"]
            and content["branch-and-merge-policy"]["merge_methods"]
            and content["approval-limits"]["gates"]
            and isinstance(content["skill-allowlist"]["skills"], list)
            and isinstance(content["skill-allowlist"]["publishers"], list)
            and isinstance(
                content["research-topics-and-schedules"]["topics"], list
            )
            and content["research-topics-and-schedules"]["cadences"]
            and isinstance(content["exceptions"]["items"], list)
        )
    except (KeyError, TypeError):
        return False


def bootstrap(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    request = snapshot["bootstrap"]
    evidence = request["evidence"]
    if set(evidence) != set(BOOTSTRAP_EVIDENCE) or not all(
        isinstance(evidence[name], dict) for name in BOOTSTRAP_EVIDENCE
    ):
        raise ValueError("bootstrap requires complete repository evidence")
    inspected_evidence = [
        name
        for name in BOOTSTRAP_EVIDENCE
        if evidence[name].get("present") is True
    ]
    unavailable_evidence = [
        name
        for name in BOOTSTRAP_EVIDENCE
        if evidence[name].get("present") is not True
    ]

    conventions = request.get("conventions", {})
    if not isinstance(conventions, dict):
        raise ValueError("invalid repository conventions")
    convention_evidence = {
        "tracker": "tracker_state",
        "checkpoint": "tracker_state",
        "programme_discovery": "programme_evidence",
    }
    reused = sorted(
        name
        for name, convention in conventions.items()
        if name in convention_evidence
        and isinstance(convention, dict)
        and convention.get("satisfies_contract") is True
        and evidence[convention_evidence[name]].get("present") is True
    )
    normalized_reused = [name.replace("_", "-") for name in reused]
    missing = set(MINIMUM_CONTROL_PLANE)
    missing.difference_update(normalized_reused)

    local_contract = request.get("local_contract")
    contract_status = "missing"
    if local_contract is not None:
        if not isinstance(local_contract, dict):
            raise ValueError("invalid local orchestration contract")
        runtime_state_present = local_contract.get("runtime_state_present") is True
        if not (
            local_contract.get("path") == LOCAL_CONTRACT_PATH
            and valid_local_contract_content(
                local_contract.get("content"),
                local_contract.get("policy_version"),
            )
            and not runtime_state_present
        ):
            contract_status = (
                "runtime-state-present" if runtime_state_present else "invalid"
            )
            local_contract = None
        else:
            contract_status = "candidate"
    agent_instructions = request.get("agent_instructions", {})
    if (
        isinstance(agent_instructions, dict)
        and agent_instructions.get("discovers_contract") is True
        and evidence["agent_instructions"].get("present") is True
    ):
        missing.discard("agent-discovery")

    capability_gaps = []
    approved_capabilities = []
    approved_provenance = {}
    approvals = snapshot.get("approvals", {})
    bootstrap_approval = approvals.get("bootstrap_capability", {})
    tracker = request.get("tracker", {})
    capability_tickets = tracker.get("capability_tickets", [])
    if not isinstance(capability_tickets, list):
        raise ValueError("invalid bootstrap capability tickets")
    for gap in request.get("capability_gaps", []):
        category = gap.get("category")
        supplied_reason = gap.get("reason")
        if category not in CAPABILITY_CATEGORIES or not (
            isinstance(supplied_reason, str) and supplied_reason.strip()
        ):
            raise ValueError("invalid bootstrap capability gap")
        reason = f"repository capability gap: {category}"
        if gap.get("approved") is True:
            issue = gap.get("issue")
            title = gap.get("title")
            approval_scope = {"issue": issue, "category": category}
            live_ticket = any(
                isinstance(ticket, dict)
                and ticket.get("issue") == issue
                and ticket.get("state") == "ready"
                for ticket in capability_tickets
            )
            exact_approval = bool(
                isinstance(bootstrap_approval, dict)
                and bootstrap_approval.get("approved") is True
                and json_equal_strict(
                    bootstrap_approval.get("scope"), approval_scope
                )
            )
            if not (
                isinstance(issue, int)
                and isinstance(title, str)
                and title.strip()
                and live_ticket
                and exact_approval
            ):
                status = "proposal"
                capability_gaps.append(
                    {"category": category, "reason": reason, "status": status}
                )
                continue
            pause = delegation_pause(gap, approvals)
            if pause is not None:
                return stopped_delegation(
                    issue, pause["reason"], [pause["effect"]]
                )
            if category == "installed_skill":
                installation = gap.get("installation", {})
                source = installation.get("source")
                publisher = installation.get("publisher")
                immutable_version = installation.get(
                    "version", installation.get("commit")
                )
                permissions = installation.get("permissions")
                installation_reason = installation.get("reason")
                if not (
                    isinstance(publisher, str)
                    and publisher.strip()
                    and isinstance(source, str)
                    and source
                    in snapshot["repository"].get(
                        "public_skill_source_allowlist", []
                    )
                    and isinstance(immutable_version, str)
                    and immutable_version.strip()
                    and isinstance(permissions, list)
                    and permissions
                    and all(
                        isinstance(permission, str) and permission.strip()
                        for permission in permissions
                    )
                    and isinstance(installation_reason, str)
                    and installation_reason.strip()
                ):
                    raise ValueError(
                        "skill capability requires auditable provenance"
                    )
                approval_provenance = {
                    key: installation[key]
                    for key in (
                        "publisher",
                        "source",
                        "version",
                        "commit",
                        "permissions",
                        "reason",
                    )
                    if key in installation
                }
                source_allowlist = snapshot["repository"].get(
                    "public_skill_source_allowlist", []
                )
                provenance = {
                    key: approval_provenance[key]
                    for key in ("publisher", "version", "commit", "permissions")
                    if key in approval_provenance
                }
                provenance["source_reference"] = (
                    "repository-public-skill-source-allowlist:"
                    f"{source_allowlist.index(source)}"
                )
                provenance["reason"] = "repository capability gap: installed_skill"
                publisher_approval = approvals.get(
                    "unverified_publisher", {}
                )
                publisher_trusted = bool(
                    installation.get("publisher_official") is True
                    or installation.get("publisher_verified") is True
                    or publisher
                    in snapshot["repository"].get(
                        "skill_publisher_allowlist", []
                    )
                    or (
                        isinstance(publisher_approval, dict)
                        and publisher_approval.get("approved") is True
                        and json_equal_strict(
                            publisher_approval.get("scope"), approval_provenance
                        )
                    )
                )
                if not publisher_trusted:
                    return stopped_delegation(
                        issue,
                        "publisher-approval-required",
                        [
                            record_blocker(
                                issue,
                                "publisher",
                                "skill publisher is not verified or allowlisted",
                                (
                                    "verify or explicitly approve the publisher "
                                    "and bounded skill provenance"
                                ),
                            )
                        ],
                    )
                approved_provenance[issue] = provenance
            approved_capabilities.append(gap)
            status = "approved"
        else:
            status = "proposal"
        capability_gaps.append(
            {"category": category, "reason": reason, "status": status}
        )
    if len(approved_capabilities) > 1:
        raise ValueError("bootstrap delegates at most one capability")

    policy = request.get("policy", {})
    published_version = policy.get("published_version")
    adopted_version = policy.get("adopted_version")
    if not (
        isinstance(published_version, int)
        and not isinstance(published_version, bool)
        and published_version > 0
        and (
            adopted_version is None
            or (
                isinstance(adopted_version, int)
                and not isinstance(adopted_version, bool)
                and adopted_version > 0
            )
        )
    ):
        raise ValueError("invalid orchestration policy versions")
    if local_contract is not None:
        if local_contract.get("policy_version") == adopted_version:
            contract_status = "adopted"
            missing.discard("local-contract")
        else:
            contract_status = "policy-version-mismatch"
            local_contract = None

    effects = []
    if missing:
        effects.append(
            {
                "effect": "propose-control-plane",
                "missing": sorted(missing),
                "minimum_only": True,
                "approval_required": True,
            }
        )
    if "local-contract" in missing:
        effects.append(
            {
                "effect": "propose-local-contract",
                "path": LOCAL_CONTRACT_PATH,
                "agent_discovery": "AGENTS.md",
                "required_sections": list(LOCAL_CONTRACT_SECTIONS),
                "runtime_state_permitted": False,
                "reviewable": True,
            }
        )
    elif "agent-discovery" in missing:
        effects.append(
            {
                "effect": "propose-agent-discovery",
                "path": "AGENTS.md",
                "contract": LOCAL_CONTRACT_PATH,
                "reviewable": True,
            }
        )
    policy_status = "current"
    if adopted_version is None:
        policy_status = "adoption-proposed"
        effects.append(
            {
                "effect": "propose-policy-adoption",
                "path": LOCAL_CONTRACT_PATH,
                "version": published_version,
                "reviewable": True,
                "silent_rewrite": False,
            }
        )
    elif adopted_version < published_version:
        change_ids = policy.get("change_ids")
        if not (
            isinstance(change_ids, list)
            and change_ids
            and all(
                isinstance(change_id, str) and is_bounded_scope(change_id)
                for change_id in change_ids
            )
        ):
            raise ValueError("policy migration requires a reviewable delta")
        policy_status = "migration-proposed"
        effects.append(
            {
                "effect": "propose-policy-migration",
                "path": LOCAL_CONTRACT_PATH,
                "from_version": adopted_version,
                "to_version": published_version,
                "reviewable": True,
                "silent_rewrite": False,
                "preserve_local_decisions": True,
                "preserve_runtime_state": True,
                "change_ids": change_ids,
                "approval_required": True,
            }
        )
    elif adopted_version > published_version:
        policy_status = "local-policy-newer"
    for gap in capability_gaps:
        if gap["status"] == "approved":
            continue
        effects.append(
            {
                "effect": "propose-capability",
                "category": gap["category"],
                "reason": gap["reason"],
                "approval_required": True,
            }
        )

    decision = "bootstrap-audit"
    if approved_capabilities:
        approved = approved_capabilities[0]
        programme_issue = request.get("programme_issue")
        if not isinstance(programme_issue, int):
            raise ValueError("approved bootstrap capability requires a programme")
        if not snapshot["repository"].get("isolated_workspaces", False):
            raise ValueError("approved bootstrap capability requires isolation")
        active_mutating_tasks = [
            task
            for task in snapshot.get("tasks", [])
            if task.get("state") in {"running", "active"}
            and task.get("mutating") is True
            and task.get("lane") in {"delivery", "capability"}
        ]
        if active_mutating_tasks:
            return stopped_delegation(
                approved["issue"], "active-mutating-task"
            )
        effects.append(
            capability_delegation(
                programme_issue,
                approved["issue"],
                approved["title"],
                **(
                    {
                        "capability_provenance": approved_provenance[
                            approved["issue"]
                        ]
                    }
                    if approved["issue"] in approved_provenance
                    else {}
                ),
            )
        )
        decision = "bootstrap-delegate-capability"

    return {
        "decision": decision,
        "audit": {
            "inspected": inspected_evidence,
            "unavailable": unavailable_evidence,
            "reused": normalized_reused,
        },
        "control_plane": {"missing": sorted(missing)},
        "contract": {
            "path": LOCAL_CONTRACT_PATH,
            "status": contract_status,
            "runtime_state_permitted": False,
        },
        "capability_gaps": capability_gaps,
        "policy": {
            "published_version": published_version,
            "adopted_version": adopted_version,
            "status": policy_status,
        },
        "root_mutation_permitted": False,
        "requested_effects": effects,
    }


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
    closure_evidence = None

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
            closure_evidence = {
                "pull_request": pull_request["url"],
                "merge_commit": pull_request.get("merge_commit"),
                "verified_main_commit": verified_commit,
                "verification_evidence_recorded": True,
                "acceptance_criteria_checked": True,
                "issue_closed": True,
            }
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

    pause = policy_pause(ticket, snapshot.get("approvals", {}))
    if pause is not None:
        observed_at = max(
            (
                snapshot.get("observed_at", reconciled["updated_at"]),
                reconciled["updated_at"],
            ),
            key=parse_timestamp,
        )
        effect = pause["effect"]
        reconciled.update(
            {
                "state": "waiting",
                "blocker": effect["blocker"],
                "next_action": effect["next_action"],
                "updated_at": observed_at,
            }
        )
        checkpoint_effects = []
        if reconciled != checkpoint:
            checkpoint_effects.append(
                {
                    "effect": "update-checkpoint",
                    "comment_id": comment["id"],
                    "checkpoint": reconciled,
                }
            )
        return {
            "decision": "wait",
            "programme": programme["issue"],
            "ticket": ticket["issue"],
            "lifecycle_state": "waiting",
            "checkpoint_comment": comment["id"],
            "checkpoint": reconciled,
            "closure_evidence": closure_evidence,
            "conflicts": conflicts,
            "notifications": [{"transition": "blocker", "state": "waiting"}],
            "stale": stale,
            "delivery_gates": None,
            "child_merge_authorized": False,
            "root_mutation_permitted": False,
            "requested_effects": checkpoint_effects,
        }

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

    delivery_gates = None
    child_merge_authorized = False
    delivered_open = bool(
        pull_request is not None
        and pull_request.get("delivered") is True
        and pull_request["state"] == "open"
    )
    delivered_merged = bool(
        pull_request is not None
        and pull_request.get("delivered") is True
        and pull_request["state"] == "merged"
        and is_commit(pull_request.get("merge_commit"))
    )
    main = snapshot["repository"].get("main", {})
    failed_verification = main.get("verification", {})
    failure_matches_merge = bool(
        delivered_merged
        and failed_verification.get("commit")
        == pull_request.get("merge_commit")
        and failed_verification.get("state") == "failed"
        and failed_verification.get("evidence_recorded") is True
    )
    failure_is_current = failure_matches_merge and (
        main.get("verified_at") is None
        or parse_timestamp(failed_verification["observed_at"])
        >= parse_timestamp(main["verified_at"])
    )

    if delivered_open:
        current_checks = pull_request.get("required_checks", [])
        checks_state = (
            "unknown"
            if "required_checks" not in pull_request
            else "failed"
            if any(check.get("state") == "failed" for check in current_checks)
            else "passed"
            if all(check.get("state") == "passed" for check in current_checks)
            else "pending"
        )
        review = pull_request.get("review", {})
        review_state = (
            "unknown"
            if "review" not in pull_request
            else "required"
            if review.get("required") is True and review.get("approved") is not True
            else "passed"
        )
        branch_state = (
            "unknown"
            if not is_commit(pull_request.get("head_commit"))
            or pull_request.get("mergeable") is None
            else "passed"
            if pull_request.get("mergeable") is True
            else "conflicting"
        )
        permitted_methods = snapshot["repository"].get("merge_policy", {}).get(
            "permitted_methods", []
        )
        supported_methods = snapshot["repository"].get(
            "supported_merge_methods", []
        )
        merge_method = next(
            (
                method
                for method in permitted_methods
                if method in supported_methods
            ),
            None,
        )
        delivery_gates = {
            "acceptance": (
                "passed"
                if ticket.get("acceptance_criteria_checked") is True
                else "failed"
            ),
            "review": review_state,
            "checks": checks_state,
            "branch": branch_state,
            "merge_policy": "passed" if merge_method is not None else "unsupported",
        }
        if all(state == "passed" for state in delivery_gates.values()):
            decision = "merge"
            requested_effects.append(
                {
                    "effect": "merge-pull-request",
                    "pull_request": pull_request["url"],
                    "head_commit": pull_request.get("head_commit"),
                    "method": merge_method,
                    "actor": "root-orchestrator",
                }
            )
        else:
            decision = "wait"
    elif failure_is_current:
        verification = failed_verification
        reconciled.update(
            {
                "state": "waiting",
                "verified_commit": None,
                "blocker": "merged main verification failed",
                "next_action": (
                    "repair merged main and rerun independent verification"
                ),
                "updated_at": verification["observed_at"],
            }
        )
        decision = "wait"
        if not any(
            effect["effect"] == "update-checkpoint"
            for effect in requested_effects
        ):
            requested_effects.insert(
                0,
                {
                    "effect": "update-checkpoint",
                    "comment_id": comment["id"],
                    "checkpoint": reconciled,
                },
            )
    elif delivered_merged and main.get("verified_commit") != pull_request.get(
        "merge_commit"
    ):
        decision = "verify-main"
        requested_effects.append(
            {
                "effect": "verify-main",
                "branch": "main",
                "commit": pull_request.get("merge_commit"),
                "independent": True,
            }
        )
    elif (
        delivered_merged
        and main.get("verified_commit") == pull_request.get("merge_commit")
        and main.get("verification_evidence_recorded")
        is True
        and ticket.get("acceptance_criteria_checked") is True
        and ticket["state"] == "open"
    ):
        decision = "close-ticket"
        requested_effects.append(
            {
                "effect": "close-ticket",
                "issue": ticket["issue"],
                "closure_evidence": {
                    "pull_request": pull_request["url"],
                    "merge_commit": pull_request.get("merge_commit"),
                    "verified_main_commit": main["verified_commit"],
                    "verification_evidence_recorded": True,
                    "acceptance_criteria_checked": True,
                },
            }
        )

    if completion_proven:
        decision = "done"
        workspace = next(
            (
                candidate
                for candidate in snapshot.get("workspaces", [])
                if candidate.get("issue") == ticket["issue"]
                and candidate.get("state") == "isolated"
                and candidate.get("branch") == reconciled.get("branch")
            ),
            None,
        )
        remote_branch = next(
            (
                candidate
                for candidate in live_branches
                if candidate.get("name") == reconciled.get("branch")
                and is_commit(candidate.get("remote_commit"))
                and candidate.get("remote_commit")
                == pull_request.get("head_commit")
            ),
            None,
        )
        if workspace is not None and remote_branch is not None:
            requested_effects.append(
                {
                    "effect": "release-workspace",
                    "issue": ticket["issue"],
                    "branch": workspace["branch"],
                    "proof": {
                        "remote_commit": remote_branch["remote_commit"],
                        "merged_commit": pull_request.get("merge_commit"),
                        "verified_main_commit": completion_commit,
                    },
                }
            )

    if (
        delivery_gates is None
        and task is not None
        and task["state"] in {"running", "active"}
    ):
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
        "closure_evidence": closure_evidence,
        "conflicts": conflicts,
        "notifications": notifications,
        "stale": stale,
        "delivery_gates": delivery_gates,
        "child_merge_authorized": child_merge_authorized,
        "root_mutation_permitted": False,
        "requested_effects": requested_effects,
    }


def chartered(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate charter resolution, authority, and one generic transition."""
    request = snapshot["chartered"]
    registry = request["registry"]
    charters = registry["charters"]
    if not isinstance(charters, list) or not charters:
        raise ValueError("a charter registry is required")

    requested_id = request.get("charter_id")
    purpose = request.get("purpose")
    candidates = [
        charter
        for charter in charters
        if (
            requested_id is not None
            and charter.get("id") == requested_id
        )
        or (
            requested_id is None
            and isinstance(purpose, str)
            and charter.get("purpose") == purpose
        )
    ]
    if len(candidates) > 1:
        return {
            "decision": "stop",
            "reason": "ambiguous-charter",
            "root_mutation_permitted": False,
            "requested_effects": [],
        }
    if len(candidates) != 1:
        return {
            "decision": "propose-adoption",
            "reason": "charter-not-registered",
            "root_mutation_permitted": False,
            "requested_effects": [],
        }

    charter = candidates[0]
    charter_id = charter["id"]
    if charter.get("state") != "registered":
        return {
            "decision": "propose-adoption",
            "reason": "charter-not-registered",
            "charter": charter_id,
            "root_mutation_permitted": False,
            "requested_effects": [],
        }

    programme_id = request["programme_id"]
    write_claims = set(charter.get("resource_claims", {}).get("write", []))
    concurrency = charter.get("concurrency", {})
    pool = concurrency.get("pool")
    ceiling = concurrency.get("mutation_ceiling")
    if not isinstance(ceiling, int) or isinstance(ceiling, bool) or ceiling < 1:
        raise ValueError("invalid mutation ceiling")
    active_writers = [
        instance
        for instance in request.get("active_instances", [])
        if instance.get("mutating") is True
        and instance.get("instance") != f"{charter_id}+{programme_id}"
    ]
    overlapping_claim = any(
        write_claims.intersection(instance.get("write_claims", []))
        for instance in active_writers
    )
    pool_at_capacity = sum(
        instance.get("pool") == pool for instance in active_writers
    ) >= ceiling
    if overlapping_claim or pool_at_capacity:
        return {
            "decision": "stop",
            "reason": "resource-conflict",
            "charter": charter_id,
            "programme": programme_id,
            "root_mutation_permitted": False,
            "requested_effects": [],
        }

    experiment = request.get("experiment")
    if charter.get("level") == "meta":
        target = request.get("target")
        if not isinstance(target, dict):
            raise ValueError("meta charter requires a target")
        bilateral = target.get("target_opt_in") is True and target.get(
            "control_plane_registration"
        ) is True
        if not bilateral:
            return {
                "decision": "stop",
                "reason": "bilateral-meta-opt-in-required",
                "charter": charter_id,
                "programme": programme_id,
                "root_mutation_permitted": False,
                "requested_effects": [],
            }
        if experiment is not None:
            assignment = experiment.get("assignment", {})
            envelope = target.get("tuning_envelope", {})
            if not assignment or any(
                control not in envelope or value not in envelope[control]
                for control, value in assignment.items()
            ):
                return {
                    "decision": "stop",
                    "reason": "tuning-envelope-violation",
                    "charter": charter_id,
                    "programme": programme_id,
                    "root_mutation_permitted": False,
                    "requested_effects": [],
                }
            bound = experiment.get("bound_assignment")
            if (
                experiment.get("work_unit_state") == "active"
                and bound is not None
                and not json_equal_strict(bound, assignment)
            ):
                return {
                    "decision": "stop",
                    "reason": "assignment-stability-violation",
                    "charter": charter_id,
                    "programme": programme_id,
                    "root_mutation_permitted": False,
                    "requested_effects": [],
                }

    completion = request.get("completion", {})
    criteria = completion.get("criteria", {})
    if criteria:
        if not all(isinstance(value, bool) for value in criteria.values()):
            raise ValueError("completion criteria must be boolean")
        if all(criteria.values()):
            return {
                "decision": "done",
                "charter": charter_id,
                "programme": programme_id,
                "lifecycle": "done",
                "decisive_evidence": {"completion": sorted(criteria)},
                "root_mutation_permitted": False,
                "requested_effects": [],
            }

    frontier = [
        unit
        for unit in request.get("work_units", [])
        if unit.get("state") == "ready" and not unit.get("blocked_by", [])
    ]
    if not frontier:
        return {
            "decision": "waiting",
            "reason": "no-ready-work-unit",
            "charter": charter_id,
            "programme": programme_id,
            "root_mutation_permitted": False,
            "requested_effects": [],
        }
    unit = frontier[0]
    intent = unit["intent"]
    permitted_routes = charter.get("routes", [])
    if intent not in permitted_routes or intent not in ASK_MATT_ROUTES:
        return {
            "decision": "stop",
            "reason": "route-not-authorized",
            "charter": charter_id,
            "programme": programme_id,
            "root_mutation_permitted": False,
            "requested_effects": [],
        }
    return {
        "decision": "delegate",
        "charter": charter_id,
        "programme": programme_id,
        "lifecycle": "ready",
        "root_mutation_permitted": False,
        "requested_effects": [
            {
                "effect": "delegate",
                "router": "ask-matt",
                "intent": intent,
                "workflow": ASK_MATT_ROUTES[intent],
                "work_unit": unit["id"],
                "authority": charter.get("adoption_authority"),
                "resource_claims": sorted(write_claims),
                "stop_condition": unit["stop_condition"],
            }
        ],
    }


def _trace(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    if "chartered" in snapshot:
        return chartered(snapshot)
    if "bootstrap" in snapshot:
        return bootstrap(snapshot)
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

    stewardship = snapshot.get("stewardship", {})
    requested_research = stewardship.get("research")
    approvals = snapshot.get("approvals", {})
    approved_read_only_research = bool(
        requested_research is not None
        and requested_research.get("approved") is True
        and requested_research.get("read_only") is True
        and delegation_pause(requested_research, approvals) is None
    )
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
    if len(active_mutating_tasks) > 1:
        return stopped_delegation(
            requested_research.get("issue")
            if requested_research is not None
            else None,
            "multiple-mutating-tasks",
        )
    research_request_concurrency_permitted = bool(
        approved_read_only_research
        and all(
            task.get("lane") in {"delivery", "capability"}
            or (
                task.get("lane") == "research"
                and task.get("read_only") is True
                and task.get("approved") is True
            )
            for task in active_tasks
        )
    )
    if active_mutating_tasks and not research_request_concurrency_permitted:
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
    if (
        active_tasks
        and not concurrent_tasks_permitted
        and not research_request_concurrency_permitted
    ):
        return {
            "decision": "stop",
            "reason": "concurrency-not-permitted",
            "selected_ticket": None,
            "root_mutation_permitted": False,
            "requested_effects": [],
        }

    capability = stewardship.get("capability")
    if capability is not None:
        category = capability.get("category")
        reason = capability.get("reason")
        if category not in CAPABILITY_CATEGORIES or not (
            isinstance(reason, str) and reason.strip()
        ):
            raise ValueError("invalid bounded capability proposal")
        provenance = None
        publisher_trusted = True
        if category == "installed_skill":
            installation = capability.get("installation", {})
            publisher = installation.get("publisher")
            source = installation.get("source")
            immutable_version = installation.get(
                "version", installation.get("commit")
            )
            permissions = installation.get("permissions")
            installation_reason = installation.get("reason")
            public_sources = snapshot["repository"].get(
                "public_skill_source_allowlist", []
            )
            if not (
                isinstance(publisher, str)
                and publisher.strip()
                and isinstance(source, str)
                and source.strip()
                and source in public_sources
                and (
                    immutable_version is None
                    or (
                        isinstance(immutable_version, str)
                        and immutable_version.strip()
                    )
                )
                and isinstance(permissions, list)
                and permissions
                and all(
                    isinstance(permission, str) and permission.strip()
                    for permission in permissions
                )
                and isinstance(installation_reason, str)
                and installation_reason.strip()
            ):
                raise ValueError("skill capability requires auditable provenance")
            provenance = {
                key: installation[key]
                for key in (
                    "publisher",
                    "source",
                    "version",
                    "commit",
                    "permissions",
                    "reason",
                )
                if key in installation
            }
            publisher_scope = {
                key: provenance[key]
                for key in (
                    "publisher",
                    "source",
                    "version",
                    "commit",
                    "permissions",
                    "reason",
                )
                if key in provenance
            }
            allowlist = snapshot["repository"].get(
                "skill_publisher_allowlist", []
            )
            publisher_approval = snapshot.get("approvals", {}).get(
                "unverified_publisher", {}
            )
            publisher_trusted = bool(
                installation.get("publisher_official") is True
                or installation.get("publisher_verified") is True
                or publisher in allowlist
                or (
                    isinstance(publisher_approval, dict)
                    and publisher_approval.get("approved") is True
                    and json_equal_strict(
                        publisher_approval.get("scope"), publisher_scope
                    )
                )
            )
        if stewardship.get("delivery_ticket_active") is True:
            return {
                "decision": "stop",
                "reason": "active-delivery-ticket",
                "selected_ticket": None,
                "root_mutation_permitted": False,
                "requested_effects": [],
            }
        if capability.get("approved") is True:
            issue = capability.get("issue")
            title = capability.get("title")
            if not isinstance(issue, int) or not (
                isinstance(title, str) and title.strip()
            ):
                raise ValueError("approved capability requires a ticket")
            pause = delegation_pause(capability, approvals)
            if pause is not None:
                return stopped_delegation(
                    issue, pause["reason"], [pause["effect"]]
                )
            if not snapshot["repository"].get("isolated_workspaces", False):
                return stopped_delegation(
                    issue, "isolated-workspace-unavailable"
                )
            if not publisher_trusted:
                return {
                    "decision": "stop",
                    "reason": "publisher-approval-required",
                    "selected_ticket": issue,
                    "root_mutation_permitted": False,
                    "requested_effects": [
                        record_blocker(
                            issue,
                            "publisher",
                            "skill publisher is not verified or allowlisted",
                            (
                                "verify or explicitly approve the publisher "
                                "and bounded skill source"
                            ),
                        )
                    ],
                }
            delegation = capability_delegation(
                programme["issue"],
                issue,
                title,
                **(
                    {"capability_provenance": provenance}
                    if provenance is not None
                    else {}
                ),
            )
            return {
                "decision": "delegate-capability",
                "selected_ticket": issue,
                "root_mutation_permitted": False,
                "requested_effects": [delegation],
            }
        proposal = {
            "effect": "create-capability-ticket",
            "programme": programme["issue"],
            "category": category,
            "reason": reason,
            "bounded": True,
        }
        if provenance is not None:
            proposal["capability_provenance"] = provenance
        return {
            "decision": "propose-capability",
            "selected_ticket": None,
            "root_mutation_permitted": False,
            "requested_effects": [proposal],
        }

    research = stewardship.get("research")
    if research is not None:
        question = research.get("question")
        roadmap_decision = research.get("roadmap_decision")
        cadence_overrides = snapshot["repository"].get(
            "research_cadences", {}
        )
        if not (
            isinstance(cadence_overrides, dict)
            and set(cadence_overrides).issubset(RESEARCH_CADENCES)
            and all(
                isinstance(cadence, str) and is_bounded_scope(cadence)
                for cadence in cadence_overrides.values()
            )
        ):
            raise ValueError("invalid research cadence policy")
        cadences = {**RESEARCH_CADENCES, **cadence_overrides}
        cadence = cadences.get(research.get("urgency"))
        if not (
            isinstance(question, str)
            and question.strip()
            and isinstance(roadmap_decision, str)
            and roadmap_decision.strip()
            and cadence is not None
        ):
            raise ValueError("invalid roadmap-linked research radar entry")
        if research.get("approved") is not True:
            return {
                "decision": "record-research-radar",
                "selected_ticket": None,
                "root_mutation_permitted": False,
                "requested_effects": [
                    {
                        "effect": "record-research-radar",
                        "programme": programme["issue"],
                        "question": question,
                        "roadmap_decision": roadmap_decision,
                        "cadence": cadence,
                        "create_schedule": False,
                    }
                ],
            }
        issue = research.get("issue")
        title = research.get("title")
        if not (
            isinstance(issue, int)
            and isinstance(title, str)
            and title.strip()
            and research.get("read_only") is True
        ):
            raise ValueError("approved research requires a read-only ticket")
        pause = delegation_pause(research, approvals)
        if pause is not None:
            return stopped_delegation(
                issue, pause["reason"], [pause["effect"]]
            )
        if not snapshot["repository"].get("isolated_workspaces", False):
            return stopped_delegation(
                issue, "isolated-workspace-unavailable"
            )
        return {
            "decision": "delegate-research",
            "selected_ticket": issue,
            "root_mutation_permitted": False,
            "requested_effects": [
                {
                    "effect": "delegate",
                    "router": "ask-matt",
                    "intent": "research",
                    "workflow": "/research",
                    "lane": "research",
                    "programme": programme["issue"],
                    "issue": issue,
                    "fresh_task": True,
                    "isolated_workspace": True,
                    "read_only": True,
                    "task_title": f"[programme #{programme['issue']}] {title}",
                    "scope": {"issues": [issue]},
                    "research_contract": {
                        "roadmap_decision": roadmap_decision,
                        "cadence": cadence,
                        "sources": "primary",
                        "reproducible_evidence": "where-possible",
                        "synthesis": "delta-against-recorded-understanding",
                    },
                }
            ],
        }

    research_result = stewardship.get("research_result")
    if research_result is not None:
        research_issue = research_result.get("research_issue")
        roadmap_decision = research_result.get("roadmap_decision")
        delta_synthesis = research_result.get("delta_synthesis")
        if not (
            isinstance(research_issue, int)
            and isinstance(roadmap_decision, str)
            and roadmap_decision.strip()
            and isinstance(delta_synthesis, str)
            and delta_synthesis.strip()
        ):
            raise ValueError("invalid research delta synthesis")
        effect = {
            "effect": "record-research-delta",
            "programme": programme["issue"],
            "research_issue": research_issue,
            "roadmap_decision": roadmap_decision,
            "delta_synthesis": delta_synthesis,
            "mutate_architecture": False,
        }
        decision = "record-research-delta"
        if research_result.get("material") is True:
            effect["effect"] = "create-decision-ticket"
            decision = "propose-decision-ticket"
        return {
            "decision": decision,
            "selected_ticket": None,
            "architecture_mutation_permitted": False,
            "root_mutation_permitted": False,
            "requested_effects": [effect],
        }

    persistent_change = stewardship.get("persistent_change")
    if persistent_change is not None:
        issue = persistent_change.get("issue")
        title = persistent_change.get("title")
        kind = persistent_change.get("kind")
        scope = persistent_change.get("scope")
        if not (
            isinstance(issue, int)
            and isinstance(title, str)
            and title.strip()
            and kind
            in {
                "external_schedule",
                "external_service",
                "persistent_automation",
            }
            and isinstance(scope, dict)
            and is_bounded_scope(scope)
            and scope.get("kind") == kind
        ):
            raise ValueError("invalid bounded persistent change")
        if stewardship.get("delivery_ticket_active") is True:
            return stopped_delegation(issue, "active-delivery-ticket")
        pause = delegation_pause(persistent_change, approvals)
        if pause is not None:
            return stopped_delegation(
                issue, pause["reason"], [pause["effect"]]
            )
        if not snapshot["repository"].get("isolated_workspaces", False):
            return stopped_delegation(
                issue, "isolated-workspace-unavailable"
            )
        approval = approvals.get("persistent_change", {})
        if not (
            isinstance(approval, dict)
            and approval.get("approved") is True
            and json_equal_strict(approval.get("scope"), scope)
        ):
            return {
                "decision": "stop",
                "reason": "persistent-change-approval-required",
                "selected_ticket": issue,
                "root_mutation_permitted": False,
                "requested_effects": [
                    record_blocker(
                        issue,
                        "persistent-change",
                        "persistent external change requires explicit approval",
                        "approve the exact external change and bounded scope",
                    )
                ],
            }
        return {
            "decision": "delegate-capability",
            "selected_ticket": issue,
            "root_mutation_permitted": False,
            "requested_effects": [
                capability_delegation(
                    programme["issue"],
                    issue,
                    title,
                    persistent_change={
                        "kind": kind,
                        "scope": scope,
                        "approved": True,
                    },
                )
            ],
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
    override_is_safe = bool(
        override_ticket is not None
        and delegation_pause(override_ticket, approvals) is None
    )
    ticket = (
        override_ticket
        if override_is_safe
        else frontier_by_issue[ordered_frontier_issues[0]]
    )
    programme_issue = programme["issue"]
    ticket_issue = ticket["issue"]
    pause = delegation_pause(ticket, approvals)
    if pause is not None:
        return stopped_delegation(
            ticket_issue, pause["reason"], [pause["effect"]]
        )
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


def configured_integrations(snapshot: Dict[str, Any]) -> list:
    integrations = snapshot.get("repository", {}).get(
        "configured_integrations", {}
    )
    if not isinstance(integrations, dict):
        raise ValueError("invalid configured integrations")
    for name, integration in integrations.items():
        if not (
            isinstance(name, str)
            and name.strip()
            and isinstance(integration, dict)
            and integration.get("source") == "installed-skill"
            and integration.get("approved") is True
            and integration.get("capability") == name
            and isinstance(integration.get("resolver"), str)
            and integration["resolver"].strip()
        ):
            raise ValueError("invalid configured integration")
    return sorted(integrations)


def trace(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    result = _trace(snapshot)
    integrations = configured_integrations(snapshot)
    if integrations:
        result.setdefault("decisive_evidence", {})[
            "configured_integrations"
        ] = integrations
    if (
        snapshot.get("user_instruction", {}).get("dry_run") is True
        and result.get("requested_effects")
    ):
        result["proposed_decision"] = result["decision"]
        result["decision"] = "dry-run"
        result["proposed_effects"] = result["requested_effects"]
        result["requested_effects"] = []
    return result


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
