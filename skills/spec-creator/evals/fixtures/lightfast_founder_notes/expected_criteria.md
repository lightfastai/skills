# Expected Criteria

- The output should frame `Lightfast Workspace Coordinator` as a long-running
  repo or workspace coordination service for turning rough requests into
  packetized artifact drafts, evaluation runs, and explicit review decisions.
- The purpose should mention a repo/workspace-facing service boundary and
  should make the main surfaces visible, such as intake, artifact drafts, eval
  runs, approvals, or history.
- The problem statement should capture transcript drift, weak traceability, and
  the risk of silent or ungated mutation of canonical artifacts.
- The output should include boundaries around human review, explicit approval
  gates, and the fact that the service is not a general autonomous engineer,
  project manager, docs CMS, or arbitrary workflow runtime.
- The output should include `### 3.2 Abstraction Levels` and
  `### 3.3 External Dependencies` using service-level language.
- The system overview should identify conservative components such as intake or
  packet normalization, artifact drafting, evaluation coordination,
  review/approval gating, and history or traceability management.
- External dependencies should stay conservative and source-backed, such as
  workspace or repo files, model providers, version control, and qualified
  downstream evaluator or executor surfaces.
- The core domain model should stay conservative. Minimal entities such as a
  work packet or request, artifact draft, evaluation run, and approval
  decision are appropriate. The output should avoid schema-complete workflow or
  organization modeling.
- The output should preserve unresolved questions explicitly, including the
  repo-native versus hosted control-plane tension and the failed-eval
  follow-up boundary.
- The output should also preserve the named tension about how much of the
  service's value sits in drafting, evaluation, or review gates, rather than
  replacing it with a different unsourced open question.
- The output should remain a service `SPEC.md`, not a Lightfast foundation
  document. It should avoid company-thesis sections or language such as
  `What This Is`, `Durable Surfaces`, `Strategic Bets`, or broad claims that
  Lightfast is a durable artifact layer or operating system.
- The output should stay behavioral and language-agnostic, not implementation
  specific.
