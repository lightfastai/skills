# Advance a route

Use this mode to move a Query through one live routing transition.

## Reconcile first

Apply the shared Query-recovery and continuation-first rules. Treat work as compatible only when its objective, target scope, authority, route identity, and material native artifacts agree. For an Orchestrator route, also require the intended adapter and exact destination Orchestrator revision; for `improve`, require the exact target Orchestrator revision and campaign identity.

When ownership, overlap, or terminal state is unresolved, return one blocker instead of creating a competing writer.

## Advance once

Choose the permitted transition:

- resume one compatible destination task or conversation;
- create one destination task when none is compatible and task creation is authorized;
- send one bounded handoff or follow-up to the destination;
- return one ordinary question, meaningful progress event, blocker, or result to the Query; or
- redirect lifecycle-authority work according to the shared routing contract.

A new or resumed handoff carries the Query reference, requested outcome, resolved target scope, constraints and exclusions, explicitly requested consequential effects, current native evidence, unresolved gates, and the stable destination identity. Let the destination apply its own admission and instructions.

## Return events

- **Question:** return one ordinary decision permitted by the shared Query and destination boundary.
- **Progress:** return a meaningful milestone with a destination link and native evidence, not routine activity.
- **Blocker:** return the affected branch, current evidence, and reopening condition without exposing sensitive metadata.
- **Result:** apply the shared result-reconciliation rule to the destination's terminal claim and native evidence links.

After the transition is identifiable by native task lineage, task ID, repository reference, or system-native identity, stop.
