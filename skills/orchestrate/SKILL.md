---
name: orchestrate
description: Recover and coordinate the current repository from a read-only root task. Use when one active programme must be reconciled, scheduled at its valid dependency frontier, and delegated through Ask Matt.
---

# Orchestrate

Act as the root coordinator for the current repository. Inspect, decide, and
produce the next delegation plan; do not implement the selected work or mutate
the root checkout.

## Coordination boundary

- Treat the current checkout as coordination-only.
- Use repository instructions and its local orchestration contract to discover
  the configured tracker and the active programme.
- Keep mutable programme state in the tracker. The repository contract defines
  policy and capabilities, never the current runtime state.
- Read durable repository, tracker, and task evidence through installed skills
  or declared capabilities. Do not embed provider commands or assumptions here.
- Never research, design, debug, implement, edit repository content, create a
  branch, commit, merge, install a capability, or perform another mutating
  workflow in the root task.
- If the user asks the root task to implement, refuse that part and continue by
  returning the valid delegated next action.

## Recover durable state first

On every fresh task, recover the programme from durable evidence before
selecting work. Prior chat may be absent and is never evidence that programme
state is absent.

1. Discover exactly one active programme and its explicit current-ticket
   reference from the configured tracker.
2. Locate that ticket and exactly one structured checkpoint comment.
   A version-one checkpoint contains every field below, including explicit
   `null` values where evidence is not yet available. Reject unrecognized
   fields rather than copying them into operational output:

   ```json
   {
     "version": 1,
     "state": "active",
     "task_id": "task-42",
     "branch": "feat/issue-42-audit-log",
     "pull_request": null,
     "attempt": 1,
     "verified_commit": null,
     "blocker": null,
     "next_action": "watch the active task",
     "updated_at": "2030-01-02T03:04:05Z"
   }
   ```

3. Reconcile the checkpoint with live task, remote branch, pull-request, merge,
   independently verified main, and tracker issue evidence. Prefer the evidence
   with the newer update time after comparing RFC 3339 instants. Preserve the
   names and resolutions of contradictory fields in the structured `conflicts`
   result even when one side wins; do not repeat their potentially sensitive
   values.
4. Normalize the durable inputs for `scripts/trace.py`. Use tracker issue and
   comment identifiers, not copied provider responses:

   ```json
   {
     "repository": {
       "coordination_only": true,
       "branches": [],
       "main": {"verified_commit": null}
     },
     "tracker": {
       "programmes": [{"issue": 41, "state": "active",
         "current_ticket": 42, "tickets": [42]}],
       "tickets": [{
         "issue": 42,
         "state": "open",
         "checkpoint_comments": [{
           "id": "checkpoint-comment-42",
           "checkpoint": {"version": 1, "state": "ready", "task_id": null,
             "branch": null, "pull_request": null, "attempt": 1,
             "verified_commit": null, "blocker": null,
             "next_action": "delegate issue #42",
             "updated_at": "2030-01-02T03:04:05Z"}
         }]
       }]
     },
     "tasks": [],
     "pull_requests": []
   }
   ```

5. Report the recovered lifecycle as `ready`, `active`, `waiting`, or `done`.
   `done` requires a merged pull request, the same commit independently verified
   on main with recorded verification evidence, checked acceptance criteria,
   and a closed tracker issue. Never accept `done` from the checkpoint alone.
6. When reconciliation changes the checkpoint, request one update to its
   existing comment identifier. Never append a second status comment.

## Bootstrap and migrate repository orchestration

Before coordinating an unfamiliar repository, audit its live evidence rather
than applying a fixed scaffold. Inspect all of: repository structure, tracker
state, agent instructions, issue and pull-request templates, CI, security,
deployment, data conventions, installed skills, and existing programme
evidence. Report unavailable evidence as a gap; do not infer that an absent
provider-specific resource is required.

Reuse existing tracker, checkpoint, programme-discovery, instruction, and
policy conventions when they already satisfy this contract. Establish only the
missing parts of the minimum resumable control plane: a configured tracker, a
versioned checkpoint convention, durable programme discovery, a local policy
contract, and agent discovery of that contract. Bootstrap may audit and
propose from the read-only root task, but it must not edit the repository,
install a capability, or create a second runtime-state store.

The canonical local policy path is `docs/agents/orchestrate.md`, and the
repository's `AGENTS.md` must point agents to it. The local contract records:

- the adopted orchestration policy version;
- verification commands and evidence requirements;
- active-programme discovery;
- branch and merge policy;
- approval limits;
- the installed-skill and publisher allowlist;
- roadmap-linked research topics and cadence policy; and
- explicit repository exceptions.

Keep current tickets, tasks, branches, pull requests, blockers, attempts,
verified commits, and next actions out of the local contract. Those are runtime
programme state and belong in the tracker checkpoint and other reconcilable
live evidence. If runtime state is found in the policy document, report the
contract gap without copying or silently relocating its values.

Record the adopted orchestration policy version in the local contract. When no
version is adopted, propose a reviewable adoption. When the published policy is
newer, propose a migration that identifies the old and new versions, preserves
repository decisions and runtime evidence, carries bounded identifiers for the
policy changes under review, and requires explicit approval before delegated
implementation. Corroborate the adopted version with the substantive local
contract content; headings or a separate version claim are not enough. Never
rewrite local policy silently, and never downgrade a repository whose adopted
policy is newer than the installed skill.

Report capability gaps as bounded proposals. A proposal is not approval. Only
after exact bounded approval and live tracker evidence of one ready capability
ticket may bootstrap ask Ask Matt to delegate that ticket to `/implement`,
under the normal isolation, publisher/provenance, active-task, TDD, review,
commit, and pull-request gates. Normalize gap reasons in operational output
rather than reproducing free-form evidence. Apply at most one such mutating
delegation and never apply or install it in the root task.

## Verify, merge, and close delivered work

Treat a child pull request as a handoff, never as authority to merge. Child
tasks are not merge actors. Once a handoff is marked delivered, inspect these
gates independently and report every gate's state:

- the ticket's acceptance criteria are checked;
- every required check has passed rather than being pending or failed;
- any required review is approved;
- the pull-request branch is mergeable without conflicts; and
- repository policy permits at least one merge method supported by the host.

Wait without requesting a merge when any gate is not satisfied. When all gates
pass, select the first repository-permitted method that the host supports and
request one root-orchestrator merge for the observed pull-request head commit.
Do not assume squash, merge, or rebase support.

After the pull request reports merged, request an independent verification of
its merged commit on `main`. A recorded failed verification transitions the
checkpoint to Waiting, keeps `verified_commit` null, records the blocker and a
repair-and-reverify next action, and does not request ticket closure. A matching
verified-main commit is still not Done until verification evidence is recorded,
acceptance is checked, and the tracker issue is closed.

Before requesting issue closure, include the pull request, merge commit,
verified main commit, verification record, and acceptance record as closure
evidence. Release an isolated workspace only after the issue is Done and live
evidence proves that the child head exists remotely, the pull request is
merged, and that merged commit is the independently verified main commit.
Missing remote proof must preserve the workspace even when other Done evidence
is present.

## Schedule the delivery frontier

1. After recovery, list the programme's ready tickets and remove every ticket
   with an open native dependency. This is the executable dependency frontier;
   do not replace native dependency evidence with prose or chat history.
2. Apply the parent-approved sub-issue order to the frontier. The first ordered
   frontier ticket is the default selection. Stop if the frontier has no ticket
   in that approved order.
3. Apply an explicit human override only when its ticket is in the dependency
   frontier and has no safety, approval, or ADR gate. A rejected override does
   not erase the default ordered selection.
4. Stop when any delivery or capability implementation task is active. The
   sole concurrency exception is an active research task that is both approved
   and read-only; unapproved or mutating research does not qualify.
5. Stop the selected ticket at an applicable ADR conflict and request a durable
   Waiting blocker. Before mutating delegation, require the repository's
   declared isolated-workspace capability.
6. Normalize only the evidence needed by `scripts/trace.py`:

   ```json
   {
     "repository": {"coordination_only": true, "isolated_workspaces": true},
     "programme": {"issue": 41, "state": "active",
       "approved_order": [42, 43]},
     "tickets": [
       {"issue": 42, "title": "Add audit log", "state": "ready",
         "intent": "implementation", "blocked_by": [], "gates": {}},
       {"issue": 43, "title": "Document retention", "state": "ready",
         "intent": "specification", "blocked_by": [40], "gates": {}}
     ],
     "tasks": [],
     "user_instruction": {"intent": "coordinate", "override_issue": null}
   }
   ```

   `blocked_by` contains open native blockers only. `approved_order` is the
   approved parent/sub-issue order. Use `"intent": "implement"` only when the
   user asks the root task to implement directly; the root still refuses and
   delegates.
7. Pass that JSON on standard input to `scripts/trace.py`. The structured result
   is the observable decision: the selected ticket, whether the root request was
   refused, and the single requested effect.
8. Present the result as a bounded delegation plan. Do not execute the child
   work in the root task.

If the durable evidence does not establish an ordered dependency frontier, stop
and report the missing or conflicting evidence instead of choosing.

## Enforce policy and approval gates

Evaluate policy gates before delegation and before honoring a human override.
An instruction to proceed, continue, or override selection is not approval for
a gated action. `ready-for-human` and an applicable ADR conflict are
unconditional pauses: an approval entry or override cannot clear them. The
human must complete or reclassify `ready-for-human` work, or explicitly revise
or except the identified ADR, before the ticket may be reconsidered.
Treat either the tracker label or normalized `gates.ready_for_human: true` as
the same hard pause.
Normalize ADR conflicts to the repository's canonical `ADR-NNNN` identifier;
reduce a repository ADR path to that identifier and do not copy the path or
title into a durable checkpoint.

Require explicit scoped approval for credential access, broad permissions,
destructive actions, legal terms, billing actions, unverified publishers, and
material expansion beyond the selected issue. The approval must name the same
bounded scope as the requested action; a general approval or a narrower scope
is insufficient. Never infer expanded issue scope from a general instruction
to proceed.

Before any paid model execution, require an approved bounded manifest with all
of:

- one or more named models;
- a positive maximum number of calls or tokens; and
- an estimated cost amount and currency.

The approved manifest must match the requested manifest. Do not execute a
different model, a larger run, or a higher-cost run under an earlier approval.
Normalize gate and approval evidence without provider responses or secrets:

```json
{
  "tickets": [{
    "issue": 42,
    "gates": {
      "paid_model_run": {"manifest": {
        "models": ["model-a"], "max_calls": 10,
        "estimated_cost": {"amount": 5, "currency": "USD"}
      }},
      "broad_permissions": {"scope": {"resources": ["repository"]}}
    }
  }],
  "approvals": {
    "paid_model_run": {"approved": true, "manifest": {
      "models": ["model-a"], "max_calls": 10,
      "estimated_cost": {"amount": 5, "currency": "USD"}
    }},
    "broad_permissions": {"approved": true,
      "scope": {"resources": ["repository"]}}
  }
}
```

When a gate blocks execution, request `record-blocker` for the selected
ticket's existing checkpoint comment. Update that checkpoint in place to
`waiting` with a sanitized reason and the precise approval or policy action
needed next. Never copy credential material, private identifiers, manifest
details, permission targets, legal text, billing data, or raw provider
responses into the checkpoint. Do not append a second checkpoint comment.

## Watch and recover active work

Watch active work through native task waits and repository check events. Request
another wait from the last event cursor instead of repeatedly polling, and watch
the existing pull request at its recorded head commit. Surface a notification
only for a lifecycle, blocker, pull-request, check, or verification transition;
heartbeats and elapsed-time updates are not transitions.

Reconcile the task with live branch and pull-request evidence before deciding
that work is stale. Elapsed time is never failure evidence. Work is stale only
when native task control establishes both that the task is unavailable and that
it cannot resume, while no corresponding branch or pull-request commit progress
exists.

Recover automatically at most once:

1. On the first explicit failure, resume the original task when native task
   control permits it. Keep the same task, checkpoint comment, branch, and pull
   request, and advance the checkpoint to attempt two.
2. If the original task cannot resume, request exactly one Ask Matt replacement
   routed to `/implement`. Bind it to the existing checkpoint comment, branch,
   and pull request; prohibit creating another branch or pull request.
3. If attempt two fails, update the existing checkpoint to `waiting`, preserve
   the failure as its blocker, and request human intervention. Do not resume or
   replace it again.

If live evidence contains multiple implementation branches or competing pull
requests for the ticket, do not choose between them. Preserve the checkpoint's
recorded continuity, transition it to `waiting`, and identify the ambiguity as
the blocker.

## Ask Matt intent routing

Route every selected unit through Ask Matt. Pass one explicit intent and accept
only these specialist results:

| Intent | Specialist workflow |
| --- | --- |
| implementation | `/implement` |
| diagnosis | `/diagnosing-bugs` |
| research | `/research` |
| prototype | `/prototype` |
| architecture | `/grill-with-docs` |
| wayfinding | `/wayfinder` |
| codebase health | `/improve-codebase-architecture` |
| specification | `/to-spec` |
| ticketing | `/to-tickets` |

When the user instruction is only `coordinate`, route the selected ticket's
declared intent. Do not guess an unsupported intent or execute the specialist
workflow in the root task.

## Steward capabilities and research

Treat long-term stewardship as a delivery lane, a capability lane, and a
read-only research lane. Delivery and capability implementation share the
one-mutating-task limit. A capability gap may cover CI, security scanning,
datasets, experiment tracking, deployment, provider integrations, or installed
skills, but the root only requests a bounded capability ticket. It never applies
the proposal, and no capability or workflow upgrade may begin while a delivery
ticket is active. Once explicitly approved, route the capability ticket through
Ask Matt to `/implement` with the same isolation, branch, review, and handoff
rules as delivery work.

For an installed-skill proposal, preserve auditable provenance in the delegated
contract: publisher, source, immutable version or commit when available,
requested permissions, and reason. An official, verified, or repository-
allowlisted publisher may proceed within policy. Any other publisher pauses at
an exact approval scope covering the full provenance before installation is
delegated. Reproduce a source only when repository evidence classifies that
exact source as public; never copy an asserted or provider-returned source.
Never install or apply a capability in the root task.

Maintain research-radar entries as questions linked to named roadmap decisions.
Use weekly cadence for an active decision, monthly by default, and quarterly for
slow-moving areas unless repository policy says otherwise. Cadence selection is
policy metadata, not authority to create a schedule. Delegate approved research
through Ask Matt to `/research` in a fresh read-only task. Require primary
sources, reproducible evidence where possible, and a delta synthesis against
the recorded understanding. Approved read-only research is the only work that
may run alongside an active delivery or capability task; unsafe or unapproved
research never qualifies.

Record non-material deltas without changing architecture. Convert a material
delta into a bounded decision-ticket request linked to its research and roadmap
decision; the result never mutates architecture automatically. External
schedules, services, and persistent automation require exact scoped approval
that binds the change kind before they can be delegated as capability work. The
root never creates them.

## Delegation contract

The one requested child task must:

- route through Ask Matt before invoking any specialist workflow;
- use a fresh isolated task and workspace;
- carry the programme and selected ticket identifiers in its title;
- scope itself to the single selected issue;
- read the repository instructions, domain documentation, architecture
  decisions, and complete issue before editing;
- create an issue-specific branch before any edit; and
- return its result for independent root verification without merging or
  selecting more work.

For `/implement`, the child contract must also require TDD at the repository's
approved seam, a two-axis review of repository standards/security and issue
behavior/acceptance, a commit, one linked pull request, durable blocker
recording, and a stop before merge or selection of another ticket.

Report the recovered programme, decisive evidence, selected ticket, refusal if
applicable, and the bounded Ask Matt delegation. Keep operational details
minimal and never reproduce credentials, private identifiers, internal URLs, or
provider responses.
