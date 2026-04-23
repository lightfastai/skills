# Lightfast Update Addendum Packet

Assembled on April 22, 2026 from synthetic founder and operator follow-up
notes.

This packet is intentionally update-shaped. There is already a draft
`SPEC.md`. These notes are only the delta and should not trigger a rewrite of
the whole document.

## Delta notes

- The existing draft is mostly right on intake, packet lineage, eval
  attachment, review gates, and visible history.
- What still feels underspecified is the thing that exists after approval.
  Right now there is a decision trail, but not a clearly named approved-output
  handoff surface.
- Need a durable object or surface for "this is the exact artifact that was
  approved, with the packet lineage and review context that went with it."
- Call that new appended component `Approved Output Handoff`.
- That handoff should make the approved artifact version, source packet or
  draft lineage, evaluator context if present, and reviewer comments visible
  together.
- Important boundary: this is packaging and visibility, not execution. Do not
  make this service apply changes to the repo, run downstream jobs, or become
  a workflow runtime.
- It may later capture whether a downstream system acknowledged receipt, but it
  is unresolved whether acknowledgement state belongs here or in the downstream
  system.
- Do not describe downstream acknowledgement as a current guaranteed capability
  of this service. Keep it as an explicit ownership question.
- Also unresolved: if the packet or draft changes after approval, does the old
  handoff remain current, become stale automatically, or require a new review
  before another handoff exists?
- Also unresolved: do rejected drafts ever produce a handoff object, or is
  handoff strictly for approved outputs?
- Keep the service repo/workspace-facing. Do not use this update to turn it
  into a hosted control plane, general docs system, or project-management
  queue.
- Add the new handoff surface as an appended main component instead of
  rewriting earlier component order.
- Add open questions instead of resolving the acknowledgement or stale-approval
  rules by guesswork.
