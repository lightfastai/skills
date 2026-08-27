# Advance a route

Use this mode to move a Query through one live routing transition.

## Reconcile first

1. Resolve the Query's native identity and bounded intent.
2. Search the intended destination's tasks, conversations, repositories, projects, and native artifacts before creating or sending anything.
3. Treat work as compatible only when its objective, target scope, authority, route identity, and material native artifacts agree. For an Orchestrator route, also require the intended adapter and exact destination Orchestrator revision; for `improve`, require the exact target Orchestrator revision and campaign identity.
4. Resume compatible work before creating a destination. When ownership, overlap, or terminal state is unresolved, return one blocker instead of creating a competing writer.

## Advance once

Choose exactly one transition:

- resume one compatible destination task or conversation;
- create one destination task when none is compatible and task creation is authorized;
- send one bounded handoff or follow-up to the destination;
- return one ordinary question, meaningful progress event, blocker, or result to the Query; or
- redirect work that designs or changes Orchestrator lifecycle rules to a task in the authoritative `lightfastai/orchestrator` repository.

A new or resumed handoff carries the Query reference, requested outcome, resolved target scope, constraints and exclusions, explicitly requested consequential effects, current native evidence, unresolved gates, and the stable destination identity. Let the destination apply its own admission and instructions.

## Return events

- **Question:** return one ordinary decision that the Query can answer without moving credentials, MFA, permissions, or a consequential approval out of the destination.
- **Progress:** return a meaningful milestone with a destination link and native evidence, not routine activity.
- **Blocker:** return the affected branch, current evidence, and reopening condition without exposing sensitive metadata.
- **Result:** return the destination's terminal claim and native evidence links, then reconcile them against the Query's original intent before describing the route as complete.

Keep credentials, MFA, permission changes, consequential approvals, and their sensitive evidence in the destination task. After the one transition is identifiable by native task lineage, task ID, repository reference, or system-native identity, stop.
