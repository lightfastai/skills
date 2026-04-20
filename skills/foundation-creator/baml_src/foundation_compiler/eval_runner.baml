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
    - Use exactly these sections and no others: `What This Is`, `Core Thesis`, `Boundaries`, `Actor Model`, `Durable Surfaces`, `Strategic Bets`, `Open Questions`.
    - If `Strategic Bets` is weakly supported, keep it short rather than expanding it.
    - Phrase `Strategic Bets` as observed directional bets, not recommendations or settled future state.
    - When a surface is visible but still evolving in the packet, qualify it explicitly as emerging, evolving, or unsettled.
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
    - Penalize `Strategic Bets` phrased as recommendations or settled conclusions when the packet only supports directional evidence.
    - Penalize flattening transitional surfaces as fully settled if the packet presents them as evolving.
    - Penalize market-leadership or competitive-superiority claims not explicitly supported by the packet.
    - Use `Pass`, `Partial`, or `Fail` for each criterion.

    {{ ctx.output_format }}
  "#
}
