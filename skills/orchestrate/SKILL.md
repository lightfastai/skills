---
name: orchestrate
description: Coordinate or recover the current repository from a read-only root task. Use when a prepared repository has one active programme whose durable tracker and repository evidence must be reconciled before the next action.
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

## Trace one ready ticket

1. After recovery, establish that there is one ticket whose durable
   state is `ready` with no open blockers. Do not infer readiness from chat
   history.
2. Normalize only the evidence needed by `scripts/trace.py`:

   ```json
   {
     "repository": {"coordination_only": true},
     "programme": {"issue": 41, "state": "active"},
     "tickets": [
       {"issue": 42, "title": "Add audit log", "state": "ready", "blocked_by": []}
     ],
     "tasks": [],
     "user_instruction": {"intent": "coordinate"}
   }
   ```

   Use `"intent": "implement"` when the user asks the root task to perform the
   implementation itself.
3. Pass that JSON on standard input to `scripts/trace.py`. The structured result
   is the observable decision: the selected ticket, whether the root request was
   refused, and the single requested effect.
4. Present the result as a bounded delegation plan. Do not execute the child
   work in the root task.

If the durable evidence does not establish exactly one ready, unblocked ticket,
stop and report the missing or conflicting evidence instead of choosing.

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

Report the recovered programme, decisive evidence, selected ticket, refusal if
applicable, and the bounded Ask Matt delegation. Keep operational details
minimal and never reproduce credentials, private identifiers, internal URLs, or
provider responses.
