function ExtractClaims(raw_notes: string) -> Claim[] {
  client EvalModel
  prompt #"
    Extract atomic claims from the raw notes below.

    Rules:
    - Preserve the original intent.
    - Split compound statements into separate claims when useful.
    - Use `Fact` only for concrete statements in the notes.
    - Use `Thesis` for directional beliefs or long-term positions.
    - Use `Boundary` for explicit scope limits or exclusions.
    - Use `Constraint` for hard operating requirements.
    - Use `OpenQuestion` when the note is unresolved.
    - Keep `sources` short and human-readable.

    Raw notes:
    {{ raw_notes }}

    {{ ctx.output_format }}
  "#
}

function BuildFoundationKernel(claims: Claim[]) -> FoundationKernel {
  client EvalModel
  prompt #"
    Build a stable foundation kernel from the extracted claims below.

    Rules:
    - Preserve ambiguity when the claims do not support a hard decision.
    - Capture durable thesis-level information.
    - Do not invent implementation detail.
    - Use empty lists when a category is not yet supported by the claims.

    Claims:
    {{ claims|format(type="yaml") }}

    {{ ctx.output_format }}
  "#
}

function CritiqueFoundationKernel(kernel: FoundationKernel) -> FoundationCritique {
  client EvalModel
  prompt #"
    Critique the foundation kernel below.

    Rules:
    - Flag contradictions across thesis, boundaries, and bets.
    - Flag vague claims that should be sharpened before document rendering.
    - Flag implementation leakage.
    - Flag missing boundaries that create strategic confusion.
    - Ask only high-leverage clarification questions.

    Kernel:
    {{ kernel|format(type="yaml") }}

    {{ ctx.output_format }}
  "#
}

function CompileFoundationBrief(
  kernel: FoundationKernel,
  critique: FoundationCritique
) -> FoundationBrief {
  client EvalModel
  prompt #"
    Compile a concise foundation brief from the kernel and critique below.

    Rules:
    - Optimize for document rendering, not implementation planning.
    - Preserve unresolved questions explicitly.
    - Exclude critique items that were already resolved by the kernel.
    - Keep the brief compact and high-signal.

    Kernel:
    {{ kernel|format(type="yaml") }}

    Critique:
    {{ critique|format(type="yaml") }}

    {{ ctx.output_format }}
  "#
}

function RenderFoundationCreatorPrompt(brief: FoundationBrief) -> string {
  client EvalModel
  prompt #"
    Render a prompt for the `foundation-creator` skill using the brief below.

    Rules:
    - Ask for a top-level foundation document.
    - Preserve strategic ambiguity where the brief leaves open questions.
    - Avoid implementation detail.
    - Emphasize thesis, boundaries, actor model, surfaces, and strategic bets.
    - Make the prompt directly usable by an agent.

    Brief:
    {{ brief|format(type="yaml") }}
  "#
}
