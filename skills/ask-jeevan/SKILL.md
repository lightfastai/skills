---
name: ask-jeevan
description: Recommend one route from the public Lightfast v1 route map. Invoke explicitly when you want a single route recommendation without starting or changing work.
---

# Ask Jeevan

You do not need to remember every Lightfast route, so ask.

A **flow** is the path from an originating **Query** conversation to one bounded outcome and back to evidence-based reconciliation. The public v1 flow has four routes. This skill recommends where to enter; it is stateless, performs no effect, and never enters the route itself.

## The main flow: Query → bounded outcome → reconciliation

Most Lightfast work follows this path.

1. **Start from the Query.** Preserve the requested outcome, target scope, constraints, exclusions, and approval boundaries already in the conversation. The Query remains the place where the original intent is reconciled later.
2. **Branch: does the live route need wayfinding?**
   - **Yes** → `/navigate` when the destination is uncertain, compatible work may already exist, the work crosses tasks or systems, or the requested outcome changes Orchestrator lifecycle rules. Navigate finds or advances one live transition without owning the destination work.
   - **No** → enter the closest outcome route directly:
     - `/ship` for a bounded code-delivery outcome that must reach the target repository's own completion boundary;
     - `/improve` for a bounded evidence or improvement campaign against one exact Orchestrator revision; or
     - `/manage-public-presence` for an owned public identity that needs audit, setup, correction, deployment, reindexing, or monitoring.
3. **Let the destination admit and own the work.** The next skill discovers or resumes its destination task, applies current native instructions, and keeps execution state in the authority home. Ask Jeevan does none of that work.
4. **Reconcile through the Query.** Ordinary questions, meaningful progress, non-sensitive blockers, and results may return. Credentials, MFA, permissions, scope expansion, and consequential approvals stay in the destination task. A result closes the flow only when it matches the original intent and links native completion evidence.

### Context hygiene

Keep the Query intact until the route is selected: its exact intent is the source for the downstream handoff and later reconciliation. A destination task is a new authority context, not spare context for the Query. Return concise events and evidence links rather than copying the destination conversation back.

## On-ramps

Starting situations join the main flow at different points.

- **Work is already underway or was interrupted** → `/navigate` in Advance mode. It searches native tasks and artifacts, resumes compatible work before creating anything, and moves one transition.
- **The route is foggy or spans multiple contexts** → `/navigate` in Find mode. It discovers live capabilities and may establish a low-resolution Route Index only when continuity warrants one.
- **The request changes how Orchestrators are created, evaluated, checked for conformance, or upgraded** → `/navigate`. Lifecycle authority takes precedence over an exact-revision improvement campaign.
- **The request evaluates or improves one exact Orchestrator revision within a bounded trial and disposition ceiling** → `/improve`. Evidence does not grant authority to change lifecycle rules.
- **An accepted code outcome is ready for repository-native delivery** → `/ship`. Work whose outcome is an Orchestrator lifecycle-rule change enters through `/navigate`, not Ship.
- **The outcome is the principal's controlled public identity** → `/manage-public-presence`, even when the authorized work includes site deployment or index notification.

## Operational wayfinding

`/navigate` has two modes. **Find a route** names the destination, discovers current candidates, and separates takeable routes from routing fog. **Advance a route** selects one compatible frontier transition, preferring resumable native work over a duplicate destination.

Simple direct routes need no routing artifact. When continuity genuinely spans contexts, Navigate may use one native append-only Route Index task as the canonical low-resolution index. Ask Jeevan never inspects, creates, or updates it.

## Phase boundaries

- **Query → route:** recommend one next invocation with the original scope and exclusions intact.
- **Route → destination task:** the downstream skill resolves live identity and admission; this recommendation transfers no extra authority.
- **Destination task → Query event:** ordinary questions, meaningful progress, blockers, and results may return; sensitive approvals remain where their evidence lives.
- **Result → reconciliation:** compare the native result with the original Query and link repository-native or system-native evidence. A task saying it is done is not evidence by itself.

## Standalone routes

Each public route can be invoked directly when the user already knows where to enter:

- `/ship` owns the handoff into the standalone Ship Orchestrator for bounded code delivery.
- `/improve` owns the handoff into the standalone Improve Orchestrator for exact-revision campaigns.
- `/navigate` owns live Lightfast wayfinding and one-step route advancement.
- `/manage-public-presence` owns controlled public-identity operations.

## Preconditions

- `/ship` needs a bounded code outcome, target scope, material constraints, and every requested consequential effect.
- `/improve` needs an exact target Orchestrator revision, bounded trials or selector, target scope and finding destinations, resource limits, evidence burden, and a disposition ceiling.
- `/navigate` needs the Query's intent and current authority; a Route Index is optional and never required for a trivial direct route.
- `/manage-public-presence` needs a principal and legitimately controlled surfaces; its own admission determines the narrowest authorized mode.

Missing detail belongs in the next invocation for the chosen route to resolve. Ask Jeevan does not interrogate live systems or perform setup.

## Response contract

Return exactly these three lines, then stop:

```text
Route: `/<route>`
Reason: <one sentence tied to the request>
Next: `$<skill> <an intent-preserving invocation>`
```
