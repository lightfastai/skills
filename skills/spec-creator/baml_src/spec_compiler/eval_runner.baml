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
    - Treat expected criteria as evaluation guidance, not as license to invent.
    - Preserve unresolved questions explicitly.
    - Avoid implementation detail.

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
    - Include these sections in order:
      - `## 1. Problem Statement`
      - `## 2. Goals and Non-Goals`
      - `### 2.1 Goals`
      - `### 2.2 Non-Goals`
      - `## 3. System Overview`
      - `### 3.1 Main Components`
      - `### 3.2 External Dependencies`
      - `## 4. Core Domain Model`
      - `### 4.1 Entities`
    - In `## 1. Problem Statement`, write:
      - one opening paragraph describing the service at a high level
      - a line like `The service solves <N> operational problems:`
      - a bullet list of concrete operational problems
    - Keep `Important boundary:` as a labeled block inside `## 1. Problem Statement`. Do not turn it into a standalone section.
    - Use a numbered list for `### 3.1 Main Components` in the form `1. `Component Name`` followed by indented responsibility bullets.
    - For entities, use `#### 4.1.x EntityName`, then `Fields:`, then field lines in the form `- `field_name` (type, constraints)` with indented semantic bullets and optional `Default: `value`` lines.
    - Use logical field types (`string`, `integer`, `boolean`, `timestamp`, `list of strings`, `map`, `string or null`), not implementation types.
    - List external dependencies as systems or services, not low-level API method names, SDK calls, classes, or internal implementation choices.
    - Preserve uncertainty where the source packet is in transition.
    - Avoid implementation detail.
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
    - Penalize missing core template sections, malformed field formatting, or moving `Important boundary:` out of the Problem Statement block.
    - Use `Pass`, `Partial`, or `Fail` for each criterion.

    {{ ctx.output_format }}
  "#
}
