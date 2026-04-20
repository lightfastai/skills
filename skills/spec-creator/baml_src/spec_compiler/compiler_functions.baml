function ExtractClaims(raw_notes: string) -> Claim[] {
  client EvalModel
  prompt #"
    {{ _.role("user") }}
    Extract atomic claims from the raw notes below.

    Rules:
    - Preserve the original intent.
    - Split compound statements into separate claims when useful.
    - Use `Fact` only for concrete statements in the notes.
    - Use `Thesis` for directional beliefs that still affect scope.
    - Use `Boundary` for explicit scope limits or exclusions.
    - Use `Constraint` for hard operating requirements.
    - Use `OpenQuestion` when the note is unresolved.
    - Keep `sources` short and human-readable.

    Raw notes:
    {{ raw_notes }}

    {{ ctx.output_format }}
  "#
}

function CompileSpecBrief(raw_notes: string, existing_spec: string?) -> SpecBrief {
  client EvalModel
  prompt #"
    {{ _.role("user") }}
    Compile a spec brief from the inputs below.

    Rules:
    - Produce a behavioral brief suitable for `spec-creator`.
    - Prefer service-level behavior over product doctrine.
    - Preserve unresolved questions explicitly.
    - Do not invent implementation detail.
    - If `existing_spec` is present, preserve compatible intent and only sharpen gaps.

    Raw notes:
    {{ raw_notes }}

    Existing spec:
    {{ existing_spec }}

    {{ ctx.output_format }}
  "#
}

function CritiqueSpecBrief(brief: SpecBrief) -> SpecCritique {
  client EvalModel
  prompt #"
    {{ _.role("user") }}
    Critique the spec brief below.

    Rules:
    - Flag contradictions across goals, non-goals, and boundaries.
    - Flag implementation leakage.
    - Flag ambiguous terms that weaken a behavioral specification.
    - Flag missing sections implied by the current brief.

    Brief:
    {{ brief|format(type="yaml") }}

    {{ ctx.output_format }}
  "#
}

function RenderSpecCreatorPrompt(brief: SpecBrief) -> string {
  client EvalModel
  prompt #"
    {{ _.role("user") }}
    Render a prompt for the `spec-creator` skill using the brief below.

    Rules:
    - Ask for a top-level `SPEC.md`.
    - Keep the output language-agnostic and behavioral.
    - Preserve unresolved questions instead of inventing decisions.
    - Emphasize problem statement, goals, non-goals, components, dependencies, and entities.
    - Make the prompt directly usable by an agent.

    Brief:
    {{ brief|format(type="yaml") }}
  "#
}
