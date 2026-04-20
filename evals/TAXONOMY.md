# Eval Taxonomy

This repo tracks eval coverage across a small shared taxonomy so new packets
expand the corpus intentionally instead of growing as one-off examples.

## Manifest fields

Each eval entry in `skills/*/evals/evals.json` should declare:

- `scenario_type`
- `input_shape`
- `ambiguity_level`
- `domain_profile`
- `primary_risks`

These fields are lightweight metadata. They do not change execution, but they
show up in `benchmark.json` so runs can be grouped by failure mode later.

## Canonical scenario types

- `clear_intent_prompt`
  - Straightforward create-mode request with explicit scope and components.
- `unstructured_notes_prompt`
  - Messy notes, but still mostly service-shaped and not deeply ambiguous.
- `source_packet_transition`
  - Curated packet with real-world material that is internally mixed, evolving,
    or timeline-sensitive.
- `update_existing_doc`
  - Existing document is the dominant constraint; success depends on precise
    in-place edits without broad drift.
- `founder_notes_ambiguity`
  - Highly ambiguous notes where positioning, boundaries, and unresolved
    questions matter more than completeness.
- `cross_domain_generalization`
  - Non-default domain chosen to test whether the skill overfits to developer
    infrastructure examples.

## Supporting axes

### `input_shape`

- `direct_prompt`
- `notes_prompt`
- `source_packet`
- `existing_doc_update`

### `ambiguity_level`

- `low`
- `medium`
- `high`

### `domain_profile`

- `developer_infrastructure`
- `company_foundation`
- `non_developer_domain`

### `primary_risks`

Use a short list of the dominant failure modes for the eval. Current common
values:

- `template_drift`
- `implementation_leakage`
- `invented_capabilities`
- `invented_certainty`
- `scope_bleed`
- `source_overfitting`
- `weak_boundaries`
- `update_regression`

## Current expansion priority

The next missing slices are:

- `update_existing_doc` for `foundation-creator` once revise-in-place behavior
  is defined
- baseline comparison runs (`current skill` vs `previous skill` / `no skill`)
  when the local harness is ready to compare deltas directly
- optional Braintrust-style scorer/export integration if local JSON artifacts are
  no longer sufficient for experiment tracking
