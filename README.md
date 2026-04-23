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
bun run eval:foundation -- update-lightfast-foundation-boundary-surface-question
bun run eval:foundation -- update-lightfast-foundation-tighten-overreach
bun run eval:spec -- create-from-vercel-mcp-source-packet
bun run eval:spec -- --all
bun run with-env -- bun ./scripts/run-baml-eval.ts foundation-creator create-foundation-from-cloudflare-source-packet --eval-profile gate --trials 3
bun run with-env -- bun ./scripts/run-baml-eval.ts foundation-creator update-lightfast-foundation-tighten-overreach --eval-profile fast --compare previous,profile:no-skill
bun run with-env -- bun ./scripts/run-baml-eval.ts foundation-creator create-foundation-from-lightfast-founder-notes --eval-profile cross
```

Each run writes packet, brief, candidate document, and evaluation report
artifacts under `skills/<skill>/evals/runs/`.

Current `foundation-creator` corpus includes:

- `create-foundation-from-vercel-source-packet`
- `create-foundation-from-cloudflare-source-packet`
- `create-foundation-from-lightfast-founder-notes`
- `create-foundation-from-harbor-care-source-packet`
- `update-lightfast-foundation-boundary-surface-question`
- `update-lightfast-foundation-tighten-overreach`

The runner now also writes:

- `deterministic_checks.json` — reference-driven checks derived from the skill's
  `template.md` and `language.md`
- `timing.json` — per-stage local timing
- `summary.json` — per-trial LLM status + combined status
- `benchmark.json` — aggregated status counts and timing summaries across all
  trials

When `--compare` is used, the run directory also includes:

- `comparison.json` — head-to-head summary across variants, all judged by the
  current skill's evaluator
- `variants/<label>/...` — per-variant packet/brief/candidate/report artifacts
  and `benchmark.json`

When `--all` is used, the runner executes every eval in the selected skill
manifest and writes a suite directory under `skills/<skill>/evals/runs/` with:

- `suite.json` — aggregate status summary for every eval in the manifest
- `<eval-name>/...` — the normal per-eval artifacts for each manifest entry

Suite mode exits nonzero if any eval has a non-`Pass` combined status, making it
suitable for CI gates.

Current comparison variants:

- `current` — working tree prompt stack
- `previous` — `HEAD~1` snapshot of the skill
- `profile:no-skill` — intentionally under-scaffolded baseline profile for
  measuring how much the foundation-specific prompt constraints matter

Current eval profiles:

- `fast` — candidate and judge both run on `openai/gpt-5.4-mini`
- `gate` — candidate runs on `openai/gpt-5.4-mini`, judge runs on `openai/gpt-5.4`
- `prod` — candidate uses the skill's default authoring model from `baml_src/clients.baml`, judge runs on `openai/gpt-5.4`
- `cross` — candidate runs on `openai/gpt-5.4-mini`, judge runs on `anthropic/claude-opus-4-7`

The default authoring client in each skill's `baml_src/clients.baml` is
`openai/gpt-5.4` for higher-quality foundation/spec generation. Eval profiles
override that default so the tuning loop can stay on cheaper candidate models.

`fast` is the default when `--eval-profile` is omitted.
Model profiles are applied as overlay fixtures, so prompt comparisons against
`previous` or `profile:no-skill` stay on the same candidate/judge model split.
The `cross` profile requires Anthropic model access through Vercel AI Gateway.

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
bun run with-env -- bun ./scripts/run-baml-eval.ts foundation-creator create-foundation-from-vercel-source-packet
```

## License

MIT
