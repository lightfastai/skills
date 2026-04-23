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
    - Do not copy forbidden-example terms from these rules or expected criteria into the brief just to name non-goals. Terms like token issuance, allowlists, registries, transport mechanics, and storage mechanics should appear only when the packet states them directly; otherwise use broader source-backed wording such as undocumented internals.
    - Preserve unresolved questions explicitly.
    - Preserve packet-named unresolved tensions when they affect scope, actor boundaries, approval boundaries, deployment shape, or operating model.
    - If the packet contains multiple materially distinct unresolved tensions, keep them distinct in `unresolved_questions` instead of collapsing them into one generic question.
    - If the raw notes contain explicit `Unresolved:` items, treat them as high-priority source facts. Preserve each materially distinct unresolved item in `unresolved_questions` unless two items are true duplicates.
    - If the packet contains multiple explicit `Unresolved:` bullets, the brief should usually preserve the same count of materially distinct unresolved questions unless two bullets are true duplicates.
    - Do not replace a packet-named open question with a narrower unsourced variant.
    - Do not invent a new unresolved question if it causes a packet-stated unresolved question to be dropped.
    - Avoid implementation detail.
    - Keep packet-named service surfaces distinct when they matter. For example, if the packet names teams separately from projects, do not silently collapse teams into projects.
    - If the packet names an ordered lineage, pipeline, or stage progression, preserve each materially distinct stage somewhere in the brief. Do not collapse named intermediate stages such as `brief` into a broader `draft` label unless the packet itself does so.
    - Use `lineage_stages` for packet-named ordered stages that materially shape the service, such as `raw request`, `packet`, `brief`, `draft`, `evaluation`, or `approval`. If the packet names such stages, preserve them there in source order.
    - Distinct source-visible surfaces do not automatically require distinct entities. Preserve the distinction in purpose, components, dependencies, or unresolved questions unless the packet clearly supports separate first-class records.
    - Use `actors` for source-backed participant roles that shape the service boundary, coordination model, or human escalation path. Human advocates, caregivers, reviewers, operators, patients, providers, and similar participants belong in `actors`.
    - Use `service_surfaces` for stable, source-backed coordination surfaces such as inboxes, queues, shared records, timelines, cases, or similar user-visible surfaces. If the packet implies one of these surfaces, preserve it there even if the wording is tentative.
    - `components` should describe major service responsibilities or user-visible service surfaces, not low-level classes, methods, SDKs, or protocols.
    - Component names should stay source-visible and behavior-oriented. Avoid internal-control names like `gate`, `control plane`, `status system`, or similar unless the packet explicitly uses that framing.
    - `abstraction_layers` should describe stable behavioral layers that make the service easier to reason about or port. Keep them service-level and conservative.
    - `external_dependencies` must name external systems, resources, or authorities explicitly visible in the packet. Do not list inferred internals such as token issuance, allowlists, registries, classes, transport mechanics, or storage engines unless they are stated directly.
    - When the packet describes an external dependency with uncertainty words such as `maybe`, `optional`, `if present`, or similar, preserve that dependency as conditional rather than turning it into an unconditional requirement.
    - Prefer systems, resources, and external services over actor roles in `external_dependencies`.
    - If the packet explicitly names a specific human authority as part of the external dependency boundary to keep the runtime honest, preserve that role as a qualified human dependency as well as an `actor`. This should be rare and should apply only to packet-explicit human review, advocate, or approval boundaries, not to general participant lists.
    - Do not list general participant roles such as family caregivers, patients, providers, reviewers, or approvers under `external_dependencies` just because they appear in the packet. Keep those in `actors`, boundaries, or escalation flows unless the packet explicitly frames a narrower human authority as part of the dependency boundary.
    - When the packet mentions approved clients, consent, or endpoint verification, keep that as a source-visible boundary or restriction. Do not turn it into an approval-state object, internal control process, or hidden eligibility system.
    - Keep approved-client wording as `approved clients` or `approved-client restrictions`. Do not paraphrase it as allowlists, client registration, registry management, eligibility status, or similar internal process language unless the packet states that mechanism.
    - `entities` should model only externally meaningful nouns the service manipulates or exposes. Do not create entities only to complete a plausible schema.
    - External resources that the service only retrieves, inspects, analyzes, or exposes through an access surface are not automatically service-owned entities. For example, projects, deployments, logs, docs, endpoint metadata, and client applications should stay in surfaces, components, dependencies, or open questions unless the packet clearly defines durable service-specific records for them.
    - If the packet supports no durable service-specific records, set `entities` to an empty list and explain the absence through components, dependencies, and unresolved questions instead of inventing placeholder entities.
    - Do not model clients, endpoints, documentation search results, approval lists, or ambiguous aliases as entities unless the packet clearly treats them as durable service records with stable fields and behavior.
    - When two labels may describe overlapping context, such as team versus workspace context, keep the ambiguity explicit instead of multiplying entities.
    - Do not add umbrella subject fields such as `subject`, `case_subject`, `party`, or similarly generalized placeholders when the packet already frames participants or care context more concretely. Prefer packet-backed wording or omit the field.
    - Every entity field must be directly supported by the packet or be the minimal identity/status field required to keep the entity coherent. Prefer fewer fields over speculative completeness.
    - When the packet describes a transition-state resource surface rather than a record-centric system, default to the sparsest viable entities. One minimal identifying field may be enough.
    - Do not infer relationship fields, lifecycle/status fields, or embedded collections such as `project_id`, `status`, or `logs` unless the packet clearly supports them.
    - Do not add audit-style fields such as `change_note`, `decided_at`, revision metadata, or extra timestamps solely because the packet mentions history or traceability. Keep history in components or prose unless the record field itself is source-backed.
    - Do not add revision-chain fields such as `revision`, `previous_*_id`, `parent_*_id`, or similar linkage solely because the packet mentions version history, revisions, or lineage. Keep revision history in components or prose unless the packet clearly makes that linkage a record-level concern.
    - Do not split a shared case, shared timeline, or shared record surface into entry-level entities such as `TimelineEntry`, `Event`, or `RecordItem` unless the packet clearly supports those entries as durable first-class records.
    - Most briefs should stay under roughly six entities unless the packet clearly supports richer modeling.
    - Prefer the smallest viable domain model. If an extra entity or field only restates behavior already captured elsewhere, omit it.
    - If the packet mentions broader `management` or `operations` language only as an unresolved transition, keep that wording in unresolved questions or narrowly qualified tension wording rather than turning it into a positive capability, component, goal, problem, boundary, or layer name.
    - When write scope is unresolved, avoid phrases like `project and deployment management` outside `unresolved_questions`; prefer neutral source-backed wording such as `project and deployment context`, `deployment inspection`, `retrieval`, `analysis`, or `later documentation wording`.
    - If the packet leaves reminders, outbound follow-up, missing-document requests, or similar communication behavior explicitly unresolved, keep that behavior in boundaries or unresolved questions rather than turning it into a standalone component, layer, or affirmative service capability.
    - If the packet emphasizes durable lineage, versioned history, approval trails, or recurring packet-to-review loops, make the service's long-running coordination role explicit in the brief rather than leaving persistence only implied.
    - When the packet supports it, use the exact phrase `long-running` in `purpose` or `update_request` instead of relying only on weaker proxies like `durable`, `ongoing`, or `history-aware`.
    - If the packet centers a stable coordination surface such as a shared case, timeline, inbox, queue, or record, make that surface explicit in the brief's purpose rather than leaving it only in components.
    - If the packet describes the service with tentative but source-backed coordination-surface language such as `feels like an inbox`, `shared record`, `queue`, or similar, preserve that surface or a close paraphrase in the brief instead of collapsing the service into pipeline-only wording.
    - When preserving a coordination surface such as an inbox, queue, or shared record, keep it visible in `service_surfaces` and in at least one other brief field such as `purpose`, `operational_problems`, `components`, or `abstraction_layers`.
    - If the packet names versioned history, a shared timeline, an approval trail, or similar trace surface as a recurring service surface, preserve at least one such surface in `service_surfaces` rather than reducing it to generic traceability wording.
    - When write scope is unresolved, do not describe project or deployment surfaces as supporting `actions`, broader `workflows`, or `possible management` behavior. Keep them framed as retrieval, inspection, analysis, source-visible context, or unresolved documentation language.
    - If a surface is explicitly ambiguous or alias-like, such as `team` versus `workspace context`, do not promote that ambiguity into a first-class entity unless the packet clearly establishes a durable record shape. Keep it in components, dependencies, or unresolved questions instead.
    - If approved-client scope is unresolved, ask source-visible questions such as whether the named client list is exhaustive or illustrative. Do not ask how approval is designated, maintained, or implemented unless the packet explicitly raises that process.
    - Use only logical field types such as `string`, `integer`, `boolean`, `timestamp`, `list of strings`, `map`, or `string or null`. Do not invent custom type labels like `duration`.
    - Do not embed `required`, `optional`, or invented constraints like `unique within service scope` into `type_expression`.
    - If a concept is visible in the packet but does not support a stable entity schema, keep it in components, dependencies, or unresolved questions instead of forcing it into the domain model.
    - Prefer omission over speculation.
    - If `existing_spec` is present and the request is a narrow update, treat the brief as a delta-oriented edit plan rather than a full regenerate-from-scratch brief.
    - In update mode, prefer the smallest possible change set. Keep `components`, `abstraction_layers`, `external_dependencies`, `entities`, and `unresolved_questions` limited to items the request explicitly adds, removes, or materially changes.
    - In update mode, the `SpecBrief` schema still requires a full-shape brief. Do not emit blank placeholders or empty required fields just because the requested edit is narrow.
    - In update mode, carry forward unchanged required fields from `existing_spec`, especially `service_name`, `purpose`, and any unchanged document-shaping lists needed to preserve the current document.
    - In update mode, treat `existing_spec` as the source of truth for unchanged wording and structure. Use the packet to identify requested edits, not to paraphrase unaffected text.
    - In update mode, do not fill in missing template sections from scratch just because the existing spec omits them. The update brief should respect the current document shape unless the request explicitly asks to expand it.
    - In update mode, do not restate or expand unchanged Purpose, Problem Statement, Goal, Non-Goal, component, dependency, or domain-model content just because you can infer a cleaner version.
    - In update mode, if an unchanged paragraph, bullet, or component description already exists in `existing_spec`, preserve that wording exactly instead of restating it from summary fields.
    - In update mode, do not make stylistic micro-edits to untouched text. Avoid synonym swaps, helper-word insertion, tense normalization, article changes, singular/plural cleanup, or punctuation-only rewriting unless the requested edit requires it.
    - In update mode, if the request asks for a new component, boundary bullet, or open-question section, do not automatically propagate that concept into Purpose, Problem Statement, Goals, Abstraction Levels, External Dependencies, or the domain model unless the request explicitly asks for those extra edits.
    - In update mode, if the request does not explicitly ask to revise `## 4. Core Domain Model`, keep the entity set unchanged. A newly added component, surface, boundary, or open question does not by itself justify a new entity or new fields.
    - In update mode, prefer expressing newly requested behavior in component text, boundary bullets, or unresolved questions before considering any domain-model edit.
    - In update mode, do not change enumerated counts such as `The service solves 5 operational problems:` unless the request explicitly asks to add or remove a problem bullet in that section.

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
    - In update mode, the create-mode template rules below do not authorize filling in missing sections, rewriting existing prose, or normalizing wording. They apply only where the update request explicitly touches that content.
    - In update mode, treat `existing_spec` as the canonical source for unchanged wording, numbering, bullet layout, and line breaks. Use the brief to identify requested edits and new content, not to paraphrase untouched text.
    - In update mode, if a surrounding paragraph, bullet, or component responsibility does not need to change, copy it exactly rather than regenerating a fresh paraphrase from the brief.
    - In update mode, do not make stylistic micro-edits to untouched text: no synonym swaps, pronoun insertion, helper words, tense normalization, singular/plural cleanup, or punctuation-only rewrites unless the requested edit requires them.
    - Follow the `spec-creator` template shape directly. Do not rename the core headings or collapse them into ad hoc labels.
    - Use exactly this opening shape:
      - `# <Service Name> Specification`
      - `Status: Draft v1 (language-agnostic)`
      - `Purpose: <one sentence>`
    - Require the `Purpose:` line to name the service kind, the protected endpoint or access boundary, and the main resource surfaces at the highest stable granularity the brief supports.
    - If the brief names surfaces like docs, teams, projects, deployments, or logs, mention them explicitly in the `Purpose:` line rather than replacing them with vague phrases like `operational context`.
    - If `service_surfaces` are present, mention at least one stable service surface from that list in the `Purpose:` line or opening Problem Statement paragraph.
    - If the brief centers a stable coordination surface such as a shared case, timeline, inbox, queue, or record, mention at least one such surface explicitly in the `Purpose:` line.
    - If the brief carries a tentative but source-backed coordination surface such as an inbox, queue, or shared record, keep that surface visible in the `Purpose:` line or opening Problem Statement paragraph rather than flattening it into pipeline-only language.
    - If the brief mentions OAuth, consent, approved clients, or secure access, the `Purpose:` line must explicitly say `OAuth-protected` or `secure, OAuth-protected` rather than leaving that security detail to later sections.
    - If the brief is fundamentally about coordination across named participant types, roles, or organizations, mention that cross-party coordination boundary in the `Purpose:` line instead of only naming artifacts or records.
    - If `actors` are present, use them to describe who coordination happens across.
    - Do not restate general participant actors as external dependencies just to make them visible. A role may appear in both places only when the brief explicitly preserves a packet-stated human authority dependency boundary.
    - If the brief names explicit ingress surfaces such as referrals, intake notes, source packets, or raw notes as core to the service, mention at least one of those entry surfaces in the `Purpose:` line instead of only describing downstream records or outputs.
    - Keep the `Purpose:` line concrete and source-bound. Avoid metaphorical or unsourced framing verbs like `protects`, `defends`, `guards`, or similar language unless the brief explicitly uses them.
    - If the brief emphasizes lineage, version history, recurring review loops, or approval trails, make the service's long-running coordination role explicit in the `Purpose:` line or opening Problem Statement paragraph instead of leaving it implicit.
    - When the brief supports it, prefer the exact phrase `long-running` in the `Purpose:` line or opening Problem Statement paragraph instead of leaving that property to inference.
    - If `service_surfaces` include versioned history, a timeline, or an approval trail, mention at least one such surface explicitly in the `Purpose:` line or opening Problem Statement paragraph instead of referring only to generic traceability or lineage.
    - When write scope is unresolved, prefer neutral words like `surface`, `context`, `retrieval`, `inspection`, or `analysis` over stronger nouns like `operations` or `management`.
    - If the brief includes source-backed but unresolved `management` wording, place the literal `management` phrase only in `## 5. Open Questions` or in explicitly qualified tension language. Do not use it in goals, problem bullets, boundaries, component names, or layer names.
    - Do not use `operation`, `operations`, or `management` in component or layer names when the brief leaves write scope unresolved.
    - Prefer `handling`, `coordination`, or `review` over workflow-forward labels like `routing`, `orchestration`, or `dispatch` unless the brief explicitly supports that language.
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
    - Write the heading `### 4.1 Entities` exactly before any entity definitions.
    - Never place `#### 4.1.x ...` headings directly under `## 4. Core Domain Model`; always emit `### 4.1 Entities` first, then any optional introductory sentence, then entity headings.
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
    - When a dependency is tentative in the packet or brief, keep that tentativeness visible with wording like `if present`, `when used`, or `if evaluations are external` rather than presenting the dependency as always required.
    - When evaluation is optional, qualified, or external in the brief, describe the service as coordinating evaluation runs or attaching evaluation results rather than claiming it always performs the evaluation itself.
    - Prefer systems and external services over actor roles in `### 3.3 External Dependencies`.
    - If the packet or brief explicitly frames a specific human authority as part of the external dependency boundary, keep that role in `### 3.3 External Dependencies` with qualified wording such as `human advocate review, when escalation is required`.
    - Do not list general participant roles such as family caregivers, patients, providers, reviewers, or approvers in `### 3.3 External Dependencies` just because the packet emphasizes a human boundary.
    - If `actors` are present, reflect them in the Problem Statement, Purpose, or component responsibilities instead of moving them wholesale into `### 3.3 External Dependencies`.
    - When a dependency is fundamentally about communicating with external parties, phrase the dependency as a communication channel, interface, or information source rather than as a bare list of counterparties.
    - If the brief mentions approved-client restrictions, keep that phrased as a boundary or restriction, not as an approval-state system or internal status object.
    - Keep packet-named surfaces visible when they materially matter. If the source packet names teams separately from projects, preserve that distinction somewhere in the spec instead of collapsing it away.
    - If `lineage_stages` are present, preserve every materially distinct stage from that list somewhere in the document. Mentioning the ordered stages in prose is acceptable even when not every stage becomes a domain entity.
    - If `service_surfaces` are present, keep at least one of those surfaces visible in the Purpose or System Overview so the service is not reduced to stage sequencing alone.
    - If `service_surfaces` include versioned history, a timeline, or an approval trail, keep at least one such history-bearing surface visible in the Purpose, Problem Statement, or System Overview rather than only generic `traceability` language.
    - If the brief names an ordered lineage or artifact pipeline, preserve every materially distinct stage somewhere in the document. If the packet or brief includes a stage like `brief` between packet and candidate artifact, keep that stage visible in the Problem Statement, System Overview, or another prose section even if it is not a domain entity.
    - Keep the domain model conservative:
      - include only entities materially supported by the brief
      - render every entity in `brief.entities` as its own `#### 4.1.x EntityName` heading with its own `Fields:` block; do not merge fields from one entity into another entity
      - preserve entity names from the brief exactly unless the name itself is malformed
      - prefer fewer entities over speculative completeness
      - use minimal source-backed fields
      - if a concept lacks enough support for a stable entity schema, keep it out of `## 4. Core Domain Model`
      - avoid second-order record types when a smaller set of entities or fields already makes the behavior legible
      - preserve packet-named distinctions somewhere in the document without forcing every named surface into the domain model
      - external resources that are only retrieved, inspected, analyzed, or exposed through an access surface are not service-owned entities; keep them in surfaces, components, dependencies, or open questions unless the brief defines durable service-specific records for them
      - if `brief.entities` is empty, render `### 4.1 Entities` followed by a short sentence explaining that the service does not define durable service-specific entities; do not invent entity headings to satisfy the template
      - do not model clients, endpoints, documentation search results, or unresolved aliases as entities unless the brief clearly treats them as durable first-class records
      - do not convert a separate packet-named surface into a nested field on another entity unless the brief clearly supports that nesting
      - when the brief is transitional on write scope, keep component and layer naming neutral rather than capability-forward
      - if broader `management` language appears only as unresolved packet wording, discuss it as a tension rather than naming a component or layer after it
      - if write scope is unresolved, do not describe project or deployment surfaces as supporting `actions`, broader `workflows`, or `possible management`; keep them framed as retrieval, inspection, analysis, or unresolved scope
      - if a surface is explicitly ambiguous or alias-like, such as `team` versus `workspace context`, keep it out of the domain model unless the brief clearly establishes it as a durable record
      - avoid component names like `gate` or dependency phrases like `client status` when the brief only supports externally visible access restrictions
      - keep entity count modest; more than roughly six entities should be rare and strongly justified by the brief
    - In field lines, use only logical types and source-backed constraints.
    - Do not put `required`, `optional`, `non-empty`, `unique`, or invented service-scope constraints inside the field parentheses.
    - If requirement state matters, express it in the indented semantic bullet rather than inside the type parentheses.
    - Preserve uncertainty where the source packet is in transition.
    - Avoid implementation detail.
    - If `unresolved_questions` are materially important, add `## 5. Open Questions` after the domain model and render them as markdown bullets.
    - When `unresolved_questions` are present, render every materially distinct item from the brief exactly once. Do not drop one for brevity or substitute only a subset.
    - When multiple unresolved questions are present, preserve the distinct tensions rather than reducing them to a single generic question.
    - Keep `## 5. Open Questions` source-bound. If the brief names a structural tension such as repo-native vs hosted, family-direct vs sponsored, or automation vs human ownership, carry that tension forward explicitly.
    - When the source packet includes explicit `Unresolved:` bullets, keep those questions source-traceable in `## 5. Open Questions` rather than substituting different questions.
    - When approved-client scope is uncertain, prefer questions about whether the named supported-client list is fixed, exhaustive, or illustrative. Do not ask how approval is internally designated or maintained unless the packet explicitly raises that process.
    - When write scope is unresolved, ask which specific mutations, if any, are supported. Do not describe the question itself in a way that implies broader actions are already established.
    - Optional extra sections are allowed only when the brief materially needs them; if used, place them after `## 4. Core Domain Model`.
    - Do not add end markers, appendix-only filler, or operational/program-management sections unless the brief explicitly requires them.
    - If `existing_spec` is present, treat this as update mode:
      - start from `existing_spec`
      - preserve all unchanged lines verbatim
      - apply only the edits implied by `update_request`
      - do not rewrite existing paragraphs, bullets, or component descriptions unless the request requires it
      - do not add new top-level sections, missing template subsections, empty scaffold headings, domain model content, dependencies, or other template-completion material unless `update_request` explicitly asks for them
      - preserve the existing section set exactly; if `existing_spec` lacks `### 3.2 Abstraction Levels`, `### 3.3 External Dependencies`, `## 4. Core Domain Model`, `## 5. Open Questions`, or any other template section, do not add that missing section unless `update_request` names that section or asks for that content explicitly
      - make the smallest textual diff that satisfies `update_request`
      - if `update_request` uses words like refresh, replace, or rewrite for a named section or subsection, treat that named section or subsection as replaceable
      - for a section or subsection refresh, keep the heading and neighboring sections unchanged, but replace that section body with the corresponding brief content
      - for a refreshed or replaced section, the old section body is not authoritative; do not copy old bullets or questions from `existing_spec` into the refreshed section unless the same bullet or question appears in the corresponding brief field
      - insertion is preferred only for add-only requests; do not preserve stale bullets inside a section that the request explicitly asks to refresh or replace
      - if `update_request` asks to refresh `### 2.2 Non-Goals`, render `brief.non_goals` as the complete new bullet list for that subsection and remove old non-goal bullets that are absent from `brief.non_goals`
      - if `update_request` asks to refresh `## 5. Open Questions`, render `brief.unresolved_questions` as the complete new bullet list for that section and remove old questions that are absent from `brief.unresolved_questions`
      - prefer insertion over rewrite; when adding a new bullet or component beside existing text, keep neighboring unchanged lines exactly as they appear in `existing_spec`
      - if `update_request` asks for a new bullet, component, boundary, or open question, insert only that material into the existing structure instead of regenerating neighboring paragraphs or adding unrelated template sections; this insertion rule does not apply to refresh, replace, or rewrite requests
      - if `update_request` does not ask to revise the Purpose line, Problem Statement bullets, existing component descriptions, dependencies, or domain-model entities, keep those lines unchanged
      - if `update_request` does not explicitly ask to revise `## 4. Core Domain Model`, preserve that entire section verbatim
      - a newly added component, surface, or open question does not authorize adding a new entity or new fields
      - if `update_request` asks for a new main component, add it only under `### 3.1 Main Components` unless the request explicitly asks for matching edits elsewhere
      - if `update_request` asks for `## 5. Open Questions`, append that section and keep earlier prose unchanged unless the request explicitly asks to revise earlier sections
      - do not update problem counts, goal counts, or other numeric summary lines unless the request explicitly changes the bullets they count

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
    - If `packet.existing_spec` is present, judge structural completeness relative to the requested update. Do not penalize sections or subsections that were already absent from `existing_spec` unless `task_prompt` or `expected_criteria` explicitly asks for those sections to be added.
    - In update mode, reward preserving the existing document shape when the task says to keep everything else as-is.
    - In update mode, penalize style-only paraphrases of untouched paragraphs, bullets, or component descriptions even when the meaning is still close.
    - In update mode, reward insertion-style edits that leave neighboring unchanged wording exactly or near-exactly intact.
    - In update mode, if the packet asks to refresh, replace, or rewrite a named section or subsection, verify that stale content from that section was removed rather than appended to. Do not mark the update as `Pass` when old bullets or questions remain verbatim inside the refreshed section.
    - In update mode, penalize new entity or field additions when the request does not explicitly ask to revise `## 4. Core Domain Model`.
    - Penalize collapsing packet-named surfaces away when they matter. For example, if the packet explicitly names teams separately from projects, omitting team/workspace context entirely should count against the candidate.
    - Penalize collapsing packet-named lineage or pipeline stages away when they matter. If the packet explicitly names `packet -> brief -> candidate artifact`, omitting the `brief` stage entirely should count against the candidate unless the stage is preserved elsewhere as a close paraphrase.
    - Penalize dropping packet-named unresolved tensions, or replacing them with narrower unsourced variants, when those tensions materially affect scope or behavior.
    - When the packet contains explicit `Unresolved:` bullets, treat omission of any materially distinct unresolved item as a real miss unless the candidate preserves it as a close paraphrase.
    - Penalize inferred internals such as token issuance, allowlists, registries, transport details, or storage choices unless the packet states them directly.
    - Penalize domain models that look schema-complete but are not source-backed.
    - Penalize flattening tentative packet dependencies into unconditional requirements when the packet uses softer wording such as `maybe`, `optional`, or `if present`.
    - Penalize listing general participant roles such as family caregivers, patients, providers, reviewers, or similar actors under external dependencies when the packet uses them to describe participants or escalation boundaries rather than dependency-like institutional authorities.
    - Reward keeping source-backed participant roles visible without treating them as infrastructure dependencies when the packet centers human coordination or escalation.
    - Do not penalize a qualified human dependency when the packet explicitly names a specific human authority, such as human advocate review, as part of the external dependency boundary.
    - Penalize Purpose lines that omit a packet-central stable coordination surface such as a shared case, timeline, inbox, queue, or record.
    - Penalize collapsing a packet-described inbox, queue, shared record, timeline, approval trail, or similar coordination surface into pipeline-only language when that surface materially shapes how the service is understood.
    - Penalize dependency wording that collapses a communication or information dependency into a bare list of external counterparties when the packet supports a clearer channel or source framing.
    - Penalize modeling access surfaces such as client applications, endpoint metadata, documentation search results, or ambiguous aliases as first-class entities unless the packet clearly treats them as durable records.
    - Do not treat preservation of packet-named surface distinctions as justification for forcing every named surface into the domain model.
    - Penalize relationship fields, lifecycle/status fields, or embedded collections that are plausible but not directly supported by the packet.
    - Penalize audit-heavy fields or record types that are justified only by general traceability language rather than directly supported packet facts.
    - Penalize revision-chain fields such as `revision`, `previous_*_id`, or `parent_*_id` when they are introduced only to express general history or lineage rather than a packet-backed record concern.
    - Penalize umbrella subject fields such as `subject`, `case_subject`, or `party` when they generalize away more concrete packet-backed participant or care-context framing.
    - Penalize splitting a shared case, shared timeline, or shared record surface into entry-level entities when the packet does not clearly establish entry records as first-class objects.
    - Penalize capability-forward wording like `operations` or `management behavior` when the packet leaves write scope explicitly unresolved.
    - Do not penalize source-backed `management` wording when it appears only inside an open question or explicitly qualified unresolved-tension sentence. Penalize it when it is used as an affirmative goal, capability, component name, layer name, or settled boundary.
    - Penalize standalone reminder, outbound follow-up, or missing-document components when the packet leaves that communication boundary explicitly unresolved.
    - Penalize component or abstraction-layer names that turn unresolved `management` language into affirmative service capability labels.
    - Penalize workflow-forward component labels like `routing`, `orchestration`, or `dispatch` when the packet only supports softer review, handling, or coordination language.
    - Penalize wording that presents project or deployment `actions`, broader `workflows`, or similar affirmative behavior when the packet only establishes retrieval/inspection surfaces plus unresolved broader language.
    - Penalize Purpose lines that omit explicit `OAuth-protected` or equivalent security wording when the packet clearly centers OAuth or secure access.
    - Penalize component, dependency, or open-question wording that turns approved-client restrictions into internal control-process speculation when the packet does not define that process.
    - Penalize promoting explicitly ambiguous surfaces, such as `team` versus `workspace context`, into first-class entities when the packet keeps them unsettled at the surface level.
    - Do not penalize typed field notation on its own; the template requires logical field types. Penalize only when the entity count or field coverage is materially more complete than the packet justifies.
    - Reward purpose lines that carry forward the core actor or coordination boundary when the packet makes that boundary central.
    - Penalize candidates that leave the long-running coordination role only implied when the packet strongly emphasizes lineage, history, approval trails, or repeated packet-to-review loops.
    - Reward making the service's long-running or durable coordination role explicit when the packet emphasizes lineage, history, approval trails, or repeated packet-to-review loops.
    - Reward conservative entity modeling and explicit `Open Questions` when the packet is genuinely transitional.
    - Use `Pass`, `Partial`, or `Fail` for each criterion.

    {{ ctx.output_format }}
  "#
}
