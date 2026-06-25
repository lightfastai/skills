# Initiative Reference

Use this reference when creating or updating Linear initiatives through Lightfast MCP.

Linear basis: initiatives are manually curated workspace-level lists of projects with an accompanying document, used to express organizational goals and monitor progress across multiple projects and long timelines. Initiative updates use a health indicator plus rich-text status to keep leaders and teams aligned.

Docs:

- https://linear.app/docs/initiatives
- https://linear.app/docs/initiative-and-project-updates
- https://linear.app/docs/custom-views
- https://linear.app/docs/sub-initiatives

## When To Use An Initiative

Use an initiative when the work:

- Represents an organizational objective, company bet, strategic goal, or cross-project program.
- Needs to group multiple projects manually, not by a filter.
- Spans multiple teams, workstreams, or a long timeline.
- Needs leadership-level progress, health, target date, or ownership.

Do not create an initiative when:

- One bounded deliverable is enough; create a project instead.
- The grouping is dynamic or filter-shaped; create or use a custom view instead.
- The work is a task list; create a project with issues.
- The category is a permanent area such as `Infrastructure`, `Research`, or `Growth` without a time-bounded objective.

Initiatives are workspace-wide. Do not promise private initiatives; private-team project visibility remains separate from initiative visibility.

Use sub-initiatives only when the workspace supports them and the program is large enough to need nested objectives. Do not create nested initiatives by default.

## Initiative Title

Name the objective or desired change, not the activity bucket.

Use:

- `Reliable Agent Runtime`
- `Production-Ready Customer Requests`
- `Enterprise Readiness`
- `Developer Activation`

Avoid:

- `Q3 Projects`
- `Infrastructure`
- `Linear Cleanup`
- `Research`
- `Workstreams`

## Initiative Summary

Use one sentence for what becomes true if the initiative succeeds.

Pattern:

```text
<Achieve/enable/ship/improve> <objective> so that <audience/system> can <strategic result>.
```

Examples:

- `Ship the core customer request loop so product teams can capture, triage, and act on customer asks in one place.`
- `Harden the agent runtime so internal and external builders can run longer tasks with predictable recovery and observability.`

## Initiative Description

Use this lightweight description:

```markdown
## Objective

What strategic outcome should this initiative create?

## Why Now

Why this matters now. Include timing, customer pressure, market pressure, risk, or dependency.

## Project Portfolio

- Project:
- Project:

## Scope

- Included:
- Excluded:

## Success Signals

- Observable signal:
- Observable signal:

## Health / Update Cadence

- Owner:
- Cadence:
- Current health:

## Risks / Decisions

- Risk:
- Decision:

## Open Questions

- Question:
```

Keep the description strategic. Put detailed project specs, research notes, diagrams, and implementation details in projects, Linear documents, or external resources, then link them.

## Initiative Properties

Set properties only when the user provides them or discovery makes the workspace convention clear:

- Owner: one accountable person.
- Teams: teams materially contributing to the objective.
- Target date: only when date pressure or planning horizon matters.
- Health: use when creating an update or when the user provides current status.
- Resources: links to strategy docs, planning docs, dashboards, or decision records.
- Projects: manually curated projects that materially advance the objective.

Do not add every related project. Curate projects that make progress measurable.

## Initiative Updates

Use initiative updates when the user asks for status, health, leadership reporting, or progress summaries.

Update shape:

```markdown
## Progress

- What moved since the last update:

## Health

- On track / At risk / Off track:
- Reason:

## Risks / Blockers

- Risk:
- Blocker:

## Next

- Next project or decision:
```

Keep updates honest and operational. Surface blockers and decisions early.

## Creation Workflow

When creating an initiative:

1. Confirm the objective is bigger than one project.
2. Identify candidate projects or project proposals.
3. Decide whether each project should already exist, be created now, or remain a placeholder in the description.
4. Discover Lightfast Linear routines and schemas.
5. Create the initiative with the minimum useful properties.
6. Link existing projects or create associated projects only when the routine supports it and the user asked for that structure.
7. Return the initiative link, linked projects, missing decisions, and recommended next project or issue creation step.
