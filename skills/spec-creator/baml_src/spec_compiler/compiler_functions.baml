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
    - Preserve unresolved questions explicitly.
    - Preserve packet-named unresolved tensions when they affect scope, actor boundaries, approval gates, deployment shape, or operating model.
    - If the notes contain multiple materially distinct unresolved tensions, keep them distinct in `unresolved_questions` instead of collapsing them into one generic question.
    - If the notes contain explicit `Unresolved:` items, treat them as high-priority source facts. Preserve each materially distinct unresolved item in `unresolved_questions` unless two items are true duplicates.
    - Do not replace a packet-named open question with a narrower unsourced variant.
    - Do not invent a new unresolved question if it causes a packet-stated unresolved question to be dropped.
    - Do not invent implementation detail.
    - Keep packet-named service surfaces distinct when they matter. For example, if the notes name teams separately from projects, do not silently collapse teams into projects.
    - `components` should describe major service responsibilities or user-visible service surfaces, not low-level classes, methods, SDKs, or protocols.
    - `abstraction_layers` should describe stable behavioral layers that make the service easier to reason about or port. Keep them service-level and conservative.
    - `external_dependencies` must name external systems, resources, or authorities explicitly visible in the notes. Do not list inferred internals such as token issuance, allowlists, registries, classes, transport mechanics, or storage engines unless they are stated directly.
    - `entities` should model only externally meaningful nouns the service manipulates or exposes. Do not create entities only to complete a plausible schema.
    - Every entity field must be directly supported by the notes or be the minimal identity/status field required to keep the entity coherent. Prefer fewer fields over speculative completeness.
    - Prefer the smallest viable domain model. If an extra entity or field only restates behavior already captured elsewhere, omit it.
    - Use only logical field types such as `string`, `integer`, `boolean`, `timestamp`, `list of strings`, `map`, or `string or null`. Do not invent custom type labels like `duration`.
    - Do not embed `required`, `optional`, or invented constraints like `unique within service scope` into `type_expression`.
    - If a concept is visible in the notes but does not support a stable entity schema, keep it in components, dependencies, or unresolved questions instead of forcing it into the domain model.
    - If `existing_spec` is present, preserve compatible intent and only sharpen gaps.
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
    - Flag abstraction layers that drift into low-level implementation or internal class design.
    - Flag dependencies that name inferred internals rather than source-visible external systems.
    - Flag entity/field modeling that looks like speculative schema completion rather than source-backed service behavior.

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
    - Require `## 1. Problem Statement` to contain:
      - one opening paragraph
      - a line like `The service solves <N> operational problems:`
      - a bullet list of explicit operational problems
    - Require the `Purpose:` line to name the service kind, the protected endpoint or access boundary, and the main resource surfaces at the highest stable granularity the brief supports.
    - If the brief names surfaces like docs, teams, projects, deployments, or logs, mention them explicitly in the `Purpose:` line rather than replacing them with vague phrases like `operational context`.
    - If the brief is fundamentally about coordination across named participant types, roles, or organizations, mention that cross-party coordination boundary in the `Purpose:` line instead of only naming artifacts or records.
    - If the brief names explicit ingress surfaces such as referrals, intake notes, source packets, or raw notes as core to the service, mention at least one of those entry surfaces in the `Purpose:` line instead of only describing downstream records or outputs.
    - Keep the `Purpose:` line concrete and source-bound. Avoid metaphorical or unsourced framing verbs like `protects`, `defends`, `guards`, or similar language unless the brief explicitly uses them.
    - Require `Important boundary:` as a standalone labeled block inside the Problem Statement, followed by boundary bullets.
    - Require numbered components and template-shaped field lines: `- `field_name` (type, constraints)`.
    - Require `### 3.2 Abstraction Levels` to explain stable behavioral layers rather than runtime call order or internal code structure.
    - Require external dependencies to stay at the system/service level rather than naming low-level API methods, SDK calls, token mechanics, registry internals, classes, or storage implementation.
    - Require packet-named surfaces to remain visible when they materially matter. For example, if the brief distinguishes teams from projects, keep that distinction somewhere in the spec instead of collapsing it away.
    - Require the domain model to stay conservative:
      - include only entities materially supported by the brief
      - prefer fewer entities over speculative completeness
      - use minimal source-backed fields
      - if a concept lacks enough support for a stable entity schema, keep it out of `## 4. Core Domain Model`
      - avoid second-order record types when a smaller set of entities or fields already makes the behavior legible
    - In field lines, use only logical types and source-backed constraints.
    - Do not put `required`, `optional`, `non-empty`, `unique`, or invented service-scope constraints inside the field parentheses.
    - If requirement state matters, express it in the indented semantic bullet rather than inside the type parentheses.
    - If `unresolved_questions` are materially important, add `## 5. Open Questions` after the domain model and render them as bullets.
    - When multiple unresolved questions are present, preserve the distinct tensions rather than reducing them to a single generic question.
    - Keep `## 5. Open Questions` source-bound. If the brief names a structural tension such as repo-native vs hosted, family-direct vs sponsored, or automation vs human ownership, carry that tension forward explicitly.
    - When the source notes include explicit `Unresolved:` bullets, keep those questions source-traceable in `## 5. Open Questions` rather than substituting different questions.
    - In update mode, do not add new top-level sections or template-completion material unless the request explicitly asks for them.
    - Emphasize problem statement, goals, non-goals, components, dependencies, and entities.
    - Make the prompt directly usable by an agent.

    Brief:
    {{ brief|format(type="yaml") }}
  "#
}
