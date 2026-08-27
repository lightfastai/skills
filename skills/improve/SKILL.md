---
name: improve
description: Route a bounded evidence campaign about an exact Orchestrator revision to the standalone Lightfast Improve Orchestrator and resume compatible campaign work. Use for Orchestrator evaluation or authorized improvement, not general codebase improvement.
---

# Improve

This is the canonical public adapter for the standalone `improve` Orchestrator. The adapter discovers or resumes one destination task and hands off a bounded request; the live `lightfastai/improve` repository remains authoritative for admission, trials, findings, recovery, and authorized dispositions.

The **Query** is the originating task or conversation that holds the user's intent. The adapter routes; it does not run trials, interpret findings, mutate an Orchestrator, or copy the Orchestrator's operating contract.

## Admission

Use this route when the Query supplies or can resolve:

- one bounded improvement question or campaign outcome;
- one target Orchestrator repository and an exact compatible revision;
- named trials or a finite bounded selector;
- visible target scope containing every trial project and finding destination;
- an operating window and material resource or cost ceilings;
- the required evidence burden; and
- a disposition ceiling of evaluate only, retain, propose, implement, merge, or publish, with consequential effects explicitly included.

General codebase improvement, route advice, an unspecified target revision, or a standing self-improvement mandate does not enter `improve`. Return one indispensable ordinary question through the Query when the target, revision, campaign question, trial boundary, destination, or disposition cannot be resolved without a materially different choice.

## Destination discovery

Discover the live `lightfastai/improve` repository through available repository and project connections. Resolve the selected repository ref to an exact revision, then read its current instructions before handoff. Do not consult `lightfastai/orchestrator`, its Workbench, or its Map at runtime.

Search live tasks and conversations in the `improve` repository for the same Query lineage, campaign question, exact target Orchestrator revision, trial scope, finding destinations, disposition ceiling, and native evidence. Resume compatible work before creating a task. If none is compatible and task creation is authorized, create one destination task from the resolved exact `improve` revision.

## Bounded handoff

Send only the material needed for `improve` to decide admission:

- the Query's native reference;
- the improvement question and requested campaign outcome;
- the target Orchestrator repository and exact compatible revision;
- admitted trials or bounded selector, trial target scope, and finding destinations;
- operating window, evidence burden, material cost or resource ceilings, and disposition ceiling;
- known native Sessions, tasks, Revisions, trials, findings, branches, pull requests, checks, or other evidence; and
- unresolved compatibility, authority, ownership, or consequential gates.

Ask the destination to reconcile its live repository instructions and native evidence. Do not choose its trials, findings, cause classification, or workflow plan.

## Approval ownership

Ordinary campaign questions, meaningful progress, non-sensitive blockers, and results may return through the Query. Credentials, MFA, permissions, paid execution, target-scope expansion, mutation, merge, release, publication, and other consequential approvals remain in the destination task. Evidence strength never lets the adapter widen the authorized disposition.

## Return events

Return at most one event per routing transition:

- **Question:** one ordinary decision, with the destination task link.
- **Progress:** one meaningful trial or finding milestone backed by native evidence.
- **Blocker:** the affected trial or disposition and its reopening condition.
- **Result:** the destination's terminal claim, authorized disposition, and linked native evidence.

## Completion evidence

Reconcile a returned result against the Query's original campaign intent. Link the exact target Orchestrator revision, trial task or evidence identities, observed and expected outcomes, cause classification, counterevidence and limits, authorized disposition, and the native finding, proposal, commit, pull request, merge, or publication evidence that actually exists. An adverse, inconclusive, or no-change result can be complete; destination task completion alone is insufficient.

## Recovery identity

Recover the route from the Query identity, route name `improve`, exact `improve` revision, exact target Orchestrator revision, admitted trial references and target scope, finding destinations, destination task identity, and native evidence identities. Keep that identity in native task lineage and evidence; do not create a campaign ledger or parallel registry.

After interruption or an ambiguous response, search those native identities before retrying. Resume the compatible task and evidence. Create a replacement only when native evidence shows continuation is unavailable or unsafe, binding the replacement to the same campaign, exact revisions, scope, evidence, and unresolved gates.
