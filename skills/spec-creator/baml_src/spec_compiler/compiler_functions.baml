function ExtractClaims(raw_notes: string) -> Claim[] {
  client EvalModel
  prompt #"
    {{ _.role("user") }}
    Extract atomic claims from the raw notes below.

    Rules:
    - Preserve the original intent.
    - Split compound statements into separate claims when useful.
    - Use `Fact` only for concrete statements in the notes.
    - Use `Thesis` for directional beliefs that still affect scope.
    - Use `Boundary` for explicit scope limits or exclusions.
    - Use `Constraint` for hard operating requirements.
    - Use `OpenQuestion` when the note is unresolved.
    - Keep `sources` short and human-readable.
    - Preserve packet-named capabilities separately when the notes distinguish them, such as docs, teams, projects, deployments, and logs.
    - Do not infer internal implementation, storage, transport, token, registry, allowlist, or SDK detail unless the notes say it directly.
    - Prefer omission over speculative completion.

    Raw notes:
    {{ raw_notes }}

    {{ ctx.output_format }}
  "#
}

function CompileSpecBrief(raw_notes: string, existing_spec: string?) -> SpecBrief {
  client EvalModel
  prompt #"
    {{ _.role("user") }}
    Compile a spec brief from the inputs below.

    Rules:
    - Produce a behavioral brief suitable for `spec-creator`.
    - Follow the `spec-creator` contract rather than ad hoc document structure.
    - Prefer service-level behavior over product doctrine.
    - Do not copy forbidden-example terms from these rules into the brief just to name non-goals. Terms like token issuance, allowlists, registries, transport mechanics, and storage mechanics should appear only when the notes state them directly; otherwise use broader source-backed wording such as undocumented internals.
    - Preserve unresolved questions explicitly.
    - Preserve packet-named unresolved tensions when they affect scope, actor boundaries, approval boundaries, deployment shape, or operating model.
    - If the notes contain multiple materially distinct unresolved tensions, keep them distinct in `unresolved_questions` instead of collapsing them into one generic question.
    - If the notes contain explicit `Unresolved:` items, treat them as high-priority source facts. Preserve each materially distinct unresolved item in `unresolved_questions` unless two items are true duplicates.
    - If the notes contain multiple explicit `Unresolved:` bullets, the brief should usually preserve the same count of materially distinct unresolved questions unless two bullets are true duplicates.
    - Do not replace a packet-named open question with a narrower unsourced variant.
    - Do not invent a new unresolved question if it causes a packet-stated unresolved question to be dropped.
    - Do not invent implementation detail.
    - Keep packet-named service surfaces distinct when they matter. For example, if the notes name teams separately from projects, do not silently collapse teams into projects.
    - If the notes name an ordered lineage, pipeline, or stage progression, preserve each materially distinct stage somewhere in the brief. Do not collapse named intermediate stages such as `brief` into a broader `draft` label unless the notes themselves do so.
    - Use `lineage_stages` for packet-named ordered stages that materially shape the service, such as `raw request`, `packet`, `brief`, `draft`, `evaluation`, or `approval`. If the notes name such stages, preserve them there in source order.
    - Distinct source-visible surfaces do not automatically require distinct entities. Preserve the distinction in purpose, components, dependencies, or unresolved questions unless the notes clearly support separate first-class records.
    - Use `actors` for source-backed participant roles that shape the service boundary, coordination model, or human escalation path. Human advocates, caregivers, reviewers, operators, patients, providers, and similar participants belong in `actors`.
    - Use `service_surfaces` for stable, source-backed coordination surfaces such as inboxes, queues, shared records, timelines, cases, or similar user-visible surfaces. If the notes imply one of these surfaces, preserve it there even if the wording is tentative.
    - `components` should describe major service responsibilities or user-visible service surfaces, not low-level classes, methods, SDKs, or protocols.
    - Component names should stay source-visible and behavior-oriented. Avoid internal-control names like `gate`, `control plane`, `status system`, or similar unless the notes explicitly use that framing.
    - `abstraction_layers` should describe stable behavioral layers that make the service easier to reason about or port. Keep them service-level and conservative.
    - `external_dependencies` must name external systems, resources, or authorities explicitly visible in the notes. Do not list inferred internals such as token issuance, allowlists, registries, classes, transport mechanics, or storage engines unless they are stated directly.
    - When the notes describe an external dependency with uncertainty words such as `maybe`, `optional`, `if present`, or similar, preserve that dependency as conditional rather than turning it into an unconditional requirement.
    - Prefer systems, resources, and external services over actor roles in `external_dependencies`.
    - If the notes explicitly name a specific human authority as part of the external dependency boundary to keep the runtime honest, preserve that role as a qualified human dependency as well as an `actor`. This should be rare and should apply only to packet-explicit human review, advocate, or approval boundaries, not to general participant lists.
    - Do not list general participant roles such as family caregivers, patients, providers, reviewers, or approvers under `external_dependencies` just because they appear in the packet. Keep those in `actors`, boundaries, or escalation flows unless the packet explicitly frames a narrower human authority as part of the dependency boundary.
    - Do not list reviewers or approvers in `external_dependencies` merely because the service has a human review gate. Keep them as actors or boundary language unless the notes explicitly define an external review authority or external review service.
    - When the notes mention approved clients, consent, or endpoint verification, keep that as a source-visible boundary or restriction. Do not turn it into an approval-state object, internal control process, or hidden eligibility system.
    - Keep approved-client wording as `approved clients` or `approved-client restrictions`. Do not paraphrase it as allowlists, client registration, registry management, eligibility status, or similar internal process language unless the notes state that mechanism.
    - `entities` should model only externally meaningful nouns the service manipulates or exposes. Do not create entities only to complete a plausible schema.
    - External resources that the service only retrieves, inspects, analyzes, or exposes through an access surface are not automatically service-owned entities. For example, projects, deployments, logs, docs, endpoint metadata, and client applications should stay in surfaces, components, dependencies, or open questions unless the notes clearly define durable service-specific records for them.
    - If the notes support no durable service-specific records, set `entities` to an empty list and explain the absence through components, dependencies, and unresolved questions instead of inventing placeholder entities.
    - Do not model clients, endpoints, documentation search results, approval lists, or ambiguous aliases as entities unless the notes clearly treat them as durable service records with stable fields and behavior.
    - When two labels may describe overlapping context, such as team versus workspace context, keep the ambiguity explicit instead of multiplying entities.
    - Do not add umbrella subject fields such as `subject`, `case_subject`, `party`, or similarly generalized placeholders when the notes already frame participants or care context more concretely. Prefer packet-backed wording or omit the field.
    - Every entity field must be directly supported by the notes or be the minimal identity/status field required to keep the entity coherent. Prefer fewer fields over speculative completeness.
    - If the notes mention lightweight status states while warning against full workflow or BPM modeling, do not add generic `status` fields to entities unless the status values are directly source-backed and essential to the record.
    - When the notes describe a transition-state resource surface rather than a record-centric system, default to the sparsest viable entities. One minimal identifying field may be enough.
    - Do not infer relationship fields, lifecycle/status fields, or embedded collections such as `project_id`, `status`, or `logs` unless the notes clearly support them.
    - Do not add audit-style fields such as `change_note`, `decided_at`, revision metadata, or extra timestamps solely because the notes mention history or traceability. Keep history in components or prose unless the record field itself is source-backed.
    - Do not add revision-chain fields such as `revision`, `previous_*_id`, `parent_*_id`, or similar linkage solely because the notes mention version history, revisions, or lineage. Keep revision history in components or prose unless the notes clearly make that linkage a record-level concern.
    - Do not split a shared case, shared timeline, or shared record surface into entry-level entities such as `TimelineEntry`, `Event`, or `RecordItem` unless the notes clearly support those entries as durable first-class records.
    - Most briefs should stay under roughly six entities unless the notes clearly support richer modeling.
    - Prefer the smallest viable domain model. If an extra entity or field only restates behavior already captured elsewhere, omit it.
    - If the notes mention broader `management` or `operations` language only as an unresolved transition, keep that wording in unresolved questions or narrowly qualified tension wording rather than turning it into a positive capability, component, goal, problem, boundary, or layer name.
    - When write scope is unresolved, avoid phrases like `project and deployment management` outside `unresolved_questions`; prefer neutral source-backed wording such as `project and deployment context`, `deployment inspection`, `retrieval`, `analysis`, or `later documentation wording`.
    - If the notes leave reminders, outbound follow-up, missing-document requests, or similar communication behavior explicitly unresolved, keep that behavior in boundaries or unresolved questions rather than turning it into a standalone component, layer, or affirmative service capability.
    - If the notes emphasize durable lineage, versioned history, approval trails, or recurring packet-to-review loops, make the service's long-running coordination role explicit in the brief rather than leaving persistence only implied.
    - When the notes support it, use the exact phrase `long-running` in `purpose` or `update_request` instead of relying only on weaker proxies like `durable`, `ongoing`, or `history-aware`.
    - If the notes center a stable coordination surface such as a shared case, timeline, inbox, queue, or record, make that surface explicit in the brief's purpose rather than leaving it only in components.
    - If the notes describe the service with tentative but source-backed coordination-surface language such as `feels like an inbox`, `shared record`, `queue`, or similar, preserve that surface or a close paraphrase in the brief instead of collapsing the service into pipeline-only wording.
    - When preserving a coordination surface such as an inbox, queue, or shared record, keep it visible in `service_surfaces` and in at least one other brief field such as `purpose`, `operational_problems`, `components`, or `abstraction_layers`.
    - If the notes name versioned history, a shared timeline, an approval trail, or similar trace surface as a recurring service surface, preserve at least one such surface in `service_surfaces` rather than reducing it to generic traceability wording.
    - When write scope is unresolved, do not describe project or deployment surfaces as supporting `actions`, broader `workflows`, or `possible management` behavior. Keep them framed as retrieval, inspection, analysis, source-visible context, or unresolved documentation language.
    - If a surface is explicitly ambiguous or alias-like, such as `team` versus `workspace context`, do not promote that ambiguity into a first-class entity unless the notes clearly establish a durable record shape. Keep it in components, dependencies, or unresolved questions instead.
    - If approved-client scope is unresolved, ask source-visible questions such as whether the named client list is exhaustive or illustrative. Do not ask how approval is designated, maintained, or implemented unless the notes explicitly raise that process.
    - Use only logical field types such as `string`, `integer`, `boolean`, `timestamp`, `list of strings`, `map`, or `string or null`. Do not invent custom type labels like `duration`.
    - Do not embed `required`, `optional`, or invented constraints like `unique within service scope` into `type_expression`.
    - If a concept is visible in the notes but does not support a stable entity schema, keep it in components, dependencies, or unresolved questions instead of forcing it into the domain model.
    - If `existing_spec` is present, preserve compatible intent and only sharpen gaps.
    - If `existing_spec` is present and the request is a narrow update, treat the brief as a delta-oriented edit plan rather than a full regenerate-from-scratch brief.
    - In update mode, prefer the smallest possible change set. Keep `components`, `abstraction_layers`, `external_dependencies`, `entities`, and `unresolved_questions` limited to items the request explicitly adds, removes, or materially changes.
    - In update mode, the `SpecBrief` schema still requires a full-shape brief. Do not emit blank placeholders or empty required fields just because the requested edit is narrow.
    - In update mode, carry forward unchanged required fields from `existing_spec`, especially `service_name`, `purpose`, and any unchanged document-shaping lists needed to preserve the current document.
    - In update mode, treat `existing_spec` as the source of truth for unchanged wording and structure. Use the notes to identify requested edits, not to paraphrase unaffected text.
    - In update mode, do not fill in missing template sections from scratch just because the existing spec omits them. The update brief should respect the current document shape unless the request explicitly asks to expand it.
    - In update mode, do not restate or expand unchanged Purpose, Problem Statement, Goal, Non-Goal, component, dependency, or domain-model content just because you can infer a cleaner version.
    - In update mode, if an unchanged paragraph, bullet, or component description already exists in `existing_spec`, preserve that wording exactly instead of restating it from summary fields.
    - In update mode, do not make stylistic micro-edits to untouched text. Avoid synonym swaps, helper-word insertion, tense normalization, article changes, singular/plural cleanup, or punctuation-only rewriting unless the requested edit requires it.
    - In update mode, if the request asks for a new component, boundary bullet, or open-question section, do not automatically propagate that concept into Purpose, Problem Statement, Goals, Abstraction Levels, External Dependencies, or the domain model unless the request explicitly asks for those extra edits.
    - In update mode, if the request does not explicitly ask to revise `## 4. Core Domain Model`, keep the entity set unchanged. A newly added component, surface, boundary, or open question does not by itself justify a new entity or new fields.
    - In update mode, prefer expressing newly requested behavior in component text, boundary bullets, or unresolved questions before considering any domain-model edit.
    - In update mode, do not change enumerated counts such as `The service solves 5 operational problems:` unless the request explicitly asks to add or remove a problem bullet in that section.
    - Prefer omission over speculation.

    Raw notes:
    {{ raw_notes }}

    Existing spec:
    {{ existing_spec }}

    {{ ctx.output_format }}
  "#
}

function CritiqueSpecBrief(brief: SpecBrief) -> SpecCritique {
  client EvalModel
  prompt #"
    {{ _.role("user") }}
    Critique the spec brief below.

    Rules:
    - Flag contradictions across goals, non-goals, and boundaries.
    - Flag implementation leakage.
    - Flag ambiguous terms that weaken a behavioral specification.
    - Flag missing sections implied by the current brief.
    - Flag missing packet-named surfaces that were collapsed away, such as teams being buried inside projects.
    - Flag named lineage or pipeline stages that disappeared from the brief, such as a `brief` stage being collapsed into a generic draft.
    - Flag abstraction layers that drift into low-level implementation or internal class design.
    - Flag dependencies that name inferred internals rather than source-visible external systems.
    - Flag human participant roles that were stuffed into `external_dependencies` instead of `actors`, except where the brief preserves a packet-explicit human authority boundary as a qualified dependency.
    - Flag missing `service_surfaces` or `lineage_stages` when the brief otherwise flattens important packet-described coordination surfaces or ordered stages into generic pipeline language.
    - Flag entity/field modeling that looks like speculative schema completion rather than source-backed service behavior.
    - Flag unresolved questions that were present in the source packet but were not preserved distinctly in the brief.

    Brief:
    {{ brief|format(type="yaml") }}

    {{ ctx.output_format }}
  "#
}

function RenderSpecCreatorPrompt(brief: SpecBrief) -> string {
  client EvalModel
  prompt #"
    {{ _.role("user") }}
    Render a prompt for the `spec-creator` skill using the brief below.

    Rules:
    - Ask for a top-level `SPEC.md`.
    - Keep the output language-agnostic and behavioral.
    - Preserve unresolved questions instead of inventing decisions.
    - If the brief includes `existing_spec`, treat the task as update mode and preserve the existing document verbatim except for the requested edits.
    - In update mode, the create-mode template rules below do not authorize filling in missing sections, rewriting existing prose, or normalizing wording. They apply only where the update request explicitly touches that content.
    - In update mode, treat `existing_spec` as the canonical source for unchanged wording, numbering, bullet layout, and line breaks. Use the brief to identify requested edits and new content, not to paraphrase untouched text.
    - In update mode, if a surrounding paragraph, bullet, or component responsibility does not need to change, copy it exactly rather than regenerating a fresh paraphrase from the brief.
    - In update mode, do not make stylistic micro-edits to untouched text: no synonym swaps, pronoun insertion, helper words, tense normalization, singular/plural cleanup, or punctuation-only rewrites unless the requested edit requires them.
    - Treat `references/template.md` and `references/language.md` as the contract.
    - Require the canonical `spec-creator` section shape:
      - `# <Service Name> Specification`
      - `Status: Draft v1 (language-agnostic)`
      - `Purpose: <one sentence>`
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
    - Require the exact heading `### 4.1 Entities` to appear before any entity definitions.
    - Never place `#### 4.1.x ...` headings directly under `## 4. Core Domain Model`; always emit `### 4.1 Entities` first, then any optional introductory sentence, then entity headings.
    - Require `## 1. Problem Statement` to contain:
      - one opening paragraph
      - a line like `The service solves <N> operational problems:`
      - a bullet list of explicit operational problems
    - If `brief.purpose` is already source-bound and concrete, use it as the `Purpose:` line with only minor grammar trimming. Do not introduce new concepts while rewriting it.
    - Require the `Purpose:` line to name the service kind and main source-backed ingress, resource, or coordination surfaces at the highest stable granularity the brief supports.
    - Name a protected endpoint, security boundary, or access boundary in the `Purpose:` line only when the brief explicitly supports one.
    - If the brief names surfaces like docs, teams, projects, deployments, or logs, mention them explicitly in the `Purpose:` line rather than replacing them with vague phrases like `operational context`.
    - If `service_surfaces` are present, mention at least one stable service surface from that list in the `Purpose:` line or opening Problem Statement paragraph.
    - If the brief centers a stable coordination surface such as a shared case, timeline, inbox, queue, or record, mention at least one such surface explicitly in the `Purpose:` line.
    - If the brief carries a tentative but source-backed coordination surface such as an inbox, queue, or shared record, keep that surface visible in the `Purpose:` line or opening Problem Statement paragraph rather than flattening it into pipeline-only language.
    - If the brief mentions OAuth, consent, approved clients, endpoint verification, or secure access, the `Purpose:` line must explicitly say `OAuth-protected` or `secure, OAuth-protected` rather than leaving that security detail to later sections.
    - Do not add `secure`, `secure access`, `protected`, or `OAuth-protected` to the `Purpose:` line unless the brief explicitly mentions OAuth, consent, approved clients, endpoint verification, or secure access.
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
    - Require `Important boundary:` as a standalone labeled block inside the Problem Statement, followed by boundary bullets.
    - Require numbered components and template-shaped field lines: `- `field_name` (type, constraints)`.
    - Require `### 3.2 Abstraction Levels` to explain stable behavioral layers rather than runtime call order or internal code structure.
    - Require external dependencies to stay at the system/service level rather than naming low-level API methods, SDK calls, token mechanics, registry internals, classes, or storage implementation.
    - When a dependency is tentative in the brief, keep that tentativeness visible with wording like `if present`, `when used`, or `if evaluations are external` rather than presenting the dependency as always required.
    - When evaluation is optional, qualified, or external in the brief, describe the service as coordinating evaluation runs or attaching evaluation results rather than claiming it always performs the evaluation itself.
    - Prefer systems and external services over actor roles in `### 3.3 External Dependencies`.
    - If the brief explicitly frames a specific human authority as part of the external dependency boundary, keep that role in `### 3.3 External Dependencies` with qualified wording such as `human advocate review, when escalation is required`.
    - Do not list general participant roles such as family caregivers, patients, providers, reviewers, or approvers in `### 3.3 External Dependencies` just because the brief emphasizes a human boundary.
    - Do not list reviewers or approvers in `### 3.3 External Dependencies` merely because the service has a human review gate. Keep them visible in actors, boundaries, or review components unless the brief explicitly defines an external review authority or external review service.
    - If `actors` are present, reflect them in the Problem Statement, Purpose, or component responsibilities instead of moving them wholesale into `### 3.3 External Dependencies`.
    - When a dependency is fundamentally about communicating with external parties, phrase the dependency as a communication channel, interface, or information source rather than as a bare list of counterparties.
    - If the brief mentions approved-client restrictions, keep that phrased as a boundary or restriction, not as an approval-state system or internal status object.
    - Require packet-named surfaces to remain visible when they materially matter. For example, if the brief distinguishes teams from projects, keep that distinction somewhere in the spec instead of collapsing it away.
    - If `lineage_stages` are present, preserve every materially distinct stage from that list somewhere in the document. Mentioning the ordered stages in prose is acceptable even when not every stage becomes a domain entity.
    - If `service_surfaces` are present, keep at least one of those surfaces visible in the Purpose or System Overview so the service is not reduced to stage sequencing alone.
    - If `service_surfaces` include versioned history, a timeline, or an approval trail, keep at least one such history-bearing surface visible in the Purpose, Problem Statement, or System Overview rather than only generic `traceability` language.
    - If the brief names an ordered lineage or artifact pipeline, preserve every materially distinct stage somewhere in the document. If the brief includes a stage like `brief` between packet and candidate artifact, keep that stage visible in the Problem Statement, System Overview, or another prose section even if it is not a domain entity.
    - Require the domain model to stay conservative:
      - include only entities materially supported by the brief
      - render every entity in `brief.entities` as its own `#### 4.1.x EntityName` heading with its own `Fields:` block; do not merge fields from one entity into another entity
      - preserve entity names from the brief exactly unless the name itself is malformed
      - prefer fewer entities over speculative completeness
      - use minimal source-backed fields
      - if a concept lacks enough support for a stable entity schema, keep it out of `## 4. Core Domain Model`
      - avoid second-order record types when a smaller set of entities or fields already makes the behavior legible
      - preserve packet-named distinctions somewhere in the spec without forcing every named surface into the domain model
      - external resources that are only retrieved, inspected, analyzed, or exposed through an access surface are not service-owned entities; keep them in surfaces, components, dependencies, or open questions unless the brief defines durable service-specific records for them
      - if `brief.entities` is empty, render `### 4.1 Entities` followed by a short sentence explaining that the service does not define durable service-specific entities; do not invent entity headings to satisfy the template
      - do not model clients, endpoints, documentation search results, or unresolved aliases as entities unless the brief clearly treats them as durable first-class records
      - do not convert a separate packet-named surface into a nested field on another entity unless the brief clearly supports that nesting
      - do not add umbrella subject fields such as `subject`, `case_subject`, or `party` when the brief does not clearly require them
      - when the brief is transitional on write scope, keep component and layer naming neutral rather than capability-forward
      - if broader `management` language appears only as unresolved packet wording, discuss it as a tension rather than naming a component or layer after it
      - if reminders, outbound follow-up, or missing-document requests are explicitly unresolved, do not model them as standalone components, layers, or capabilities
      - if write scope is unresolved, do not describe project or deployment surfaces as supporting `actions`, broader `workflows`, or `possible management`; keep them framed as retrieval, inspection, analysis, or unresolved scope
      - if a surface is explicitly ambiguous or alias-like, such as `team` versus `workspace context`, keep it out of the domain model unless the brief clearly establishes it as a durable record
      - avoid component names like `gate` or dependency phrases like `client status` when the brief only supports externally visible access restrictions
      - do not add revision-chain fields such as `revision`, `previous_*_id`, or `parent_*_id` solely to express history or traceability when the brief does not make that linkage record-level
      - do not split a shared case, shared timeline, or shared record surface into entry-level entities unless the brief clearly makes those entries first-class durable records
      - keep entity count modest; more than roughly six entities should be rare and strongly justified by the brief
      - if the brief names a shared case timeline or shared record surface without explicit entry records, do not create `TimelineEntry`, `Event`, or similar entry entities just to make the timeline concrete
    - In field lines, use only logical types and source-backed constraints.
    - Do not add generic `status` fields just because a brief or packet mentions lightweight state. Include status fields only when the source makes status values essential and not merely a warning against over-modeling workflow state.
    - Do not put `required`, `optional`, `non-empty`, `unique`, or invented service-scope constraints inside the field parentheses.
    - If requirement state matters, express it in the indented semantic bullet rather than inside the type parentheses.
    - If `unresolved_questions` is non-empty, add `## 5. Open Questions` after the domain model and render every question as a markdown bullet.
    - When `unresolved_questions` are present, render every materially distinct item from the brief exactly once. Do not drop one for brevity, substitute only a subset, or move the questions only into boundary prose.
    - When multiple unresolved questions are present, preserve the distinct tensions rather than reducing them to a single generic question.
    - Keep `## 5. Open Questions` source-bound. If the brief names a structural tension such as repo-native vs hosted, family-direct vs sponsored, or automation vs human ownership, carry that tension forward explicitly.
    - When the source notes include explicit `Unresolved:` bullets, keep those questions source-traceable in `## 5. Open Questions` rather than substituting different questions.
    - When approved-client scope is uncertain, prefer questions about whether the named supported-client list is fixed, exhaustive, or illustrative. Do not ask how approval is internally designated or maintained unless the brief explicitly raises that process.
    - When write scope is unresolved, ask which specific mutations, if any, are supported. Do not describe the question itself in a way that implies broader actions are already established.
    - In update mode, do not add new top-level sections, missing template subsections, empty scaffold headings, or template-completion material unless the request explicitly asks for them.
    - In update mode, preserve the existing section set exactly. If `existing_spec` lacks `### 3.2 Abstraction Levels`, `### 3.3 External Dependencies`, `## 4. Core Domain Model`, `## 5. Open Questions`, or any other template section, do not add that missing section unless `update_request` names that section or asks for that content explicitly.
    - In update mode, make the smallest textual diff that satisfies `update_request`.
    - In update mode, if `update_request` uses words like refresh, replace, or rewrite for a named section or subsection, treat that named section or subsection as replaceable. Keep its heading and neighboring sections unchanged, but replace the section body with the corresponding brief content.
    - For a refreshed or replaced section, the old section body is not authoritative. Do not copy old bullets or questions from `existing_spec` into the refreshed section unless the same bullet or question appears in the corresponding brief field.
    - In update mode, insertion is preferred only for add-only requests. Do not preserve stale bullets inside a section that the request explicitly asks to refresh or replace.
    - If `update_request` asks to refresh `### 2.2 Non-Goals`, render `brief.non_goals` as the complete new bullet list for that subsection and remove old non-goal bullets that are absent from `brief.non_goals`.
    - If `update_request` asks to refresh `## 5. Open Questions`, render `brief.unresolved_questions` as the complete new bullet list for that section and remove old questions that are absent from `brief.unresolved_questions`.
    - In update mode, prefer insertion over rewrite. When adding a new bullet or component beside existing text, keep neighboring unchanged lines exactly as they appear in `existing_spec`.
    - If `update_request` asks for a new bullet, component, boundary, or open question, insert only that material into the existing structure instead of regenerating neighboring paragraphs or adding unrelated template sections. This insertion rule does not apply to refresh, replace, or rewrite requests.
    - If `update_request` does not ask to revise the Purpose line, Problem Statement bullets, existing component descriptions, dependencies, or domain-model entities, keep those lines unchanged.
    - If `update_request` does not explicitly ask to revise `## 4. Core Domain Model`, preserve that entire section verbatim.
    - A newly added component, surface, or open question does not authorize adding a new entity or new fields.
    - If `update_request` asks for a new main component, add it only under `### 3.1 Main Components` unless the request explicitly asks for matching edits elsewhere.
    - If `update_request` asks for `## 5. Open Questions`, append that section and keep earlier prose unchanged unless the request explicitly asks to revise earlier sections.
    - Do not update problem counts, goal counts, or other numeric summary lines unless the request explicitly changes the bullets they count.
    - Emphasize problem statement, goals, non-goals, components, dependencies, and entities.
    - Make the prompt directly usable by an agent.

    Brief:
    {{ brief|format(type="yaml") }}
  "#
}
