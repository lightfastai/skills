# Lightfast Skills

Agent skills published by Lightfast. Compatible with the [Agent Skills](https://agentskills.io/) specification.

## Skills

| Skill | Purpose |
|---|---|
| [`ask-jeevan`](skills/ask-jeevan/) | Explicit-only, stateless recommendation of one public Lightfast route. |
| [`navigate`](skills/navigate/) | Chart or advance a live Lightfast route through a native frontier without owning destination work. |
| [`ship`](skills/ship/) | Hand a bounded code-delivery outcome to the authoritative `ship` Orchestrator task. |
| [`improve`](skills/improve/) | Hand an exact-revision Orchestrator improvement campaign to the authoritative `improve` task. |
| [`manage-public-presence`](skills/manage-public-presence/) | Audit and manage controlled public identity across websites, source hosts, registries, profiles, search systems, and AI retrieval. |

## Install

Install the complete public route set so every `$ask-jeevan` recommendation is
available:

```bash
npx skills add lightfastai/skills --skill ask-jeevan navigate ship improve manage-public-presence
```

To install a single skill, keep only its name after `--skill`.

## Discovery and invocation

Invoke `$ask-jeevan` explicitly when you want one recommendation from the
public v1 map: `/ship`, `/improve`, `/navigate`, or
`/manage-public-presence`. It performs no effects and stops after giving the
next invocation.

The other published skills are available for implicit model discovery.
`navigate` finds or advances one live route. Direct routes need no persistent
artifact; multi-context continuity may use one native append-only Route Index
task. An optional local rediscovery aid requires consent and never becomes an
authority source. `ship` and `improve` are public adapters: their packages here
own the handoff contract, while their standalone Orchestrator repositories
remain authoritative for execution and completion.

## Validate

```bash
python3 scripts/validate_routing_skills.py
python3 -m unittest discover -s tests -v
```

This deterministic local check validates package metadata, invocation policy,
the public route set, Navigate's visible routing architecture, forbidden
runtime lookup paths, README discovery, and realistic flow, frontier, Route
Index, approval, recovery, and reconciliation scenarios. It does not consult a
runtime registry or add a scheduled workflow.

## Security

Published skill content must contain no credentials, private identifiers,
internal URLs, unpublished principal data, or copied provider responses.
Provider-aware skills may describe only the public integrations required by
their declared purpose. Operational outputs should minimize and mask sensitive
metadata by default.

## License

MIT
