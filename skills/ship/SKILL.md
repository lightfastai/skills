---
name: ship
description: Route a bounded code-delivery outcome to the standalone Lightfast Ship Orchestrator and resume compatible shipping work. Use when code must reach a target repository's own completion boundary; not for route advice or Orchestrator evaluation.
---

# Ship

This is the canonical public adapter for the standalone `ship` Orchestrator. The adapter discovers or resumes one destination task and hands off a bounded request; the live `lightfastai/ship` repository remains authoritative for admission, planning, execution, recovery, and completion.

The **Query** is the originating task or conversation that holds the user's intent. The adapter routes; it does not implement the outcome or copy the Orchestrator's operating contract.

## Admission

Use this route when the Query supplies or can resolve:

- one bounded code-delivery outcome;
- named target repositories or a bounded selection rule;
- material constraints and exclusions; and
- every requested consequential effect, such as deployment, production change, release, publication, migration, destructive action, paid execution, or permission expansion.

The target repository defines completion. A request for advice only, an unbounded product objective, or an Orchestrator evaluation campaign does not enter `ship`. Return one indispensable ordinary question through the Query when outcome or target scope cannot be bounded.

## Destination discovery

Discover the live `lightfastai/ship` repository through available repository and project connections. Resolve the selected repository ref to an exact revision, then read its current instructions before handoff. Do not consult `lightfastai/orchestrator`, its Workbench, or its Map at runtime.

Search live tasks and conversations in the `ship` repository for the same Query lineage, outcome, target scope, authority, and native artifacts. Resume compatible work before creating a task. If none is compatible and task creation is authorized, create one destination task from the resolved exact `ship` revision.

## Bounded handoff

Send only the material needed for `ship` to decide admission:

- the Query's native reference;
- the code-delivery outcome and observable target-defined completion;
- the resolved target scope;
- constraints, exclusions, and explicitly requested consequential effects;
- known target-native tasks, issues, branches, commits, pull requests, checks, deployments, or other evidence; and
- unresolved gates or ownership conflicts.

Ask the destination to reconcile its live repository instructions and native evidence. Do not prescribe its workflow plan or decompose its implementation.

## Approval ownership

Ordinary product questions, meaningful progress, non-sensitive blockers, and results may return through the Query. Credentials, MFA, permissions, scope expansion, and consequential approvals remain in the destination task. The adapter and Query cannot relay an approval that belongs beside destination-native evidence.

## Return events

After a destination exists, return at most one event per routing transition:

- **Question:** one ordinary decision, with the destination task link.
- **Progress:** one meaningful milestone backed by target-native evidence.
- **Blocker:** the affected delivery branch and its reopening condition.
- **Result:** the destination's terminal claim and linked completion evidence.

## Completion evidence

Reconcile a returned result against the Query's original outcome and the exact integrated target state. Link repository-native evidence such as commits, pull requests, required checks and reviews, the default-branch result, tracker state, and deployment or production verification only when those effects were in scope. Destination task completion alone is insufficient.

## Recovery identity

Recover the route from the Query identity, route name `ship`, exact `ship` revision, target scope, destination task identity, and target-native artifact identities. Keep that identity in native task lineage and evidence; do not create a parallel registry or checkpoint.

After interruption or an ambiguous response, search those native identities before retrying. Resume the compatible task and artifacts. Create a replacement only when native evidence shows continuation is unavailable or unsafe, binding the replacement to the same outcome, scope, artifacts, and unresolved gates.
