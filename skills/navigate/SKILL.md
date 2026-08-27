---
name: navigate
description: Find, resume, or advance a live Lightfast route when the operational destination or authority is uncertain. Use for cross-system wayfinding and one-step handoffs; execution remains with the destination.
---

# Navigate

A Query has a bounded outcome, but the live path across Lightfast skills, tasks, conversations, repositories, projects, or systems is unclear, interrupted, or split across contexts. Navigate finds the **destination** and advances the route one transition at a time. The destination is the native authority task or system that can admit and own the requested outcome; naming it is the first act of routing.

## Route, do not own

Navigate is routing by default. Its plan-and-don't-do invariant is **route; do not own**: recover the Query, discover current authority, expose the frontier, and move one bounded transition. Destination work, workflow planning, durable execution state, approvals, and completion stay with the destination.

The pull to implement, run a campaign, or manage the destination is the signal that the route has reached its boundary. Stop after the handoff, resumption, returned event, or other single transition is identifiable in native state.

## Refer by name

Every route, task, conversation, repository, and system has a human-readable name. Use that name in narration and the Route Index. Render the name as the link when a URL is available, and keep the native task ID or other stable identity in the same reference; a bare ID, slug, or URL never stands in for the name.

Names make the route legible. Native identities make it recoverable. A route's identity comes from its source Query, adapter or capability, destination task or system ID, exact revisions where relevant, target scope, and native artifacts—not from the display name or a copied record.

## The Route Index

Most routing is direct and needs no artifact. When cross-context continuity genuinely needs a durable rediscovery spine, use one native Codex task named **Route Index: &lt;destination&gt;** as the canonical low-resolution routing artifact. Merely spanning multiple tasks, conversations, repositories, systems, or context windows does not require one when the originating Query can still recover the route. Search for a compatible Route Index task before creating one. Task creation must be authorized.

The Route Index is an **index, not a store**. Its native conversation is append-only: the opening message names the destination and boundaries, then later messages append route entries and state observations. Earlier messages remain unchanged. The destination task, repository, project, or system remains authoritative for live detail; the index holds a gist and a pointer, never a copy of destination state or authority.

Do not require a Route Index for a trivial direct recommendation, a single handoff, or a result that can return in the current Query. Continuity, not importance, earns the index.

### Opening message

```markdown
## Destination

<the bounded outcome and what a successfully reconciled return to the Query looks like>

## Notes

<source Query name and ID; standing constraints; relevant installed capabilities>

## Not yet specified

<in-scope routing fog that is not sharp enough to name as a route entry>

## Out of scope

<destinations, effects, and scope explicitly ruled beyond this route>
```

### Route entries

Append one low-resolution entry when a native destination or transition becomes relevant, and append another observation when its state materially changes. The latest observation for the same native identity is the current index view.

```markdown
Route: [<human-readable route or task name>](<native link>) (task <native ID>)
Outcome: <one-line gist of the bounded outcome>
State: <current native state or concise takeable/resumable/blocked/completed gist>
Authority home: <native repository, project, task, or system>
Exact revision: <adapter or Orchestrator revision when compatibility depends on it>
Evidence: <native artifact links needed to recover the route>
```

Use only fields that help rediscover or choose a transition. Detailed plans, credentials, approval evidence, copied conversations, and destination-owned completion records stay in their native homes.

### Local rediscovery aid

With explicit user consent naming this effort and `~/.codex/query/routes.md`, Navigate may maintain that file as a local rediscovery aid. Consent permits the aid but does not make it necessary; use it only when the user also wants local rediscovery. Each line contains only a human-readable name, native task ID, short outcome gist, and state:

```markdown
- <name> | <task ID> | <short outcome gist> | <state>
```

The local file is optional, consent-bounded, and subordinate to the native Route Index task. Use it only to rediscover the native task, then verify live state there. It grants no authority, carries no credentials or links, and is never a second ledger. If local persistence is unavailable or consent is absent, continue without it. v1 creates no Query repository.

## The frontier

A **route entry** is compatible only when the objective, target scope, authority, adapter or capability identity, exact revisions, and material native artifacts agree with the Query. Similar wording is insufficient when these identities differ.

The **frontier** is the compatible transitions takeable or resumable now. Derive it from live native surfaces each invocation; the Route Index only points toward those surfaces. A transition leaves the frontier when a native blocker, conflicting writer, unresolved ownership, missing approval, or unavailable authority prevents it.

Continuation-first ordering is strict:

1. resume compatible native work whose reopening condition is satisfied;
2. take an already-created compatible transition with no live blocker or ownership conflict;
3. create one destination only when live discovery proves no compatible destination exists and task creation is authorized.

If the user names a compatible frontier transition, take it. Otherwise choose the first live frontier entry in Route Index order, or live discovery order when no index exists. Recheck native state immediately before acting because concurrent sessions may change the frontier.

## Routing fog

The route is deliberately incomplete. **Routing fog** is in-scope uncertainty you can see but cannot yet express as one destination or transition. In a Route Index it belongs under **Not yet specified**; without an index, state it in the Query response.

**Fog or route entry?** The test is whether the destination and next transition can be named precisely now, not whether the outcome can be completed now.

- Create or append a route entry when its native destination and next transition are sharp, even if blocked.
- Keep it not yet specified when discovery or one indispensable ordinary Query decision is still needed to name the route.

Never turn fog into speculative tasks. Read-only discovery may clear it; otherwise return one bounded routing question and stop.

## Out of scope

The destination and snapshotted target scope bound the route. Work beyond them is out of scope, not fog, and never enters the frontier. Record only a low-resolution boundary in the Route Index when one exists.

Scope expansion remains a destination-owned approval beside the native evidence that motivates it. The Query, Route Index, and local rediscovery aid cannot approve or imply it. After the destination records approval, a later Navigate invocation may discover the newly authorized route.

## Native authority and precedence

Discover installed skills, live tasks and conversations, connected projects, repositories, systems, and public Orchestrator adapters from current native surfaces. Read only the candidate instructions needed to decide the route. The public `ship` and `improve` adapters in `lightfastai/skills` own their handoff contracts; their standalone Orchestrator repositories own admission and execution.

Apply this precedence when Orchestrator work could look similar:

- Work that designs or changes the rules for Orchestrator creation, evaluation, conformance, or upgrades routes to a native task in the live `lightfastai/orchestrator` lifecycle authority.
- A bounded evaluation or authorized improvement campaign for one exact Orchestrator revision routes through the live `improve` adapter.
- Evidence from Improve may support a later lifecycle proposal, but it grants no lifecycle-rule authority. Route that proposal separately to the lifecycle authority.

The Workbench is a lifecycle destination, never a runtime lookup service. Ordinary routing and Orchestrator execution never consult the Workbench or Orchestrator Map for discovery, substitution, permission, or state.

## Invocation

Two modes. Either way, advance no more than one bounded routing transition per invocation.

### Find a route

Use when the Query needs the best live route and no destination transition is ready.

1. **Name the destination.** Recover the Query's bounded outcome, target scope, exclusions, consequential effects, and authority. If materially different destinations remain, return one indispensable ordinary question.
2. **Chart the live route space breadth-first.** Discover plausible installed skills, adapters, tasks, conversations, projects, repositories, and systems. Read enough current native instruction and state to distinguish them; preserve user changes and unresolved ownership. When the Query asks to locate tasks, chats, conversations, or user-authored turns, read [the conversation and task locator](references/conversation-task-locator.md) and complete its surface-specific discovery before ranking candidates.
3. **Separate frontier, fog, and out of scope.** Apply compatibility and precedence before ranking candidates. A missing optional capability is a route-specific blocker, not permission to emulate or silently substitute it.
4. **Choose the continuity level.** For a clear direct route, return its human-readable destination and next invocation with no Route Index. When multi-context continuity needs an index, resume or create one native Route Index task and append the current low-resolution route entries, fog, and boundaries as this invocation's single routing transition.
5. **Stop before destination execution.** Report the chosen route or Route Index by human-readable linked name, its native identity, the request-specific reason, and any reopening condition.

### Advance a route

Use when a destination is known or likely, compatible work may exist, or the user wants to resume or hand off work.

1. **Load low resolution.** If the user names a Route Index, read its opening and latest observations, not every linked destination. Otherwise recover the Query and discover live candidates directly.
2. **Choose the frontier transition.** Use a user-named compatible transition or the first live takeable/resumable entry. Search native tasks and artifacts before creation; unresolved overlap returns one blocker instead of a competing writer.
3. **Advance once.** Resume one compatible task or conversation; create one destination when none exists and creation is authorized; send one bounded handoff or follow-up; redirect lifecycle work to its native authority; or return one permitted event to the Query.
4. **Carry a bounded handoff.** Include the Query reference, requested outcome, resolved target scope, constraints and exclusions, explicitly requested consequential effects, current native evidence, unresolved gates, and stable destination identity. The destination applies its own admission and instructions.
5. **Append the observation.** When a Route Index exists, append the transition and resulting low-resolution state. With active consent, update the local rediscovery line using only its four allowed fields. These pointers never replace live verification.
6. **Stop.** Identify the one transition by its human-readable linked name and native identity, then yield to the destination or Query.

## Return and reconciliation

After a destination exists, ordinary downstream questions, meaningful progress, non-sensitive blockers, and results may return through the originating Query. Credentials, MFA, permission changes, scope expansion, and consequential approvals stay in the destination task where the governing evidence is visible.

- **Question:** return one ordinary decision that does not move destination-owned approval or sensitive context.
- **Progress:** return a meaningful milestone with a destination link and native evidence, not routine activity.
- **Blocker:** return the affected route, current evidence, and reopening condition without exposing sensitive metadata.
- **Result:** carry the destination's terminal claim and native evidence links back to the Query.

Reconcile every result against the Query's original intent. Link repository-native or system-native completion evidence and verify the exact integrated state where the destination contract requires it. A destination task reporting done is an event, not completion evidence by itself.
