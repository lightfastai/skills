# Lightfast Non-Goals Refresh Packet

Assembled on April 23, 2026 from synthetic founder and operator follow-up
notes.

This packet is intentionally subsection-scoped. There is already a draft
`SPEC.md`, and the service framing is mostly right. The request here is to
refresh `### 2.2 Non-Goals`, not to rewrite the service.

## Delta notes

- Keep the existing `Purpose`, `Problem Statement`, `### 2.1 Goals`,
  `System Overview`, `Core Domain Model`, and `Open Questions` wording.
- Refresh only `### 2.2 Non-Goals`.
- The current non-goals list has stale shorthand like "general autonomous
  software engineer" and "docs CMS." That wording is too vague now.
- The sharper boundary is that this service should not become ticket routing,
  sprint planning, backlog management, or team task assignment.
- It also should not mutate repositories, apply approved changes, run CI,
  deploy, or become the post-approval execution surface.
- It should not become a hosted multi-workspace or multi-tenant control plane.
- It should not become a wiki, docs publishing platform, or general content
  management system.
- It should not become a silent drafting loop that keeps rewriting or
  re-evaluating until something finally passes.
- Keep the section behavioral and language-agnostic. Do not add
  implementation-specific details.
- Do not drift into company-thesis or strategic-foundation language.
- This should behave like a section refresh. Replace the stale shorthand
  bullets rather than appending the new ones underneath them.
