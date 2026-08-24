---
name: orchestrate
description: Coordinate the current repository from a read-only root task. Use when a prepared repository has one active programme and ready tracker work that must be selected and handed to a fresh child task through Ask Matt.
---

# Orchestrate

Act as the root coordinator for the current repository. Inspect, decide, and
produce the next delegation plan; do not implement the selected work or mutate
the root checkout.

## Coordination boundary

- Treat the current checkout as coordination-only.
- Use repository instructions and its local orchestration contract to discover
  the configured tracker and the active programme.
- Read durable repository, tracker, and task evidence through installed skills
  or declared capabilities. Do not embed provider commands or assumptions here.
- Never research, design, debug, implement, edit repository content, create a
  branch, commit, merge, install a capability, or perform another mutating
  workflow in the root task.
- If the user asks the root task to implement, refuse that part and continue by
  returning the valid delegated next action.

## Trace one ready ticket

1. Read the repository instructions and local orchestration contract before
   inspecting the configured tracker.
2. Establish that there is one active programme and one ticket whose durable
   state is `ready` with no open blockers. Do not infer readiness from chat
   history.
3. Normalize only the evidence needed by `scripts/trace.py`:

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
4. Pass that JSON on standard input to `scripts/trace.py`. The structured result
   is the observable decision: the selected ticket, whether the root request was
   refused, and the single requested effect.
5. Present the result as a bounded delegation plan. Do not execute the child
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
