---
name: ask-jeevan
description: Recommend one route from the public Lightfast v1 route map. Invoke explicitly when you want a single route recommendation without starting or changing work.
---

# Ask Jeevan

You do not need to remember every Lightfast route, so ask.

This skill is a stateless, recommendation-only index. Use only the originating conversation and the request already in context. Do not inspect live systems, open or resume tasks, invoke the recommended skill, or perform any other effect.

## Route map

| Route | Choose it when | Next invocation |
| --- | --- | --- |
| `/ship` | A bounded code-delivery outcome should reach the target repository's own completion boundary. | `$ship` |
| `/improve` | A bounded campaign should evaluate an exact Orchestrator revision and reach an evidence or improvement disposition. | `$improve` |
| `/navigate` | The live Lightfast destination is uncertain, compatible work may already exist, or one route needs to be found, resumed, or advanced. | `$navigate` |
| `/manage-public-presence` | A controlled public identity needs an audit, setup, correction, deployment, reindexing, or monitoring. | `$manage-public-presence` |

Choose the closest specific route. Prefer `/ship`, `/improve`, or `/manage-public-presence` when the request already meets that route's footing; use `/navigate` for live wayfinding or an uncertain destination. Preserve the user's objective, scope, exclusions, and approval boundaries in the suggested prompt.

## Response contract

Return exactly these three lines, then stop:

```text
Route: `/<route>`
Reason: <one sentence tied to the request>
Next: `$<skill> <an intent-preserving invocation>`
```
