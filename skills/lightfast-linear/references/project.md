# Project Reference

Use this reference when creating or updating Linear projects, project descriptions, project properties, or project milestones through Lightfast MCP.

Linear basis: projects organize feature, release, and other bounded work; issues can belong to only one project at a time; the project lead owns the spec and general execution; project milestones represent stages in a project's lifecycle and can be shown on timelines and initiative views.

Docs:

- https://linear.app/docs/projects
- https://linear.app/docs/project-overview
- https://linear.app/docs/project-milestones
- https://linear.app/docs/project-status
- https://linear.app/docs/project-templates
- https://linear.app/method/scope-projects

## When To Use A Project

Use a project for:

- A feature, release, research bet, migration, launch, or large deliverable with a planned completion path.
- Work that needs a project lead, project brief, scope, milestones, status, timeline, or initiative association.
- A bounded slice of an ongoing area.

Do not create a project when:

- The work is one concrete task; create an issue.
- The work is an org-level goal made of multiple projects; create or use an initiative.
- The work is a recurring category or permanent area; prefer smaller time-bounded projects or a custom view.

## Project Title

Name the bounded deliverable or bet, not the activity.

Use:

- `Customer Request Inbox`
- `Usage-Based Billing`
- `Attuned Interaction Prototype`
- `Mobile Onboarding Refresh`

Avoid:

- `Research`
- `Infrastructure`
- `Q3 Work`
- `Explore Ideas`

## Project Summary

Use one sentence for what becomes true if the project succeeds.

Pattern:

```text
<Verb> <outcome> so that <audience/system> can <new capability or decision>.
```

Examples:

- `Ship a request inbox so support and product can triage customer asks from one place.`
- `Build and evaluate a prototype so the team can decide whether the interaction model is worth extending.`

## Project Description

Use this lightweight description:

```markdown
## Outcome

What will be true when this project succeeds?

## Why Now

Why this matters now. Include timing, dependency, user pressure, or strategic pressure.

## Scope

- Included:
- Excluded:

## Milestone Plan

- Stage:
- Stage:
- Stage:

## Success Signals

- Observable signal:
- Observable signal:

## Open Questions

- Question:
- Question:
```

Keep the description strategic and navigable. Put long specs, research notes, and diagrams in Linear documents or external resources, then link them from the project.

## Project Properties

- Assign a single lead when the user provides one or the workspace convention is clear.
- Add members only when collaboration or notifications matter.
- Add start and target dates only when the user provides dates or wants forecasting.
- Choose broad timeframes when precise dates are not known.
- Associate an initiative when the project materially advances that objective.
- Add external resources when they are decision-relevant.
- Set status only when the user provides it or the workflow requires it; project statuses are manual.

Use project templates only when the user asks for a repeatable pattern or the workspace already has a template that fits.

## Milestone Structure

Use milestones as lifecycle stages or evidence gates inside a project, not as themes or departments.

Each milestone should have:

```text
Name:
Stage of completion.

Description:
What this stage must prove, produce, or unlock.

Done When:
2-4 concrete exit criteria.

Target date:
Only when the user provides date pressure or forecasting matters.
```

Good exploratory milestone patterns:

- `Frame the bet`
- `Build the smallest proof`
- `Evaluate the signal`
- `Decide the next bet`

Good product/build milestone patterns:

- `Define scope`
- `Build core path`
- `Validate with users`
- `Ship`
- `Measure follow-up`

Good release milestone patterns:

- `Internal alpha`
- `Beta 1`
- `Beta 2`
- `Public launch`
- `Post-launch readout`

Rules:

- Milestones should be legible on timelines and initiative views.
- Do not use milestones for themes like `Infra`, `Design`, `Research`, or `Voice` unless the project itself is organized by workstream.
- Current milestones get concrete issues.
- Next milestones can have placeholders only when needed.
- Later milestones stay as descriptions until evidence catches up.
- If a milestone grows into a large independent deliverable, consider turning it into its own project.

## Creation Workflow

When creating a project:

1. Confirm the project has a bounded outcome.
2. Draft the title, summary, description, properties, and milestone plan.
3. Decide whether it belongs to an existing initiative.
4. Create concrete issues only for the current milestone or immediate execution stage.
5. Discover Lightfast Linear routines and schemas.
6. Create the project, milestones, and immediate issues only when the user asked for that structure.
7. Return the project link, milestone outline, created issues, and unresolved decisions.
