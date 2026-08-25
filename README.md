# Lightfast Skills

Agent skills published by Lightfast. Compatible with the [Agent Skills](https://agentskills.io/) specification.

## Skills

| Skill | Purpose |
|---|---|
| [`create-orchestrator`](skills/create-orchestrator/) | Design and conflict-test an unregistered orchestrator charter before adoption. |
| [`manage-public-presence`](skills/manage-public-presence/) | Audit and manage controlled public identity across websites, source hosts, registries, profiles, search systems, and AI retrieval. |
| [`orchestrate`](skills/orchestrate/) | Resolve one registered charter, recover its programme, and request one bounded transition from a read-only root task. |

## Install

```bash
npx skills add lightfastai/skills --skill manage-public-presence
npx skills add lightfastai/skills --skill orchestrate
npx skills add lightfastai/skills --skill create-orchestrator
```

## Orchestrate: first run

`orchestrate` is a coordination kernel, not an implementation agent. Its root
task remains read-only: it resolves one registered charter, recovers durable
programme state, chooses one valid transition, and routes one bounded task
through Ask Matt.

On first run, it reads the authority home's instructions and orchestration
registry, then loads only the selected charter and shared policy. The registry
owns registration and resource claims; the charter owns purpose, programme
discovery, routes, controls, and completion; the configured tracker owns live
state. Missing or ambiguous authority produces one bounded adoption proposal,
not an inferred mutation.

An instance is `charter_id + programme_id`. Draft charters remain proposal-only.
Registered writers may overlap only when resource claims and concurrency permit
it. Meta observation requires bilateral opt-in, and one experiment assignment
stays fixed for its selected work unit.

Use a dry run to inspect the same recovered evidence and proposed transition
without requesting the delegation or any other effect.

The coordination boundary also applies to integrations and approvals.
Provider commands are resolved through declared capabilities; they are not
bundled into `orchestrate`. Credentials, broad
permissions, destructive actions, legal or billing actions, unverified
publishers, paid model runs, persistent external changes, and material scope
expansion pause until the exact bounded approval is recorded.

## Security

Published skill content must contain no credentials, private identifiers,
internal URLs, unpublished principal data, or copied provider responses. The
generic `orchestrate` kernel must additionally remain provider-independent;
provider-aware skills may describe only the public integrations required by
their declared purpose. Operational outputs should minimize and mask sensitive
metadata by default.

`create-orchestrator` is explicit by design. It interviews one decision at a
time, returns an unregistered charter and registry entry, conflict-tests the
authority boundary, and stops before registration or programme mutation.

## License

MIT
