# Lightfast Skills

Agent skills published by Lightfast. Compatible with [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and the [Agent Skills](https://agentskills.io/) specification.

## Skills

| Skill | Purpose |
|---|---|
| [`foundation-creator`](skills/foundation-creator/) | Draft a top-level foundation document for a product or company primitive: thesis, mission, boundaries, actor model, surfaces, strategic bets, and open questions. |
| [`spec-creator`](skills/spec-creator/) | Write and update a top-level `SPEC.md` service specification following a strict template and language guide. |

## Install

Each skill is a subdirectory under `skills/`. To install one into a project:

```bash
npx skills add lightfastai/skills --skill foundation-creator
npx skills add lightfastai/skills --skill spec-creator
```

Or copy the directory directly into `.claude/skills/` in your project.

## Local evals

This repo now includes BAML-backed fixture evals for `foundation-creator` and
`spec-creator`.

```bash
npm install
OPENAI_API_KEY=... npm run eval:foundation -- create-foundation-from-vercel-source-packet
OPENAI_API_KEY=... npm run eval:spec -- create-from-vercel-mcp-source-packet
```

Each run writes packet, brief, candidate document, and evaluation report
artifacts under `skills/<skill>/evals/runs/`.

## License

MIT
