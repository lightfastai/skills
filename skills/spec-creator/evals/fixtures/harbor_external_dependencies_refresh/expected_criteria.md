# Expected Criteria

- The output should behave like a narrow update to the existing `SPEC.md`,
  with `### 3.3 External Dependencies` refreshed rather than the full document
  being rewritten.
- The output should preserve `Purpose`, `## 1. Problem Statement`,
  `## 2. Goals and Non-Goals`, `### 3.1 Main Components`,
  `### 3.2 Abstraction Levels`, `## 4. Core Domain Model`, and
  `## 5. Open Questions` unchanged.
- The refreshed dependencies should be framed as external sources,
  communication channels, and qualified human review authority rather than as
  a bare participant list.
- The refreshed dependencies should include referral and intake sources,
  care-document sources for coordination context, communication channels with
  provider offices, pharmacies, payers, and other care contacts, and human
  advocate review for ambiguous, sensitive, or clinically interpretive issues.
- The older generic bullets `Referral and intake channels.`, `Care documents
  such as referral forms, intake notes, and discharge paperwork.`,
  `Communication channels with provider offices, pharmacies, payers, and other
  care contacts.`, and `Human advocates.` should be removed rather than
  preserved verbatim.
- The output should not list patients, family caregivers, provider offices,
  pharmacies, or payers as bare dependency bullets.
- The output should not invent EHR integration, claims adjudication,
  telehealth, clinical triage, caregiver portals, consent-management systems,
  notification infrastructure, or implementation-specific detail.
- The output should stay behavioral and language-agnostic, and it should
  remain a service `SPEC.md` rather than drifting into company-foundation
  language.
