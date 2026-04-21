function CompileFoundationBriefFromPacket(packet: FoundationEvalPacket) -> FoundationBrief {
  client EvalModel
  prompt #"
    {{ _.role("user") }}
    Create a foundation brief from the evaluation packet below.

    Task prompt:
    {{ packet.task_prompt }}

    Raw notes:
    {{ packet.raw_notes }}

    Existing foundation:
    {{ packet.existing_foundation }}

    Expected criteria:
    {{ packet.expected_criteria }}

    Guidelines:
    - Produce a clear, polished foundation brief.
    - Summarize the strongest interpretation of what the company or primitive is.
    - Fill in reasonable connective tissue when the packet is incomplete.
    - Organize the result into `summary`, `core_theses`, `boundaries`, `actor_model`, `surfaces`, `strategic_bets`, and `unresolved_questions`.
    - If `existing_foundation` is present, include it and describe the requested changes in `update_request`, but rewrite surrounding language whenever it improves coherence.
    - Prefer a decisive synthesis over a list of fragments.

    {{ ctx.output_format }}
  "#
}

function RenderFoundationDocumentDraft(brief: FoundationBrief) -> string {
  client EvalModel
  prompt #"
    {{ _.role("user") }}
    Draft a polished foundation document from the brief below.

    Guidelines:
    - Write a strong, coherent top-level foundation document.
    - Make the framing crisp and readable, even when the source material is somewhat mixed.
    - Resolve ambiguity when a clearer interpretation improves the document.
    - Use markdown and keep the document compact.
    - Start with `# <Primitive Name> Foundation`.
    - Use these sections:
      - `## What This Is`
      - `## Core Thesis`
      - `## Boundaries`
      - `## Actor Model`
      - `## Durable Surfaces`
      - `## Strategic Bets`
      - `## Open Questions`
    - If `existing_foundation` is present, use it as a starting point but rewrite surrounding content freely when it makes the document more consistent.
    - Favor confident, finished prose over heavily qualified language.

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
    - If `existing_foundation` is present, penalize rewriting unchanged content or adding broad new material outside the requested edit.
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
