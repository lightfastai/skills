function ExtractClaims(raw_notes: string) -> Claim[] {
  client EvalModel
  prompt #"
    {{ _.role("user") }}
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
    - Do not infer business model, monetization, org structure, metrics, or roadmap items unless explicit in the notes.
    - Prefer omission over speculation.

    Raw notes:
    {{ raw_notes }}

    {{ ctx.output_format }}
  "#
}

function BuildFoundationKernel(claims: Claim[]) -> FoundationKernel {
  client EvalModel
  prompt #"
    {{ _.role("user") }}
    Build a stable foundation kernel from the extracted claims below.

    Rules:
    - Preserve ambiguity when the claims do not support a hard decision.
    - Capture durable thesis-level information.
    - Do not invent implementation detail.
    - Use empty lists when a category is not yet supported by the claims.
    - Do not infer monetization, pricing, KPIs, org structure, GTM strategy, partnership priorities, or execution plans unless explicitly supported.
    - Prefer a shorter kernel over a speculative one.

    Claims:
    {{ claims|format(type="yaml") }}

    {{ ctx.output_format }}
  "#
}

function CritiqueFoundationKernel(kernel: FoundationKernel) -> FoundationCritique {
  client EvalModel
  prompt #"
    {{ _.role("user") }}
    Critique the foundation kernel below.

    Rules:
    - Flag contradictions across thesis, boundaries, and bets.
    - Flag vague claims that should be sharpened before document rendering.
    - Flag implementation leakage.
    - Flag unsupported inferences that are plausible-sounding but not clearly supported by source material.
    - Flag missing boundaries that create strategic confusion.
    - Flag consulting-style drift such as metrics, decision agendas, operating plans, or monetization claims.
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
    {{ _.role("user") }}
    Compile a concise foundation brief from the kernel and critique below.

    Rules:
    - Optimize for document rendering, not implementation planning.
    - Preserve unresolved questions explicitly.
    - Exclude critique items that were already resolved by the kernel.
    - Keep the brief compact and high-signal.
    - Remove unsupported inferences rather than softening them.
    - Prefer omission over consultant-style expansion.
    - Do not add business-model, KPI, org, roadmap, or operating-plan language unless source-backed.
    - Treat `strategic_bets` as observed directional bets, not recommendations or settled future state.
    - If a surface is visible but still in transition, preserve that qualification in the surrounding summary or questions.
    - Avoid market-leadership or competitive-superiority language unless directly supported by source material.

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
    {{ _.role("user") }}
    Render a prompt for the `foundation-creator` skill using the brief below.

    Rules:
    - Ask for a top-level foundation document.
    - Preserve strategic ambiguity where the brief leaves open questions.
    - Avoid implementation detail.
    - Emphasize thesis, boundaries, actor model, surfaces, and strategic bets.
    - State that the writer is a source-bound synthesizer, not a strategy consultant.
    - Require exactly these sections unless the user asks otherwise: `What This Is`, `Core Thesis`, `Boundaries`, `Actor Model`, `Durable Surfaces`, `Strategic Bets`, `Open Questions`.
    - Forbid extra sections like `Success Signals`, `Metrics`, `Decision Agenda`, `Next Steps`, `Operating Guidance`, or `Roadmap`.
    - Require `Strategic Bets` to be phrased as observed directional bets rather than prescriptions.
    - Require recently emerging or transitional surfaces to be qualified explicitly rather than flattened as fully settled.
    - Forbid market-leadership or superiority claims unless they are explicit in the brief.
    - Make the prompt directly usable by an agent.

    Brief:
    {{ brief|format(type="yaml") }}
  "#
}
