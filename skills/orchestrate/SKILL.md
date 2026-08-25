---
name: orchestrate
description: Recover and coordinate a registered orchestrator programme. Use when selecting, watching, resuming, or closing work under a repository or control-plane charter.
---

# Orchestrate

Coordinate from a read-only root. The root owns only the effects granted by one registered charter and delegates specialist work to isolated tasks.

## Resolve the charter

Read the authority home's instructions and orchestration registry. Select the explicitly named charter, or the sole charter that matches the requested purpose. Report ambiguity instead of choosing among multiple matches.

Load the shared policy and that charter only. The registry owns registration and resource claims; the charter owns purpose, programme discovery, routes, controls, and completion. Tracker evidence owns live state.

Draft charters may inspect and propose but cannot coordinate mutations. When the registry, charter, or bilateral meta opt-in is missing or incompatible, read [charters and registration](references/charters.md) and return one bounded adoption proposal.

Completion: one registered charter and one programme are identified, or the exact gap is reported.

## Recover the instance

1. Identify the instance as `charter_id + programme_id` from the charter's declared tracker source.
2. Reconcile its checkpoint with native task, repository, and tracker evidence relevant to that charter.
3. Report `ready`, `active`, `waiting`, or `done` using the charter's completion criteria.
4. Update an existing checkpoint only when a governed field materially changes.

Completion: durable evidence supports the lifecycle and next valid transition.

## Select one transition

1. Build the charter's native dependency frontier.
2. Apply registered resource claims and concurrency ceilings. Capacity is a ceiling, not a target; readers consume no mutation capacity.
3. Pause at human, approval, safety, decision, or authority gates. Read [approval and capability gates](references/gates.md) when one applies.
4. Select the first approved frontier unit and route its declared intent through Ask Matt.
5. Request one effect, then recover before requesting another.

An approved meta experiment may adjust only controls inside the target's tuning envelope. Bind its assignment when a work unit starts and keep it fixed until that unit closes.

Completion: one requested effect names the charter, programme, work unit, intent, authority, resource claim, gates, and stop condition.

## Watch and recover

Wait on native task and evidence events from the last cursor. Surface lifecycle, blocker, authority, verification, or charter-declared completion transitions. Elapsed time and heartbeats are not transitions.

When continuity fails or conflicts, read [recovery](references/recovery.md). Completion: existing work is resumed, replaced within policy, waiting on one exact gate, or durably complete.

## Close under the charter

Apply the charter's completion criteria and request only its permitted closure effects. When the charter coordinates software delivery, read [delivery closure](references/delivery.md).

Completion: every criterion is evidenced, or one exact blocker and next action are recorded.

## Output

Report the charter, programme, lifecycle, decisive evidence, and one bounded effect. For `waiting`, report the exact gate and required action. For `done`, report final evidence and request no new effect. Delegations carry only the work unit, intent, authority, acceptance boundary, gates, and stop conditions. Continuations carry only the delta.
