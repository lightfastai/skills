# Harbor External Dependencies Refresh Packet

Assembled on April 23, 2026 from synthetic operator and founder follow-up
notes.

This packet is intentionally subsection-scoped. There is already a draft
`SPEC.md`, and it already contains the `Advocate Escalation Queue` component.
The request here is to refresh only `### 3.3 External Dependencies`, not to
rewrite the service description, add new components, or change the domain
model.

## Delta notes

- The current Harbor draft is mostly right on intake, shared case state,
  handoffs, benefits questions, and the explicit advocate escalation surface.
- The existing external-dependencies list is too loose. It reads like a
  participant list plus a generic "human advocates" line. Tighten it so the
  dependencies are framed as sources, communication channels, and human review
  authority.
- Keep `Purpose`, `Problem Statement`, `Goals and Non-Goals`,
  `### 3.1 Main Components`, `### 3.2 Abstraction Levels`,
  `Core Domain Model`, and `Open Questions` unchanged.
- Replace the current `### 3.3 External Dependencies` bullets with the current
  dependency boundary.
- Harbor depends on referral and intake sources, including referral forms,
  intake notes, and discharge paperwork.
- Harbor depends on care-document sources needed to understand current
  coordination context. This is document access, not an EHR integration.
- Harbor depends on communication channels used to coordinate with provider
  offices, pharmacies, payers, and other care contacts. Phrase this as a
  communication dependency, not as a bare list of counterparties.
- Harbor depends on human advocate review when an issue is ambiguous,
  sensitive, or clinically interpretive.
- Do not list patients, family caregivers, provider offices, pharmacies, or
  payers as bare external dependencies just because they are participants in
  the coordination loop.
- Do not invent EHR integration, claims processing, telehealth, clinical
  triage, consent-management, caregiver portal, notification infrastructure,
  or implementation-specific detail.
- The output should behave like a subsection refresh, not an append-only
  update and not a full-document rewrite.
