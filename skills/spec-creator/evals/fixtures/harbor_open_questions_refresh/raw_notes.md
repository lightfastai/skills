# Harbor Open Questions Refresh Packet

Assembled on April 23, 2026 from synthetic operator and founder follow-up
notes.

This packet is intentionally subsection-scoped. There is already a draft
`SPEC.md`, and it already contains the `Advocate Escalation Queue` component.
The request here is to refresh `## 5. Open Questions`, not to rewrite the
service description.

## Delta notes

- The current Harbor draft is mostly right on intake, shared case state,
  handoffs, benefits questions, and the explicit advocate escalation surface.
- The older open questions were useful earlier, but the sharper unresolved
  tensions are now around household access authority, external-resolution
  tracking after an escalation, and after-hours non-clinical support
  boundaries.
- Keep the existing service framing, scope, and component wording. Do not
  rewrite `Purpose`, `Problem Statement`, `Goals and Non-Goals`,
  `System Overview`, or `Core Domain Model`.
- `Advocate Escalation Queue` is already the right component name and should
  stay as-is. This packet is not asking for another component or new entities.
- Replace the current `## 5. Open Questions` section with questions focused on
  the current advocate and household-boundary ambiguity.
- First question: which non-advocate participants can view or update the
  shared case timeline? Is that limited to the patient, patient-designated
  caregivers, or some sponsored navigator role? Keep it unresolved rather than
  inventing a portal or permissions engine.
- Second question: when Harbor escalates a benefits or coordination issue to a
  payer, provider office, or pharmacy, does Harbor track the external
  resolution state, or only the handoff plus the next internal follow-up?
- Third question: if a time-sensitive but non-clinical issue lands after
  hours, does it wait for the next advocate review window or belong in a
  separate urgent-support path?
- Do not turn after-hours handling into telehealth, clinical triage, or on-call
  clinical support.
- Do not add a portal component, consent engine, claims adjudication, EHR
  behavior, or operational runbook detail.
- The output should behave like a section refresh, not a rewrite with broader
  rewording.
