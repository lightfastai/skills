function CompileSpecBriefFromPacket(packet: SpecEvalPacket) -> SpecBrief {
  client EvalModel
  prompt #"
    {{ _.role("user") }}
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
    - Follow the `spec-creator` template and language guide rather than an ad hoc service summary.
    - Treat expected criteria as evaluation guidance, not as license to invent.
    - Preserve unresolved questions explicitly.
    - Preserve packet-named unresolved tensions when they affect scope, actor boundaries, approval gates, deployment shape, or operating model.
    - If the packet contains multiple materially distinct unresolved tensions, keep them distinct in `unresolved_questions` instead of collapsing them into one generic question.
    - If the raw notes contain explicit `Unresolved:` items, treat them as high-priority source facts. Preserve each materially distinct unresolved item in `unresolved_questions` unless two items are true duplicates.
    - Do not replace a packet-named open question with a narrower unsourced variant.
    - Do not invent a new unresolved question if it causes a packet-stated unresolved question to be dropped.
    - Avoid implementation detail.
    - Keep packet-named service surfaces distinct when they matter. For example, if the packet names teams separately from projects, do not silently collapse teams into projects.
    - `components` should describe major service responsibilities or user-visible service surfaces, not low-level classes, methods, SDKs, or protocols.
    - `abstraction_layers` should describe stable behavioral layers that make the service easier to reason about or port. Keep them service-level and conservative.
    - `external_dependencies` must name external systems, resources, or authorities explicitly visible in the packet. Do not list inferred internals such as token issuance, allowlists, registries, classes, transport mechanics, or storage engines unless they are stated directly.
    - `entities` should model only externally meaningful nouns the service manipulates or exposes. Do not create entities only to complete a plausible schema.
    - Every entity field must be directly supported by the packet or be the minimal identity/status field required to keep the entity coherent. Prefer fewer fields over speculative completeness.
    - Prefer the smallest viable domain model. If an extra entity or field only restates behavior already captured elsewhere, omit it.
    - Use only logical field types such as `string`, `integer`, `boolean`, `timestamp`, `list of strings`, `map`, or `string or null`. Do not invent custom type labels like `duration`.
    - Do not embed `required`, `optional`, or invented constraints like `unique within service scope` into `type_expression`.
    - If a concept is visible in the packet but does not support a stable entity schema, keep it in components, dependencies, or unresolved questions instead of forcing it into the domain model.
    - Prefer omission over speculation.

    {{ ctx.output_format }}
  "#
}

function RenderSpecDocumentDraft(brief: SpecBrief) -> string {
  client EvalModel
  prompt #"
    {{ _.role("user") }}
    Draft a `SPEC.md` from the brief below.

    Rules:
    - Output valid markdown.
    - Keep the document behavioral and language-agnostic.
    - If `existing_spec` is present, treat this as update mode and let the update-mode rules override the create-mode template-completion rules below.
    - Follow the `spec-creator` template shape directly. Do not rename the core headings or collapse them into ad hoc labels.
    - Use exactly this opening shape:
      - `# <Service Name> Specification`
      - `Status: Draft v1 (language-agnostic)`
      - `Purpose: <one sentence>`
    - Require the `Purpose:` line to name the service kind, the protected endpoint or access boundary, and the main resource surfaces at the highest stable granularity the brief supports.
    - If the brief names surfaces like docs, teams, projects, deployments, or logs, mention them explicitly in the `Purpose:` line rather than replacing them with vague phrases like `operational context`.
    - If the brief is fundamentally about coordination across named participant types, roles, or organizations, mention that cross-party coordination boundary in the `Purpose:` line instead of only naming artifacts or records.
    - If the brief names explicit ingress surfaces such as referrals, intake notes, source packets, or raw notes as core to the service, mention at least one of those entry surfaces in the `Purpose:` line instead of only describing downstream records or outputs.
    - Keep the `Purpose:` line concrete and source-bound. Avoid metaphorical or unsourced framing verbs like `protects`, `defends`, `guards`, or similar language unless the brief explicitly uses them.
    - Include these sections in order:
      - `## 1. Problem Statement`
      - `## 2. Goals and Non-Goals`
      - `### 2.1 Goals`
      - `### 2.2 Non-Goals`
      - `## 3. System Overview`
      - `### 3.1 Main Components`
      - `### 3.2 Abstraction Levels`
      - `### 3.3 External Dependencies`
      - `## 4. Core Domain Model`
      - `### 4.1 Entities`
    - In `## 1. Problem Statement`, write:
      - one opening paragraph describing the service at a high level
      - a line like `The service solves <N> operational problems:`
      - a bullet list of concrete operational problems
    - Keep `Important boundary:` as a standalone labeled block inside `## 1. Problem Statement`, followed by bullets. Do not turn it into a standalone section.
    - Use a numbered list for `### 3.1 Main Components` in the form `1. `Component Name`` followed by indented responsibility bullets.
    - Use a numbered list for `### 3.2 Abstraction Levels` in the form `1. `Layer Name`` followed by indented responsibility bullets.
    - For entities, use `#### 4.1.x EntityName`, then `Fields:`, then field lines in the form `- `field_name` (type, constraints)` with indented semantic bullets and optional `Default: `value`` lines.
    - Use logical field types (`string`, `integer`, `boolean`, `timestamp`, `list of strings`, `map`, `string or null`), not implementation types.
    - List external dependencies as systems or services, not low-level API method names, SDK calls, token mechanics, registry internals, classes, or internal implementation choices.
    - Keep packet-named surfaces visible when they materially matter. If the source packet names teams separately from projects, preserve that distinction somewhere in the spec instead of collapsing it away.
    - Keep the domain model conservative:
      - include only entities materially supported by the brief
      - prefer fewer entities over speculative completeness
      - use minimal source-backed fields
      - if a concept lacks enough support for a stable entity schema, keep it out of `## 4. Core Domain Model`
      - avoid second-order record types when a smaller set of entities or fields already makes the behavior legible
    - In field lines, use only logical types and source-backed constraints.
    - Do not put `required`, `optional`, `non-empty`, `unique`, or invented service-scope constraints inside the field parentheses.
    - If requirement state matters, express it in the indented semantic bullet rather than inside the type parentheses.
    - Preserve uncertainty where the source packet is in transition.
    - Avoid implementation detail.
    - If `unresolved_questions` are materially important, add `## 5. Open Questions` after the domain model and render them as markdown bullets.
    - When multiple unresolved questions are present, preserve the distinct tensions rather than reducing them to a single generic question.
    - Keep `## 5. Open Questions` source-bound. If the brief names a structural tension such as repo-native vs hosted, family-direct vs sponsored, or automation vs human ownership, carry that tension forward explicitly.
    - When the source packet includes explicit `Unresolved:` bullets, keep those questions source-traceable in `## 5. Open Questions` rather than substituting different questions.
    - Optional extra sections are allowed only when the brief materially needs them; if used, place them after `## 4. Core Domain Model`.
    - Do not add end markers, appendix-only filler, or operational/program-management sections unless the brief explicitly requires them.
    - If `existing_spec` is present, treat this as update mode:
      - start from `existing_spec`
      - preserve all unchanged lines verbatim
      - apply only the edits implied by `update_request`
      - do not rewrite existing paragraphs, bullets, or component descriptions unless the request requires it
      - do not add new top-level sections, domain model content, dependencies, or other template-completion material unless `update_request` explicitly asks for them

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
    {{ _.role("user") }}
    Evaluate the candidate `SPEC.md` against the evaluation packet.

    Packet:
    {{ packet|format(type="yaml") }}

    Candidate document:
    {{ candidate_document }}

    Rules:
    - Grade against the expected criteria explicitly.
    - Penalize invented capabilities, invented certainty, or implementation leakage.
    - Reward correct scope boundaries and careful handling of transition states.
    - Penalize missing core template sections, missing `### 3.2 Abstraction Levels`, missing `### 3.3 External Dependencies`, malformed field formatting, or moving `Important boundary:` out of the Problem Statement block.
    - Penalize collapsing packet-named surfaces away when they matter. For example, if the packet explicitly names teams separately from projects, omitting team/workspace context entirely should count against the candidate.
    - Penalize dropping packet-named unresolved tensions, or replacing them with narrower unsourced variants, when those tensions materially affect scope or behavior.
    - When the packet contains explicit `Unresolved:` bullets, treat omission of any materially distinct unresolved item as a real miss unless the candidate preserves it as a close paraphrase.
    - Penalize inferred internals such as token issuance, allowlists, registries, transport details, or storage choices unless the packet states them directly.
    - Penalize domain models that look schema-complete but are not source-backed.
    - Do not penalize typed field notation on its own; the template requires logical field types. Penalize only when the entity count or field coverage is materially more complete than the packet justifies.
    - Reward purpose lines that carry forward the core actor or coordination boundary when the packet makes that boundary central.
    - Reward conservative entity modeling and explicit `Open Questions` when the packet is genuinely transitional.
    - Use `Pass`, `Partial`, or `Fail` for each criterion.

    {{ ctx.output_format }}
  "#
}
