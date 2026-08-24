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
