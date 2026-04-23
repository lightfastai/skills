# Lightfast Open Questions Refresh Packet

Assembled on April 22, 2026 from synthetic founder and operator follow-up
notes.

This packet is intentionally subsection-scoped. There is already a draft
`SPEC.md`, and it already contains the `Approved Output Handoff` component.
The request here is to refresh `## 5. Open Questions`, not to rewrite the
service description.

## Delta notes

- The current open questions are now slightly off. They still reflect earlier
  "where does value land first" framing, but the sharper tension is around the
  approval-to-handoff boundary.
- Keep the existing service framing, scope, and component wording. Do not
  rewrite `Purpose`, `Problem Statement`, `Goals and Non-Goals`,
  `System Overview`, or `Core Domain Model`.
- `Approved Output Handoff` is already the right component name and should
  stay as-is. This packet is not asking for another component or for schema
  changes.
- Replace the current `## 5. Open Questions` section with questions focused on
  the approval-handoff boundary.
- First question: if an approved output is handed off to another system, who
  owns acknowledgement of receipt or acceptance? It is unresolved whether that
  acknowledgement belongs in this service or only in the downstream system.
- Second question: if the packet or candidate draft changes after approval,
  what happens to the existing handoff? Does it remain as a historical record,
  become stale automatically, or require another approval before a new handoff
  can exist?
- Third question: do rejected drafts ever produce a handoff object for audit
  or reference, or is handoff strictly approval-only?
- Do not turn acknowledgement into a resolved current capability. Keep it as
  an open question.
- Do not use this update to turn the service into a workflow runtime,
  deployment executor, release manager, hosted control plane, or queue system.
- The output should behave like a section refresh, not a rewrite with broader
  rewording.
