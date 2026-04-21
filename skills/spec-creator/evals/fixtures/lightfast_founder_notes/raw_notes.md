# Lightfast Founder Notes Packet

Assembled on April 21, 2026 from synthetic founder-style product notes.

This packet is intentionally messy. It tests whether `spec-creator` can derive
a concrete service specification for a Lightfast runtime surface without
sliding into company-foundation language or inventing implementation that the
notes do not settle.

## Raw notes

- Working name: `Lightfast Workspace Coordinator`. Maybe the product name stays
  just `Lightfast`, but this service is the clearest concrete slice right now.
- The thing probably lives inside or alongside a repo/workspace and manages the
  loop from rough operator request -> structured packet -> draft artifacts ->
  eval results -> explicit review decision.
- It is not another infinite chat transcript. The durable thing should be the
  packet, draft, eval, and approval trail.
- Someone should be able to drop in founder/operator notes and get back
  explicit artifacts that can be inspected, edited, approved, or rejected.
- Feels like an operator inbox plus artifact pipeline.
- Maybe also feels like a repo-native work loop with checkpoints.
- Strong rule: no silent mutation of canonical docs. Anything that might
  replace a foundation/spec or kick off downstream execution should go through
  an explicit review gate.
- Strong rule: failed evals stay attached to the draft. The service should not
  quietly keep regenerating until something looks plausible.
- The service should preserve lineage:
  raw request -> packet -> brief -> candidate artifact -> eval run ->
  approval/rejection.
- Main surfaces that recur:
  - intake of rough notes / source material
  - artifact drafting for foundation/spec/eval docs
  - evaluation runs against packet criteria
  - approval / rejection with reviewer comments
  - versioned history of what changed and why
- likely actors:
  - operator / founder / PM / eng lead
  - reviewer / approver
  - optional downstream executor or another agent system
- Not a general autonomous software engineer.
- Not project management or backlog grooming.
- Not a docs CMS.
- Not the runtime that executes arbitrary business workflows after approval.
- It should only coordinate work that has been packetized into artifact stages.
- There may be lightweight status states for work items and drafts, but do not
  turn it into a full BPM monster.
- Unresolved:
  repo-native first vs a hosted catalog / multi-workspace control plane later.
- Unresolved:
  when an eval fails, does this service create follow-up tasks itself or just
  surface the failure for humans / external systems?
- Unresolved:
  how much of the value is in drafting vs evaluation vs review gates?
- External things it probably depends on:
  workspace files / repo state,
  model providers,
  version control,
  maybe a separate evaluator,
  maybe a downstream execution system for approved outputs.
- If the source packet is ambiguous, the service should surface open questions
  rather than pretend it understands the answer.
