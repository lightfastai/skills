function CompileFoundationBriefFromPacket(packet: FoundationEvalPacket) -> FoundationBrief {
  client EvalModel
  prompt #"
    {{ _.role("user") }}
    Compile a foundation brief from the evaluation packet below.

    Task prompt:
    {{ packet.task_prompt }}

    Raw notes:
    {{ packet.raw_notes }}

    Existing foundation:
    {{ packet.existing_foundation }}

    Expected criteria:
    {{ packet.expected_criteria }}

    Rules:
    - Produce a concise, durable foundation brief.
    - Preserve ambiguity where the notes do not settle the framing.
    - Treat expected criteria as evaluation guidance, not as license to invent.
    - Avoid implementation detail.
    - If `existing_foundation` is present, treat this as update mode:
      - preserve the existing section structure
      - carry forward unchanged framing and language verbatim whenever possible
      - extract a narrow `update_request` rather than rewriting the entire document
      - do not resolve existing ambiguity unless the task prompt explicitly asks for it
      - if a boundary, actor, surface, strategic bet, or open question is not explicitly targeted by the task prompt, keep its wording unchanged in the brief
      - do not rewrite or replace an existing open question unless the task prompt explicitly targets that exact question
      - if the task prompt asks for a new or replacement open question, preserve all other existing open-question bullets exactly and add or replace only the targeted question
      - when a line is unchanged, copy its text verbatim from `existing_foundation` instead of normalizing nouns or labels
      - do not rewrite unchanged `company`, `product`, `primitive`, or actor labels into nearby synonyms
      - if the task prompt gives target phrasing for a local rewrite, preserve those anchor words in the rewritten field instead of loosening them into synonyms
      - if the task prompt specifies a comparative or causal clause such as `easiest first wedge because eval loops are tighter`, keep that clause explicit
      - if the task prompt names `coding workflows` as the wedge subject, do not substitute `skills`, `skills surface`, or another artifact label as the wedge subject in thesis or strategic-bet wording
    - Do not infer monetization, metrics, org structure, GTM strategy, or operating plans unless the packet explicitly supports them.
    - If `strategic_bets` are included, phrase them as source-visible directional signals or evidence.
    - Each `strategic_bets` item must begin with an evidence-matched source-centered opening.
    - For note-only packets, use `The notes suggest...`, `There are visible signals that...`, or `The source material indicates...`.
    - Use `Public materials suggest...` only when the packet explicitly cites public docs, press releases, or other external sources.
    - Do not phrase `strategic_bets` as direct statements of company intent such as `The company appears to be betting on...`.
    - Do not use prescriptive or categorical phrasing in `strategic_bets`, including `prioritize`, `invest in`, `ship`, `treat as first-class`, `first-class`, `is the wedge`, `is a defensible primitive`, `will remain`, or `matters more than`.
    - Do not use comparative durability claims in `strategic_bets`, including `more durable than raw prompts` or `will outlast raw prompts`. Prefer source-bound wording like `The source material emphasizes formal constraints and reusable artifacts as durable surfaces relative to raw prompts and transcripts.`
    - If a possible bet cannot be stated as a source-visible signal without overclaiming, move it to `open_questions` or omit it.
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
    - If `existing_foundation` is present, treat this as update mode and let the update-mode rules override the create-mode template-completion rules below.
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
    - Render `Core Thesis`, `Boundaries`, `Actor Model`, `Durable Surfaces`, `Strategic Bets`, and `Open Questions` as markdown bullet lists using `- ` for every item.
    - Do not render `Strategic Bets` or `Open Questions` as paragraph-only prose.
    - If `Strategic Bets` is weakly supported, keep it short rather than expanding it.
    - Phrase `Strategic Bets` as source-visible directional signals, not recommendations or settled future state.
    - Each `Strategic Bets` bullet must begin with an evidence-matched source-centered opening.
    - For note-only packets, use `The notes suggest...`, `There are visible signals that...`, or `The source material indicates...`.
    - Use `Public materials suggest...` only when the packet explicitly cites public docs, press releases, or other external sources.
    - Do not use direct company-intent phrasing such as `The company appears to be betting on...`.
    - Do not use bare `Bet:` labels or categorical statements like `X is the wedge`, `Y is a defensible primitive`, `X will remain the center of gravity`, or `Y matters more than Z`.
    - Do not use prescriptive verbs or categorical labels like `prioritize`, `invest in`, `ship`, `treat as first-class`, or `first-class` in `Strategic Bets`.
    - Do not use comparative durability claims in `Strategic Bets`, including `more durable than raw prompts` or `will outlast raw prompts`. Prefer source-bound wording like `The source material emphasizes formal constraints and reusable artifacts as durable surfaces relative to raw prompts and transcripts.`
    - If a would-be strategic bet cannot be phrased as a source-visible signal, convert it into an `Open Questions` bullet or omit it.
    - When a surface is visible but still evolving in the packet, qualify it explicitly as emerging, evolving, or unsettled.
    - Write `Open Questions` as actual unresolved questions, typically ending with `?`.
    - Do not use market-leadership or competitive-superiority language unless the packet explicitly supports it.
    - If `existing_foundation` is present, treat this as update mode:
      - start from `existing_foundation`
      - preserve all unchanged lines verbatim
      - preserve unchanged bullet wording and unchanged open questions exactly as written
      - do not rewrite or replace existing open questions unless `update_request` explicitly targets that exact question
      - when adding or replacing an open question, keep every other existing open-question bullet in its original order and wording
      - apply only the edits implied by `update_request`
      - do not rewrite existing paragraphs or bullets unless the request requires it
      - do not add new sections or broad new framing unless `update_request` explicitly asks for them
      - copy unchanged lines literally, including nouns and subject labels such as `company`, rather than normalizing them into synonyms
      - if `update_request` supplies target phrasing for a local rewrite, preserve those anchor words rather than replacing them with looser synonyms
      - if `update_request` includes a comparative or causal clause such as `easiest first wedge because eval loops are tighter`, keep that clause explicit in the revised line
      - if `update_request` says `coding workflows are the easiest first wedge because eval loops are tighter`, keep `coding workflows` as the subject anywhere that wedge claim is restated. Do not rewrite it as `skills` or `skills surface`.

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
    - In update mode, do not penalize exactly one added `Open Questions` bullet when the task explicitly asks to restore or add an open question; penalize only unrelated new questions or extra questions beyond the requested one.
    - Penalize unsupported business-model, monetization, KPI, org, partnership, or operating-plan language.
    - Penalize consulting-style sections such as `Success Signals`, `Metrics`, `Decision Agenda`, `Next Steps`, `Operating Guidance`, or similar drift.
    - Penalize missing markdown heading structure if the document drifts from the required template shape.
    - Penalize paragraph-only rendering of list sections that the template expects as markdown bullets, especially `Strategic Bets` and `Open Questions`.
    - `## Strategic Bets` is a required template section. Do not penalize its presence by itself when the bullets remain source-bound and restrained.
    - Penalize `Strategic Bets` phrased as recommendations, direct company-intent claims, or settled conclusions when the packet only supports directional evidence.
    - Penalize `Strategic Bets` that use verbs or labels like `prioritize`, `invest in`, `ship`, `treat as first-class`, `first-class`, `will remain`, or `matters more than`, or phrases like `The company appears to be betting on...`.
    - Penalize evidence-source mismatch inside `Strategic Bets`, such as `Public materials suggest...` when the packet only contains founder notes or internal notes.
    - Penalize flattening transitional surfaces as fully settled if the packet presents them as evolving.
    - Penalize `Open Questions` that silently resolve ambiguity instead of keeping it open.
    - Penalize market-leadership or competitive-superiority claims not explicitly supported by the packet.
    - Use `Pass`, `Partial`, or `Fail` for each criterion.

    {{ ctx.output_format }}
  "#
}
