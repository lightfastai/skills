# Expected Criteria

- The output should frame `Harbor Care Coordination Service` as a long-running
  care-coordination service that turns messy referrals, intake notes, and
  follow-up events into a shared case timeline, explicit next actions, and
  handoff tracking.
- The purpose should mention intake or referrals, a shared case/timeline
  surface, and coordination across participants such as family caregivers,
  advocates, providers, pharmacies, or payers.
- The problem statement should capture fragmented care logistics, missing
  shared operating picture, and the burden placed on families when coordination
  is implicit.
- The output should keep human advocates central and include boundaries around
  clinical interpretation, telehealth, diagnosis, EHR behavior, insurer claims
  processing, and marketplace behavior.
- The output should include `### 3.2 Abstraction Levels` and
  `### 3.3 External Dependencies` using service-level language rather than
  developer-tooling language.
- The system overview should identify conservative components such as intake
  normalization, case timeline management, coordination task ownership, handoff
  tracking, advocate escalation, and a qualified benefits-question surface.
- External dependencies should stay conservative and source-backed, such as
  intake or referral channels, care documents, provider or payer
  communications, and human advocates. The output should avoid inventing EHR
  integrations, claims adjudication machinery, diagnosis engines, or
  compliance-specific infrastructure unless the packet states them directly.
- The core domain model should stay conservative. Minimal entities such as a
  care case, participant, coordination task, handoff, or benefits question are
  appropriate when they are kept source-backed.
- The output should preserve unresolved questions explicitly, including the
  automation-versus-advocate boundary, the access/sponsorship model, and the
  reminder-service boundary.
- The output should stay behavioral and language-agnostic, not implementation
  specific, and it should avoid company-foundation language.
