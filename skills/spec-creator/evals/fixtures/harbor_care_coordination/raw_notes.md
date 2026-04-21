# Harbor Care Coordination Packet

Assembled on April 21, 2026 from synthetic founder and operations notes.

This packet tests whether `spec-creator` generalizes to a non-developer,
trust-heavy operations service without inventing clinical authority, compliance
machinery, or overly complete healthcare schemas.

## Raw notes

- Working name: `Harbor Care Coordination Service`.
- Families keep becoming the default project managers for eldercare and
  chronic-care logistics. The service should turn scattered referrals, notes,
  discharge instructions, and benefits questions into a living coordination
  case with explicit ownership.
- The problem is not diagnosis. The problem is that tasks, documents,
  callbacks, and handoffs sit in different places and nobody has a current
  operating picture.
- Inputs are messy: referral forms, intake call notes, discharge paperwork,
  home-care issues, pharmacy problems, benefits questions.
- The service should normalize that into one case timeline plus a queue of
  next actions.
- Human advocates are central. If something is ambiguous, sensitive, or
  clinically interpretive, route it to an advocate instead of pretending the
  system can decide.
- It should track who owns the next step across family caregiver, advocate,
  provider office, home-care organization, pharmacy, or payer contact.
- It should preserve a longitudinal record of what happened, what is pending,
  and what still needs documents or callbacks.
- Handoff tracking matters a lot: hospital -> home, clinic -> rehab,
  pharmacy -> family, payer -> advocate, etc.
- There may be a benefits or eligibility question surface, but this is not an
  adjudication engine.
- The system may send reminders or request missing documents, but it should not
  turn into a generic outbound CRM.
- Not telehealth.
- Not diagnosis or treatment planning.
- Not an EHR.
- Not an insurer claims processor.
- Not a marketplace for clinicians or home aides.
- likely actors:
  - family caregiver
  - patient sometimes
  - care advocate
  - external provider or discharge planner
  - payer or benefits administrator occasionally
- recurring service surfaces:
  - referral / intake normalization
  - case timeline
  - coordination task queue with ownership
  - handoff tracker
  - advocate escalation queue
  - benefits question tracker maybe
- Unresolved:
  how much outbound follow-up can be automated vs advocate-owned?
- Unresolved:
  is the primary access model family direct, employer/payer sponsored, or
  provider-linked?
- Unresolved:
  do reminders belong here or in a separate communication service?
- External dependencies probably include intake/referral channels, care
  documents, communications with providers/payers, and human advocates. Keep
  the runtime honest about the human boundary.
- If records conflict, the service should surface the discrepancy and keep the
  case moving where possible, not invent a clinical conclusion.
