---
name: navigate
description: Find, resume, or advance a live Lightfast route when the operational destination or authority is uncertain. Use for cross-system wayfinding and one-step handoffs; execution remains with the destination.
---

# Navigate

Navigate is Lightfast's operational router. Its invariant is **route; do not own**: discover the live authority, move the request through one bounded routing transition, and leave execution and durable state with the destination.

The **Query** is the originating task or conversation that holds the user's intent. Keep its native identity so downstream events can return without creating a parallel routing ledger.

## Choose one mode

- **Find a route:** the user needs the best live capability or authority and no transition is ready. Read [references/find-route.md](references/find-route.md), follow it, and stop when one route or one indispensable routing question is returned.
- **Advance a route:** a destination is known or likely, compatible work may exist, or the user wants to resume or hand off work. Read [references/advance-route.md](references/advance-route.md), perform one bounded transition, and stop.

Load only the selected mode reference.

## Shared routing contract

- Recover the Query's bounded objective, target scope, exclusions, consequential effects, and current authority before routing.
- Discover installed skills, live tasks and conversations, connected projects, repositories, systems, and public Orchestrator adapters from their current native surfaces. Verify a candidate's current instructions and availability instead of relying on a maintained exhaustive registry.
- Prefer a compatible existing destination task and native artifacts over creating duplicates. Preserve user changes and unresolved ownership.
- Treat each authority home as authoritative for its own work, approvals, and completion evidence. A route transfers no broader authority than the Query already carries.
- Route work that designs or changes the rules for Orchestrator creation, evaluation, conformance, or upgrades to a task in the live `lightfastai/orchestrator` repository, whose current instructions own that lifecycle. Route a bounded evaluation or authorized improvement campaign for one exact Orchestrator revision through the live `improve` adapter. The Workbench is a lifecycle destination, never a runtime lookup service: do not consult the Workbench or Orchestrator Map to resolve ordinary routes or run another Orchestrator.
- Use a live public adapter such as `ship` or `improve` to enter an Orchestrator runtime. The adapter in `lightfastai/skills` owns the public handoff contract; the destination Orchestrator repository owns admission and execution.
- Complete at most one routing transition per invocation. Do not implement destination work, coordinate its plan, mirror its state, or declare its outcome complete.

## Query and destination boundary

Ordinary downstream questions, meaningful progress, non-sensitive blockers, and results may return through the Query. Credentials, MFA, permission changes, and consequential approvals stay in the destination task where the governing context and evidence are visible.

When a result returns, reconcile it against the Query's original intent and link the repository-native or system-native completion evidence. A destination task reporting done is an event to verify, not completion evidence by itself.

## Response contract

Identify the selected mode. For a successful route, identify one destination or transition, its live identity or link, the reason it fits, and any next gate. For a routing question or blocker, identify the unresolved choice or reopening condition and the relevant live evidence. Keep sensitive operational metadata out of the response.
