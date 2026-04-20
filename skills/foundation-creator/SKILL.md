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

## Core behavior

- Start from thesis and boundaries, not components.
- Prefer explicit open questions over invented certainty.
- Separate durable beliefs from speculative bets.
- Avoid implementation detail unless the user explicitly wants it.
- Escalate to `spec-creator` only when a subsystem is concrete enough to
  deserve a `SPEC.md`.

## Current compiler surface

This skill includes typed BAML contracts under `baml_src/foundation_compiler/`
for:

- extracting atomic claims from messy notes
- compiling a stable foundation kernel
- critiquing ambiguity, contradiction, and implementation leakage
- compiling a brief suitable for downstream document rendering

The BAML layer is schema-first. Prompt wording and document templates can
evolve without changing the core interfaces.
