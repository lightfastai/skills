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
    - Treat `strategic_bets` as source-visible directional signals, not recommendations or settled future state.
    - Each `strategic_bets` item must begin with an evidence-matched source-centered opening.
    - For note-only packets, use `The notes suggest...`, `There are visible signals that...`, or `The source material indicates...`.
    - Use `Public materials suggest...` only when the packet explicitly cites public docs, press releases, or other external sources.
    - Avoid wording that attributes settled intent directly to the company, such as `The company appears to be betting on...`.
    - Forbid prescriptive or categorical phrasing in `strategic_bets`, including `prioritize`, `invest in`, `ship`, `treat as first-class`, `first-class`, `is the wedge`, `is a defensible primitive`, `will remain`, or `matters more than`.
    - Avoid comparative durability claims in `Strategic Bets` such as `more durable than raw prompts` or `will outlast raw prompts`. Prefer source-bound wording like `The source material emphasizes formal constraints and reusable artifacts as durable surfaces relative to raw prompts and transcripts.`
    - If a possible bet cannot be phrased as a source-visible signal without overclaiming, move it to `open_questions` or omit it.
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
    - If the brief includes `existing_foundation`, treat the task as update mode and preserve the existing document verbatim except for the requested edits.
    - In update mode, tell the writer to copy every unchanged bullet and question verbatim instead of paraphrasing it.
    - In update mode, tell the writer not to rewrite or replace existing open questions unless the update request explicitly targets that exact question.
    - In update mode, if the request asks for a new or replacement open question, preserve all other existing open-question bullets exactly and add or replace only the targeted question.
    - In update mode, do not normalize nouns or labels inside unchanged lines; if an unchanged question says `company`, keep `company` rather than rewriting it as `project`, `product`, or `primitive`.
    - In update mode, when the edit request supplies target phrasing for a local rewrite, preserve those anchor words rather than substituting looser synonyms.
    - For example, if the request says `easiest first wedge because eval loops are tighter`, keep both `easiest first wedge` and `eval loops are tighter` explicit in the revised line.
    - If the request names `coding workflows` as the wedge subject, do not substitute `skills`, `skills surface`, or another artifact label as the wedge subject in thesis or strategic-bet wording.
    - Require markdown output with exactly this heading structure unless the user asks otherwise:
      - `# <Primitive Name> Foundation`
      - `## What This Is`
      - `## Core Thesis`
      - `## Boundaries`
      - `## Actor Model`
      - `## Durable Surfaces`
      - `## Strategic Bets`
      - `## Open Questions`
    - Require `Core Thesis`, `Boundaries`, `Actor Model`, `Durable Surfaces`, `Strategic Bets`, and `Open Questions` to use markdown bullets with `- ` for each item rather than paragraph-only prose.
    - Forbid extra sections like `Success Signals`, `Metrics`, `Decision Agenda`, `Next Steps`, `Operating Guidance`, or `Roadmap`.
    - Require `Strategic Bets` to be phrased as source-visible directional signals rather than prescriptions or settled company posture.
    - Require each `Strategic Bets` bullet to begin with an evidence-matched source-centered opening.
    - For note-only packets, use `The notes suggest...`, `There are visible signals that...`, or `The source material indicates...`.
    - Use `Public materials suggest...` only when the packet explicitly cites public docs, press releases, or other external sources.
    - Forbid wording like `The company appears to be betting on...`, bare `Bet:` labels, or categorical claims like `X is the wedge`, `Y is a defensible primitive`, `X will remain the center of gravity`, or `Y matters more than Z`.
    - Forbid prescriptive verbs and categorical labels in `Strategic Bets`, including `prioritize`, `invest in`, `ship`, `treat as first-class`, or `first-class`.
    - Avoid comparative durability claims in `Strategic Bets` such as `more durable than raw prompts` or `will outlast raw prompts`. Prefer source-bound wording like `The source material emphasizes formal constraints and reusable artifacts as durable surfaces relative to raw prompts and transcripts.`
    - If a would-be strategic bet cannot be phrased as a source-visible signal, convert it into an `Open Questions` bullet or omit it.
    - Require recently emerging or transitional surfaces to be qualified explicitly rather than flattened as fully settled.
    - Require `Open Questions` bullets to remain actual unresolved questions rather than disguised conclusions.
    - Forbid market-leadership or superiority claims unless they are explicit in the brief.
    - In update mode, do not add new sections or broad new framing unless the request explicitly asks for them.
    - In update mode, if a boundary, actor, surface, strategic bet, or open question is not part of the requested edit, preserve its wording exactly.
    - In update mode, do not rewrite an existing open question into a nearby broader or narrower variant just because it overlaps with the requested edit. Keep non-targeted questions byte-for-byte except for markdown context required by the edit.
    - In update mode, when adding or replacing an open question, keep the rest of the `Open Questions` list in its original order and wording.
    - In update mode, preserve unchanged nouns and subject labels inside copied lines exactly as written.
    - In update mode, if the request gives a specific comparative or causal formulation, keep that formulation explicit instead of paraphrasing it away.
    - In update mode, if the request says `coding workflows are the easiest first wedge because eval loops are tighter`, keep `coding workflows` as the subject anywhere that wedge claim is restated. Do not rewrite it as `skills` or `skills surface`.
    - Make the prompt directly usable by an agent.

    Brief:
    {{ brief|format(type="yaml") }}
  "#
}
