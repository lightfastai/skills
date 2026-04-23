# Lightfast Workspace Coordinator Specification
Status: Draft v1 (language-agnostic)
Purpose: Lightfast Workspace Coordinator is a long-running repo/workspace coordination service at the workspace boundary for rough notes and source material, with an intake inbox, structured packet record, artifact draft workspace, evaluation results view, approval/rejection trail, and versioned history.

## 1. Problem Statement

Lightfast Workspace Coordinator keeps rough operator requests and source notes inside a repo/workspace boundary so they become inspectable packets, draft artifacts, evaluation results, and explicit review decisions instead of fading into an untraceable transcript. It preserves the ordered lineage from raw request to packet, brief, candidate artifact, eval run, and approval or rejection so people can inspect, edit, approve, or reject work with visible history.

The service solves 5 operational problems:
- Rough notes and source material can drift into an untraceable transcript instead of becoming inspectable artifacts.
- Canonical docs can be replaced or mutated without an explicit review gate.
- Evaluation failures can get detached from the draft instead of staying visible with the work that failed.
- Versioned history of what changed and why is hard to follow across request, packet, brief, candidate artifact, eval run, and decision stages.
- Ambiguous source notes can be over-interpreted instead of surfaced as open questions.

Important boundary:
- No silent mutation of canonical docs; replacement requires explicit review and approval.
- Failed evaluation runs stay attached to the draft instead of being hidden or discarded.
- Human review is part of the service boundary, not an incidental side effect.
- Downstream execution, if any, remains external to this service and only receives approved outputs.
- Only work that has been packetized into artifact stages is in scope for coordination.
- Open questions from the source packet should remain visible rather than being resolved by guesswork.

## 2. Goals and Non-Goals

### 2.1 Goals
- Intake rough notes or source material and normalize them into a structured packet.
- Produce draft artifacts that can be inspected, edited, approved, or rejected.
- Coordinate evaluation runs against packet criteria and keep the results attached to the draft trail.
- Preserve lineage from raw request to packet, brief, candidate artifact, eval run, and approval or rejection.
- Make human review and explicit approval the point where canonical replacement or downstream handoff can happen.
- Surface unresolved questions rather than pretending ambiguous source material is settled.

### 2.2 Non-Goals
- Not a general autonomous software engineer.
- Not project management or backlog grooming.
- Not a docs CMS.
- Not an arbitrary workflow runtime or hidden background execution system.
- Not a system that silently regenerates until a draft looks plausible.
- Not the downstream executor for approved business workflows.

## 3. System Overview

Lightfast Workspace Coordinator is organized around workspace-facing intake, artifact lineage, review-bound coordination, and visible history. It does not hide state transitions behind silent background mutation; instead, it keeps the packet, brief, draft, evaluation, and decision trail inspectable.

### 3.1 Main Components
1. `Intake and packet normalization`
   - Accept rough notes or source material from the workspace boundary.
   - Normalize source material into a structured packet record.
   - Preserve the visible connection between raw request input and packet output.
   - Surface ambiguous material as questions rather than resolving it implicitly.

2. `Artifact drafting`
   - Produce draft foundation, spec, or eval artifacts from the packet.
   - Keep drafts inspectable and editable before any approval decision.
   - Maintain the link between the packet and each candidate artifact.
   - Allow drafts to remain in progress without implying completion.

3. `Evaluation run coordination`
   - Coordinate evaluations against packet criteria when evaluation is used.
   - Keep evaluation results attached to the draft trail.
   - Preserve failed runs alongside the work that produced them.
   - Attach criteria text so review can inspect what was measured.

4. `Review decision handling`
   - Present drafts and evaluation outcomes for explicit approval or rejection.
   - Keep reviewer comments visible with the decision trail.
   - Make approval the visible point where canonical replacement or handoff may happen.
   - Stop short of downstream execution.

5. `Traceability and history`
   - Preserve the visible lineage from source request through packet, brief, draft, evaluation, and decision.
   - Keep change history and evaluation outcomes inspectable.
   - Support versioned history or timeline views at the workspace boundary.
   - Make it clear what changed and why across long-running coordination.

### 3.2 Abstraction Levels
1. `Workspace-facing intake layer`
   - Keeps the service anchored to repo or workspace source material.
   - Accepts rough notes, source packets, and other entry material.
   - Avoids free-form transcript accumulation as the primary record.
   - Surfaces source ambiguity instead of converting it to assumed intent.

2. `Artifact lineage layer`
   - Maintains the ordered progression from raw request to packet, brief, draft, eval run, and decision.
   - Connects each artifact stage to the next stage in the visible trail.
   - Keeps candidate artifacts tied to the packet that produced them.
   - Preserves the distinction between intermediate stages rather than collapsing them.

3. `Review-bound coordination layer`
   - Holds work until humans make an explicit approval or rejection decision.
   - Prevents silent replacement of canonical docs.
   - Keeps evaluation failures and reviewer comments visible during review.
   - Allows downstream handoff only after approval.

4. `Traceability layer`
   - Makes change history and evaluation outcomes inspectable.
   - Supports versioned history or timeline views.
   - Keeps the service long-running without hiding state transitions.
   - Exposes what changed across request, packet, brief, draft, evaluation, and decision stages.

### 3.3 External Dependencies
- Workspace files and repository state
- Version control
- Model providers, when draft generation or normalization uses model assistance
- A separate evaluator service, if present
- A downstream execution system for approved outputs, if present

## 4. Core Domain Model

### 4.1 Entities

The core model is intentionally small and centers on the packet, draft, evaluation, and decision trail that the service makes visible.

#### 4.1.1 WorkPacket
Fields:
- `id` (string)
  - Stable identifier for the packet record.
- `raw_request` (string)
  - Original rough notes or source material submitted to the service.
- `packet_text` (string or null)
  - Normalized packet text produced from the raw request.
  - May remain null until the intake material has been normalized.
- `brief_text` (string or null)
  - Narrower brief derived from the packet before candidate artifact drafting.
  - Keeps the packet-to-brief stage visible in the lineage.
- `open_questions` (list of strings or null)
  - Source-backed unresolved questions that should remain visible.
  - Reflects ambiguity that should not be guessed away.

#### 4.1.2 ArtifactDraft
Fields:
- `id` (string)
  - Stable identifier for the draft artifact.
- `source_packet_id` (string)
  - Reference to the packet that produced this draft.
  - Preserves the lineage from packet to candidate artifact.
- `artifact_kind` (string)
  - Source-visible kind of draft, such as foundation, spec, or eval document.
- `draft_text` (string or null)
  - Current draft content.
  - May be revised before approval or rejection.

#### 4.1.3 EvaluationRun
Fields:
- `id` (string)
  - Stable identifier for the evaluation run.
- `source_draft_id` (string)
  - Reference to the draft that was evaluated.
  - Keeps the evaluation result attached to the work that was checked.
- `result` (string)
  - Evaluation outcome or summary, such as pass or fail.
- `criteria_text` (string or null)
  - Criteria or rubric used for the run.
  - May reflect packet criteria when evaluation is coordinated externally.

#### 4.1.4 ApprovalDecision
Fields:
- `id` (string)
  - Stable identifier for the decision record.
- `source_draft_id` (string)
  - Reference to the draft that received the review decision.
  - Connects approval or rejection back to the candidate artifact.
- `decision` (string)
  - Review outcome, such as approved or rejected.
- `reviewer_comments` (string or null)
  - Reviewer notes explaining the decision or requested changes.
  - Keeps review rationale visible in the trail.

## 5. Open Questions

- Should the service stay repo-native and workspace-local first, or become a hosted catalog or multi-workspace control plane later?
- When an evaluation fails, should the service create follow-up tasks itself, or only surface the failure to humans or external systems?
- How much of the service's value should land first in drafting, evaluation, or review gates?
