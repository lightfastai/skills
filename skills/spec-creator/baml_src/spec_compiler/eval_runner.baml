function CompileSpecBriefFromPacket(packet: SpecEvalPacket) -> SpecBrief {
  client EvalModel
  prompt #"
    Compile a spec brief from the evaluation packet below.

    Task prompt:
    {{ packet.task_prompt }}

    Raw notes:
    {{ packet.raw_notes }}

    Existing spec:
    {{ packet.existing_spec }}

    Expected criteria:
    {{ packet.expected_criteria }}

    Rules:
    - Produce a behavioral service brief suitable for `spec-creator`.
    - Treat expected criteria as evaluation guidance, not as license to invent.
    - Preserve unresolved questions explicitly.
    - Avoid implementation detail.

    {{ ctx.output_format }}
  "#
}

function RenderSpecDocumentDraft(brief: SpecBrief) -> string {
  client EvalModel
  prompt #"
    Draft a `SPEC.md` from the brief below.

    Rules:
    - Keep the document behavioral and language-agnostic.
    - Use problem statement, goals, non-goals, boundaries, components,
      dependencies, and entities.
    - Preserve uncertainty where the source packet is in transition.
    - Avoid implementation detail.

    Brief:
    {{ brief|format(type="yaml") }}
  "#
}

function EvaluateSpecDocument(
  packet: SpecEvalPacket,
  candidate_document: string
) -> EvalReport {
  client EvalModel
  prompt #"
    Evaluate the candidate `SPEC.md` against the evaluation packet.

    Packet:
    {{ packet|format(type="yaml") }}

    Candidate document:
    {{ candidate_document }}

    Rules:
    - Grade against the expected criteria explicitly.
    - Penalize invented capabilities, invented certainty, or implementation leakage.
    - Reward correct scope boundaries and careful handling of transition states.
    - Use `Pass`, `Partial`, or `Fail` for each criterion.

    {{ ctx.output_format }}
  "#
}
