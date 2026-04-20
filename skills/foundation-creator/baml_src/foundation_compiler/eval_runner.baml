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

    {{ ctx.output_format }}
  "#
}

function RenderFoundationDocumentDraft(brief: FoundationBrief) -> string {
  client EvalModel
  prompt #"
    {{ _.role("user") }}
    Draft a top-level foundation document from the brief below.

    Rules:
    - Write a durable strategic document, not a `SPEC.md`.
    - Start from thesis and boundaries, not architecture.
    - Preserve unresolved questions explicitly.
    - Avoid implementation detail.

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
    - Use `Pass`, `Partial`, or `Fail` for each criterion.

    {{ ctx.output_format }}
  "#
}
