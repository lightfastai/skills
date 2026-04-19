# Specification Language Guide

How the specification language should be worded.

## 1. Voice and Tense

- Present tense, active voice throughout.
- Third person only. Never "we" or "you". Use the component name: "the orchestrator decides",
  "the service validates", "implementations should document".
- Declarative statements for behavior: "The poll loop runs every `interval_ms` milliseconds."
- Imperative for requirements: "Normalize labels to lowercase before comparison."

## 2. Obligation Keywords

| Word     | Meaning                                                        |
| -------- | -------------------------------------------------------------- |
| must     | Hard requirement. Conformance depends on it.                   |
| should   | Strong recommendation. Deviations require justification.       |
| may      | Optional. Implementation decides.                              |
| required | Field or behavior is mandatory for dispatch/conformance.       |
| optional | Field or behavior can be omitted without breaking conformance. |

Use "should" as the default for behavioral guidance. Reserve "must" for invariants that, if
violated, break correctness or interoperability.

## 3. Structural Conventions

### Section Headings

- `##` for major numbered sections (Problem Statement, Goals, System Overview).
- `###` for subsections within a section.
- `####` for detailed items (individual entities, config keys, specific behaviors).

### Field Definitions

Use this format for every field in a domain model or config schema:

```
- `field_name` (type, constraints)
  - Semantic description.
  - Default: `value` (if applicable).
```

Type should be the logical type (`string`, `integer`, `boolean`, `list of strings`, `map`,
`timestamp`, `path string`). Include constraints inline: "integer, >= 1", "string or null".

### Component Definitions

Numbered list. Each entry:

```
1. `Component Name`
   - Verb-led sentence describing what it does.
   - Second sentence if needed for scope boundary.
```

### Goals

- Verb-led phrases: "Poll the issue tracker on a fixed cadence."
- One goal per bullet.
- Specific enough to be testable.

### Non-Goals

- Gerund or noun phrases: "Rich web UI or multi-tenant control plane."
- Clarify scope boundaries, not just negations.
- Parenthetical context when useful: "(That logic lives in the workflow prompt.)"

## 4. Annotation Patterns

Use these labeled blocks to break flow and add context without disrupting the main narrative:

- **`Design note:`** — Rationale for a decision. Explains _why_, not _what_.
- **`Important boundary:`** — Scope clarification. Draws a line the spec does not cross.
- **`Important nuance:`** — Subtle behavioral detail that is easy to miss or misimplement.
- **`Note:`** — General supplementary information.
- **`Example:`** or **`Example <qualifier>:`** — Illustrative case, not normative.

Each annotation starts on its own line as a block, not inline.

## 5. State and Lifecycle Descriptions

- Name states in backticks with PascalCase: `Running`, `RetryQueued`, `Released`.
- Use numbered lists for ordered phase sequences (lifecycle stages).
- Use bullet lists for transition triggers (unordered events).
- Describe recovery behavior with conditional format:
  ```
  - <failure class>:
    - <recovery action>.
    - <continuation behavior>.
  ```

## 6. Code and Identifiers

- Backtick all: field names, state names, config keys, file paths, CLI flags, protocol values.
- Use `snake_case` for field and config key names.
- Use `PascalCase` for state names, component names, entity type names.
- Use `UPPER_SNAKE` for environment variables.
- JSON examples use standard formatting with 2-space indent inside fenced blocks.

## 7. Tone

- Dense, not conversational. Every sentence carries information.
- No filler ("it is worth noting that", "in order to").
- No hedging ("perhaps", "it might be useful to").
- Specificity over abstraction. Prefer "30000 milliseconds" over "a reasonable interval".
- When a default exists, state it. When a range is valid, state the bounds.
