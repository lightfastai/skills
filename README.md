# Lightfast Skills

Agent skills published by Lightfast. Compatible with the [Agent Skills](https://agentskills.io/) specification.

## Skills

| Skill | Purpose |
|---|---|
| [`ask-jeevan`](skills/ask-jeevan/) | Explicit-only, stateless advice across available project capabilities and Lightfast core routes. |
| [`navigate`](skills/navigate/) | Chart or advance a live Lightfast route through a native frontier without owning destination work. |
| [`ship`](skills/ship/) | Hand a bounded code-delivery outcome to the authoritative `ship` Orchestrator task. |
| [`improve`](skills/improve/) | Hand an exact-revision Orchestrator improvement campaign to the authoritative `improve` task. |
| [`manage-public-presence`](skills/manage-public-presence/) | Audit and manage controlled public identity across websites, source hosts, registries, profiles, search systems, and AI retrieval. |

## Install

Install all Lightfast core routes together:

```bash
npx skills add lightfastai/skills --skill ask-jeevan navigate ship improve manage-public-presence
```

To install a single skill, keep only its name after `--skill`. Optional project
capabilities remain separately installed and discoverable by `$ask-jeevan`.

## Discovery and invocation

Invoke `$ask-jeevan` explicitly when you want advisory routing. It responds
naturally when no route is needed, may recommend one specialist capability
that is actually available in the current project, and retains `/ship`,
`/improve`, `/navigate`, and `/manage-public-presence` as Lightfast core
routes. It performs no effects and stops after at most one recommendation.

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
LIGHTFAST_RUN_INSTALLER_TESTS=1 python3 -m unittest discover -s tests -v
```

This deterministic local check validates package metadata, invocation policy,
the core route set, forbidden runtime lookup paths, README discovery, and
advisory, locator-surface, frontier, Route Index, approval, recovery, and
reconciliation invariants without binding them to generated wording. The
fixtures are deterministic contract data with fake user messages and native
surface call transcripts ready for later replay. They do not execute a model
or prove behavioral quality. The opt-in third command uses the current Skills
CLI to make a fresh copied installation, verify every source byte, and list all
five installed packages. None of these checks adds a scheduled workflow.

## Security

Published skill content must contain no credentials, private identifiers,
internal URLs, unpublished principal data, or copied provider responses.
Provider-aware skills may describe only the public integrations required by
their declared purpose. Operational outputs should minimize and mask sensitive
metadata by default.

## License

MIT
