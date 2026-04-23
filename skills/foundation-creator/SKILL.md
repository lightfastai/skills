---
name: foundation-creator
description: >
  Use this skill when the user wants to write, draft, update, or revise a
  top-level foundation document for a company, product, or new primitive.
  This document captures thesis, mission, boundaries, actor model, surfaces,
  strategic bets, and open questions without collapsing ambiguity into
  implementation decisions. Applies when the user is still defining what the
  system is, what it is not, and what long-term direction it implies. Does
  NOT apply to concrete service specifications in `SPEC.md`, implementation
  plans, PRDs, or roadmap execution docs.
---

# Foundation Creator

Writes and updates a single top-level foundation document for an early-stage
product or company primitive. The resulting document is strategic and
behavioral, not implementation-level. It should preserve uncertainty where
decisions are not yet mature.

This skill is a source-bound documentarian, not a strategy consultant. Its job
is to synthesize what the available material already supports about the
primitive: what it is, what it is not, what durable surfaces exist, and what
remains unresolved.

## Reference files

Load on demand, not upfront.

- `references/template.md` — the allowed section shape for a foundation
  document. Read it when drafting a new foundation doc and when checking
  whether the output stayed within scope.
- `references/language.md` — wording and restraint rules. Read it before
  writing prose and again during the validation pass.

## Core behavior

- Start from thesis and boundaries, not components.
- Prefer explicit open questions over invented certainty.
- Separate durable beliefs from speculative bets.
- Avoid implementation detail unless the user explicitly wants it.
- When updating an existing foundation document, preserve section order and
  untouched wording unless the request explicitly requires a rewrite.
- Escalate to `spec-creator` only when a subsystem is concrete enough to
  deserve a `SPEC.md`.

## Decide: create or update

Before writing:

1. If the user provides an existing foundation document or asks to revise one,
   use **update mode**.
2. Otherwise, use **create mode**.

Do not treat a revise-in-place request as a greenfield rewrite. The distinction
matters because foundation documents often preserve useful ambiguity that
should not be flattened during an edit.

## Create mode

Gather only what is still missing from the notes:

- what the primitive or company is
- what it is not
- durable thesis-level beliefs
- meaningful actors
- durable surfaces
- unresolved tensions or open questions

Then draft the document using `references/template.md` and validate it against
`references/language.md`.

## Update mode

1. Read the existing foundation document fully.
2. Scope the requested change narrowly.
3. Edit in place:
   - preserve the existing heading structure
   - keep unchanged lines and bullets verbatim where possible
   - add or revise only what the request requires
   - do not add new sections, planning material, or stronger certainty unless
     the request explicitly justifies it
4. Re-read and validate the whole document, not just the changed section.

Typical update shapes:

- add a sharper boundary
- add or remove a durable surface
- clarify a strategic bet without turning it into a recommendation
- add an open question that the earlier draft omitted
- tighten an overconfident sentence back into source-bound language

## Allowed content

- What the primitive is.
- What the primitive is not.
- Durable thesis-level framing.
- Actor model and durable surfaces.
- Strategic bets only when they are clearly supported by the source material.
  Frame them as source-visible directional signals, not recommendations or
  direct claims about company intent. Match the lead-in to the evidence:
  note-style packets should use note-style attribution, and `Public materials
  suggest...`, `Public materials indicate...`, or `Public materials
  emphasize...` should appear only when the packet actually cites public
  sources.
- Open questions and unresolved tensions.

## Forbidden drift

- Do not invent monetization, revenue models, KPIs, or internal
  organizational structure unless the source explicitly states them.
- Do not produce roadmap items, implementation plans, operating cadences,
  pilot programs, or execution checklists unless the user explicitly asks.
- Do not turn open questions into decision agendas or recommended next steps.
- Do not fill gaps with plausible-sounding business language. Prefer omission
  or an explicit unresolved question.
- Do not collapse ambiguous positioning into a single confident frame when the
  source material remains mixed.
- Do not assert market leadership, superiority, or competitive differentiation
  unless the source explicitly makes that claim and it matters to the
  foundation.

## Validation focus

Before finalizing, check for these failure modes:

- unsupported inference
- consulting-style sections (`Success Signals`, `Decision Agenda`,
  `Next Steps`, `Operating Guidance`, similar)
- implementation leakage
- business-model speculation
- metrics or operational milestones not present in the source
- missing explicit open questions where the notes remain unsettled
- update drift that rewrites unchanged material or quietly resolves ambiguity

## Current compiler surface

This skill includes typed BAML contracts under `baml_src/foundation_compiler/`
for:

- extracting atomic claims from messy notes
- compiling a stable foundation kernel
- critiquing ambiguity, contradiction, unsupported inference, and
  implementation leakage
- compiling a brief suitable for downstream document rendering

The BAML layer is schema-first. Prompt wording and document templates can
evolve without changing the core interfaces.
