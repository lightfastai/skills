# Lightfast Skills

Agent skills published by Lightfast. Compatible with the [Agent Skills](https://agentskills.io/) specification.

## Skills

| Skill | Purpose |
|---|---|
| [`manage-public-presence`](skills/manage-public-presence/) | Audit and manage controlled public identity across websites, source hosts, registries, profiles, search systems, and AI retrieval. |

## Install

```bash
npx skills add lightfastai/skills --skill manage-public-presence
```

## Security

Published skill content must contain no credentials, private identifiers,
internal URLs, unpublished principal data, or copied provider responses.
Provider-aware skills may describe only the public integrations required by
their declared purpose. Operational outputs should minimize and mask sensitive
metadata by default.

## License

MIT
