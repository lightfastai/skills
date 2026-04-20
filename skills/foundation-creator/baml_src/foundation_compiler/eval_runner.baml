function CompileFoundationBriefFromPacket(packet: FoundationEvalPacket) -> FoundationBrief {
  client EvalModel
  prompt #"
    {{ _.role("user") }}
    Compile a foundation brief from the evaluation packet below.

    Task prompt:
    {{ packet.task_prompt }}

    Raw notes:
    {{ packet.raw_notes }}

    Expected criteria:
    {{ packet.expected_criteria }}

    Rules:
    - Produce a concise, durable foundation brief.
    - Preserve ambiguity where the notes do not settle the framing.
    - Treat expected criteria as evaluation guidance, not as license to invent.
    - Avoid implementation detail.
    - Do not infer monetization, metrics, org structure, GTM strategy, or operating plans unless the packet explicitly supports them.
    - If `strategic_bets` are included, phrase them as observed directional signals or evidence.
    - Each `strategic_bets` item should start with explicit hedge language such as `The notes suggest a bet on...`, `There are visible signals that...`, or `The company appears to be betting on...`.
    - Do not use bare `Bet:` labels or categorical claims like `X is the wedge` or `Y is a defensible primitive`.
    - Keep `strategic_bets` short when evidence is weak.
    - Keep unresolved questions as actual unresolved questions rather than quietly resolving them in the summary.
    - Prefer omission over speculation.

    {{ ctx.output_format }}
  "#
}

function RenderFoundationDocumentDraft(brief: FoundationBrief) -> string {
  client EvalModel
  prompt #"
    {{ _.role("user") }}
    Draft a top-level foundation document from the brief below.

    Rules:
    - Write a durable foundation document, not a `SPEC.md`, strategy memo, roadmap, or operating plan.
    - Start from thesis and boundaries, not architecture.
    - Preserve unresolved questions explicitly.
    - Avoid implementation detail.
    - Stay source-bound: do not invent monetization, KPIs, org structure, partnerships, operating guidance, or next-step plans.
    - Prefer omission over plausible-sounding speculation.
    - Return markdown.
    - Start with `# <Primitive Name> Foundation`.
    - Use exactly these `##` sections and no others:
      - `## What This Is`
      - `## Core Thesis`
      - `## Boundaries`
      - `## Actor Model`
      - `## Durable Surfaces`
      - `## Strategic Bets`
      - `## Open Questions`
    - If `Strategic Bets` is weakly supported, keep it short rather than expanding it.
    - Phrase `Strategic Bets` as observed directional bets or public signals, not recommendations or settled future state.
    - Each `Strategic Bets` bullet must start with explicit hedge language such as `The notes suggest a bet on...`, `There are visible signals that...`, or `The company appears to be betting on...`.
    - Do not use bare `Bet:` labels or categorical statements like `X is the wedge` or `Y is a defensible primitive`.
    - When a surface is visible but still evolving in the packet, qualify it explicitly as emerging, evolving, or unsettled.
    - Write `Open Questions` as actual unresolved questions, typically ending with `?`.
    - Do not use market-leadership or competitive-superiority language unless the packet explicitly supports it.

    Brief:
    {{ brief|format(type="yaml") }}
  "#
}

function EvaluateFoundationDocument(
  packet: FoundationEvalPacket,
  candidate_document: string
) -> EvalReport {
  client EvalModel
  prompt #"
    {{ _.role("user") }}
    Evaluate the candidate foundation document against the evaluation packet.

    Packet:
    {{ packet|format(type="yaml") }}

    Candidate document:
    {{ candidate_document }}

    Rules:
    - Grade against the expected criteria explicitly.
    - Reward preservation of uncertainty when the source packet is genuinely mixed.
    - Penalize invented certainty, invented capabilities, or implementation leakage.
    - Penalize unsupported business-model, monetization, KPI, org, partnership, or operating-plan language.
    - Penalize consulting-style sections such as `Success Signals`, `Metrics`, `Decision Agenda`, `Next Steps`, `Operating Guidance`, or similar drift.
    - Penalize missing markdown heading structure if the document drifts from the required template shape.
    - Penalize `Strategic Bets` phrased as recommendations or settled conclusions when the packet only supports directional evidence.
    - Penalize flattening transitional surfaces as fully settled if the packet presents them as evolving.
    - Penalize `Open Questions` that silently resolve ambiguity instead of keeping it open.
    - Penalize market-leadership or competitive-superiority claims not explicitly supported by the packet.
    - Use `Pass`, `Partial`, or `Fail` for each criterion.

    {{ ctx.output_format }}
  "#
}
