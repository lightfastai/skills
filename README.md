# Lightfast Skills

Agent skills published by Lightfast. Compatible with the [Agent Skills](https://agentskills.io/) specification.

## Skills

| Skill | Purpose |
|---|---|
| [`ask-jeevan`](skills/ask-jeevan/) | Explicit-only, stateless recommendation of one public Lightfast route. |
| [`navigate`](skills/navigate/) | Discover, resume, or advance one live route across Lightfast without owning destination work. |
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
`navigate` finds or advances one live route. `ship` and `improve` are public
adapters: their packages here own the handoff contract, while their standalone
Orchestrator repositories remain authoritative for execution and completion.

## Validate

```bash
python3 scripts/validate_routing_skills.py
```

This deterministic local check validates package metadata, invocation policy,
route and adapter integrity, progressive references, and README discovery. It
does not consult a runtime registry or add a scheduled workflow.

## Security

Published skill content must contain no credentials, private identifiers,
internal URLs, unpublished principal data, or copied provider responses.
Provider-aware skills may describe only the public integrations required by
their declared purpose. Operational outputs should minimize and mask sensitive
metadata by default.

## License

MIT
