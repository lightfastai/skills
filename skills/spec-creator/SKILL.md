---
name: spec-creator
description: >
  Use this skill when the user wants to write, draft, update, or revise a
  top-level SPEC.md service specification — the language-agnostic behavioral
  spec that sits at a project's root and describes what a long-running
  service or automation does (problem statement, goals/non-goals, components,
  domain model). Applies when the user says things like "write a spec for
  X", "draft a specification", "update SPEC.md to add Y", "revise the
  non-goals", "add a new component to the spec", or hands over notes and
  asks for them to be turned into a formal service spec. Also applies when
  the user references an existing SPEC.md and wants edits, even if they
  don't explicitly use the word "spec". Covers both greenfield creation and
  targeted updates of an existing file. Does NOT apply to per-topic specs
  under thoughts/shared/specs/ (those are produced by create_ralph_topics
  from a JTBD), nor to JTBDs, implementation plans, or PRDs.
---

# Spec Creator

Writes and updates a single `SPEC.md` at the repository root, conforming to a strict section template and wording guide. One file per project. Language-agnostic — the resulting spec describes behavior only, not implementation.

## Reference files

Load on demand, not upfront. The three reference files are short (~100 lines each); read each fully when needed.

- `references/template.md` — the authoritative section structure. Read it when drafting a new spec and when checking whether a section lives in the right place.
- `references/language.md` — wording rules: voice, tense, obligation keywords, field format, annotation patterns, code-identifier casing, tone. Read it before writing prose and again during the validation pass.
- `references/examples/reaper.md` — a complete filled-in spec for a deployment-rollback monitor. Read it when the user asks "what does a good one look like" or when a concrete pattern helps.

Do not paraphrase the reference files from memory. Their rules are specific and easy to recall wrong.

## Decide: create or update

Before writing anything:

1. Check whether `SPEC.md` exists at the repo root.
2. If absent → **Create mode**.
3. If present → **Update mode**. Read the existing file fully before editing.

A user who says "write a spec for X" may already have a stub that should be extended, not overwritten. The check matters.

## Create mode

### 1. Interview first, draft second

The template has 8+ sections and filling them blindly produces generic output. Ask, in order, what the user hasn't already told you:

- What does the service do, in one sentence? → feeds `Purpose` and the opening paragraph.
- What manual or broken process does it replace? What isolation or safety does it provide? What versioning or configuration benefit? → feeds the Problem Statement bullets.
- What is it **not**? What adjacent concerns live elsewhere? → feeds the "Important boundary" block and Non-Goals.
- What are the main components? Name them. → feeds Main Components and Abstraction Levels.
- What external systems does it depend on? → feeds External Dependencies.
- What are the core entities? For each, what fields and types? → feeds the Domain Model.

If the user has supplied notes covering some answers, pull from the notes and ask only what remains. Do not re-ask what's already on the table.

### 2. Draft the spec top-to-bottom

Follow `references/template.md` for section structure and numbering. Keep placeholder markers like `{Service Name}` out of the final output — they scaffold the template file only.

### 3. Validate before handing back

Run the validation pass (below). Fix violations before showing the user.

### 4. Write to `SPEC.md` at the repo root

Not to `thoughts/`, not to `docs/`. If the user explicitly requests a different path, honor it and call out the deviation.

## Update mode

### 1. Read the existing spec fully

Read with no offset or limit. The file is short enough that partial reads waste more tokens than they save.

### 2. Scope the change

Ask what the user wants changed. Common update shapes:

- Add or remove a goal or non-goal.
- Add a new component, rename an existing one, or change its scope sentence.
- Add a field to an entity, change its type, or change its default.
- Rewrite a section that has drifted from current product intent.

### 3. Edit in place

Use Edit for targeted changes. Preserve section numbering, heading depth, and any sections the user did not ask about. If a change forces renumbering (e.g. a new section inserted in the middle), ask first — downstream references may break.

### 4. Validate the whole file, not just the diff

Re-read and re-validate. Edits reliably break field-format consistency and introduce first-person slips.

## Validation

Run every time before finalizing. `references/language.md` is the source of truth; load it for the full list. The recurring failure modes:

**Voice**
- First person anywhere: `we`, `our`, `us`. Replace with the component name. ("The orchestrator decides" not "we decide".)
- Second person: `you`, `your`. Same fix.
- Passive voice in behavioral statements. "The poll loop runs every N ms" not "the poll loop is run every N ms".

**Field format**
- Every field in a domain model or config schema follows: name in backticks, then `(type)` or `(type, constraints)`, then an indented bullet with a semantic description. Defaults use a separate `Default: \`value\`` sub-bullet, not prose.
- Types are logical, not language-specific: `string`, `integer`, `boolean`, `list of strings`, `map`, `timestamp`, `string or null`. Not `int`, `String`, `Option<T>`, `bool`.

**Obligation keywords**
- Lowercase `must`, `should`, `may`. Not `MUST` or `SHOULD`.
- `should` is the default for behavioral guidance. Reserve `must` for invariants whose violation breaks correctness or interoperability.

**Identifiers in backticks**
- Field names, config keys, file paths, CLI flags, environment variables, state names, and protocol values are all in backticks.
- State names are `PascalCase`: `` `Running` ``, `` `RetryQueued` ``, `` `Released` ``.
- Config keys and fields are `snake_case`.
- Environment variables are `UPPER_SNAKE`.

**Tone**
- Filler to cut: "it is worth noting that", "in order to", "perhaps", "it might be useful to".
- Vague bounds: replace "a reasonable interval" with the explicit value (`30000` milliseconds) or the range.

When a violation is found, fix it and re-read the affected section once.

## Section template (compact)

Use this as a quick reminder; defer to `references/template.md` for anything you're unsure about.

```
# {Service Name} Specification

Status: Draft v1 (language-agnostic)
Purpose: {one sentence}

## 1. Problem Statement
## 2. Goals and Non-Goals
### 2.1 Goals
### 2.2 Non-Goals
## 3. System Overview
### 3.1 Main Components
### 3.2 Abstraction Levels
### 3.3 External Dependencies
## 4. Core Domain Model
### 4.1 Entities
#### 4.1.1 {Entity Name}
```

The section set may grow — state machine, configuration, observability, lifecycle — depending on the service. New sections follow the same numbering and heading-depth conventions.

## Gotchas

- **Specs are behavioral.** No function names, class names, framework references, or code blocks showing implementation. "The service persists state" not "`StateManager.write()` serializes to JSON".
- **Don't treat the example as the one true shape.** `references/examples/reaper.md` is a deployment-rollback monitor. A data pipeline, webhook retry service, or CLI tool will have different components and possibly different sections. The language rules are universal; the section set is not.
- **Don't output `{placeholder}` tokens.** They're in the template only for scaffolding.
- **Annotation blocks stand alone.** `Design note:`, `Important boundary:`, `Important nuance:`, `Note:`, `Example:` each start on their own line as a block, not inline.
- **Present tense, active voice.** "The service validates", not "the service will validate" and not "validation is performed by the service".
