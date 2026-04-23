# Eval Runner Modules

This directory holds reusable primitives for local skill eval runners. Keep
modules small and project-agnostic so other repos can copy the runner without
bringing Lightfast-specific skill logic with it.

Current modules:

- `baml.ts` regenerates and imports generated BAML clients.
- `cli.ts` parses command-line flags into a runner request.
- `manifest.ts` loads eval manifests, selects eval entries, and builds packets
  from fixture files.
- `normalization.ts` owns post-compile brief normalization before rendering.
- `profiles.ts` defines model profile presets and profile summaries.
- `reports.ts` builds benchmark, comparison, and suite-summary artifacts.
- `runtime.ts` owns process/runtime helpers such as command execution and file
  loading.
- `status.ts` owns pass/partial/fail ordering and numeric summaries.
- `text.ts` owns markdown/text normalization helpers.
- `variants.ts` materializes current, git, and profile-based skill variants.
- `validators/` owns deterministic reference-document checks.

The remaining orchestration in `../run-baml-eval.ts` should stay limited to
three separable areas:

- Trial execution.
- Artifact writing.
- Provider/reporter integrations.

Keep Braintrust or other external reporting behind a reporter interface rather
than adding vendor-specific branches to the runner core.
