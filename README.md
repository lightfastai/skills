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
bun install
bun run eval:foundation -- create-foundation-from-vercel-source-packet
bun run eval:foundation -- create-foundation-from-lightfast-founder-notes
bun run eval:spec -- create-from-vercel-mcp-source-packet
bun run with-env -- bun run ./scripts/run-baml-eval.mjs foundation-creator create-foundation-from-cloudflare-source-packet --trials 3
```

Each run writes packet, brief, candidate document, and evaluation report
artifacts under `skills/<skill>/evals/runs/`.

Current `foundation-creator` corpus includes:

- `create-foundation-from-vercel-source-packet`
- `create-foundation-from-cloudflare-source-packet`
- `create-foundation-from-lightfast-founder-notes`
- `create-foundation-from-harbor-care-source-packet`

The runner now also writes:

- `deterministic_checks.json` — reference-driven checks derived from the skill's
  `template.md` and `language.md`
- `timing.json` — per-stage local timing
- `summary.json` — per-trial LLM status + combined status
- `benchmark.json` — aggregated status counts and timing summaries across all
  trials

Eval manifests also carry lightweight taxonomy metadata
(`scenario_type`, `input_shape`, `ambiguity_level`, `domain_profile`,
`primary_risks`) so benchmark runs can be grouped by failure mode. Shared
taxonomy guidance lives in [`evals/TAXONOMY.md`](evals/TAXONOMY.md).

When `--trials N` is used, the run directory contains `trial-1/`, `trial-2/`,
... plus a top-level `benchmark.json`.

`bun run eval:*` loads `.env` automatically through `dotenv-cli`, so
`AI_GATEWAY_API_KEY` can live in the repo-local `.env` without manual
`source` steps.

For other local commands that should inherit `.env`, use:

```bash
bun run with-env -- bun run ./scripts/run-baml-eval.mjs foundation-creator create-foundation-from-vercel-source-packet
```

## License

MIT
