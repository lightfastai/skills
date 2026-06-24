# Lightfast Skills

Agent skills published by Lightfast. Compatible with [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and the [Agent Skills](https://agentskills.io/) specification.

## Skills

| Skill | Purpose |
|---|---|
| [`foundation-creator`](skills/foundation-creator/) | Draft or update a top-level foundation document for an early product, company primitive, or strategic bet. |
| [`lightfast-linear`](skills/lightfast-linear/) | Shape Lightfast MCP work into lightweight Linear projects, milestones, and artifact-shaped issues. |
| [`spec-creator`](skills/spec-creator/) | Draft or update a top-level `SPEC.md` service specification. |

## Install

Install a skill into a project:

```bash
npx skills add lightfastai/skills --skill foundation-creator
npx skills add lightfastai/skills --skill lightfast-linear
npx skills add lightfastai/skills --skill spec-creator
```

Or copy a skill directory from `skills/` into `.claude/skills/` in your project.

## Repository Layout

```text
skills/
  foundation-creator/
  lightfast-linear/
  spec-creator/
scripts/
  check-eval-fixtures.ts
  run-baml-eval.ts
  braintrust-evals.ts
evals/
  TAXONOMY.md
```

## Local Development

Install dependencies:

```bash
bun install
```

Run the cheap deterministic checks:

```bash
bun run eval:check
```

Run the full CI check:

```bash
bun run ci:check
```

Run smoke evals:

```bash
bun run eval:foundation:smoke
bun run eval:spec:smoke
```

Run one eval:

```bash
bun run eval:foundation -- create-foundation-from-lightfast-founder-notes
bun run eval:spec -- create-from-vercel-mcp-source-packet
```

Eval outputs are written to:

```text
skills/<skill>/evals/runs/
```

## Eval Notes

`foundation-creator` and `spec-creator` have BAML-backed fixture evals. `lightfast-linear` is currently guidance-only and does not have eval fixtures.

Useful commands:

```bash
bun run eval:typecheck
bun run braintrust:list -- --limit 5
bun run braintrust:latest -- --capability foundation-doc
bun run braintrust:latest -- --capability service-spec
```

Environment variables can live in `.env`; model-backed eval and Braintrust commands load it through `dotenv-cli`.

Optional Braintrust export requires `BRAINTRUST_API_KEY`. The default project is `lightfast-skills`, override with `BRAINTRUST_PROJECT`.

## License

MIT
