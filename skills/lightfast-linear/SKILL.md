---
name: lightfast-linear
description: General-purpose Linear planning and creation guidance for Lightfast MCP work. Use only when the user explicitly invokes $lightfast-linear and the task involves creating, updating, triaging, or planning Linear projects, milestones, or issues through mcp__lightfast provider routines. Do not invoke implicitly and do not use for general Linear planning outside Lightfast MCP.
---

# Lightfast Linear

Use this skill only after the user explicitly invokes `$lightfast-linear` for Lightfast-driven Linear work. Shape Linear projects, milestones, and issues into a lightweight operating system: bounded project outcomes, milestone stage gates, and artifact-shaped issues.

## Operating Rule

When using `mcp__lightfast` with Linear:

1. Discover available Linear routines before assuming schemas or IDs.
2. Shape the project, milestone, or issue before calling a write routine.
3. Keep Linear structure lightweight enough to maintain.
4. Do not generate full future milestone issue batches before the current stage has produced evidence.

Skip this skill if the user did not explicitly invoke it, or if Lightfast MCP is not part of the task.

## Lightfast Routine Discovery

Before calling a Linear provider routine:

1. If needed, check availability with `mcp__lightfast.lightfast_system_health`.
2. Find available Linear routines with `mcp__lightfast.proxy_find` using `provider: "linear"` and `includeSchema: true`.
3. Select the routine that matches the requested operation.
4. Call the routine with the exact schema returned by Lightfast.
5. Report what changed, including Linear links or IDs returned by the routine.

Do not assume routine IDs, argument names, team IDs, project IDs, milestone IDs, label IDs, or workspace configuration. Discover them through Lightfast or ask the user if discovery does not provide enough information.

## Core Model

Use this hierarchy:

- Project: bounded outcome or deliverable.
- Milestone: stage of completion inside the project.
- Issue: artifact-shaped unit of work.

Avoid using projects for permanent ongoing areas. If the work is ongoing, prefer smaller time-bounded projects, an Initiative, or a maintenance-style project only when that is explicitly the desired workflow.

## Project Structure

Use Linear projects for features, releases, research bets, or large units of work with a clear outcome or planned completion.

### Project Title

Name the bounded deliverable or bet, not the activity.

Use:

- `Customer Request Inbox`
- `Usage-Based Billing`
- `Attuned Interaction Prototype`
- `Mobile Onboarding Refresh`

Avoid:

- `Research`
- `Infrastructure`
- `Q3 work`
- `Explore ideas`

### Project Summary

Use one sentence for what becomes true if the project succeeds.

Pattern:

```text
<Verb> <outcome> so that <audience/system> can <new capability or decision>.
```

Examples:

- `Ship a request inbox so support and product can triage customer asks from one place.`
- `Build and evaluate a prototype so the team can decide whether the interaction model is worth extending.`

### Project Description

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

### Project Properties

- Assign a single lead when the user provides one or the workspace convention is clear.
- Add members only when collaboration or notifications matter.
- Add start and target dates only when the user provides dates or wants forecasting.
- Choose broad timeframes when precise dates are not known.
- Add external resources when they are decision-relevant.

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
- Current milestone gets concrete issues.
- Next milestone can have placeholders only when needed.
- Later milestones stay as descriptions until evidence catches up.
- If a milestone grows into a large independent deliverable, consider turning it into its own project.

## Issue Structure

Issues should be artifact-shaped, not thought-shaped.

Each issue should usually produce one durable artifact: a memo, decision, diagram, prototype, rubric, dataset, evaluation readout, code change, design, or equivalent object.

Use one grouped label set:

- `Type/Research`: creates evidence, comparison, synthesis, taxonomy, or structured understanding.
- `Type/Prototype`: creates runnable, inspectable, or interactive behavior.
- `Type/Evaluation`: scores, tests, audits, compares, or validates an artifact.
- `Type/Writing`: turns thinking into durable prose for others to use.
- `Type/Decision`: resolves a fork and records the rationale.

Rules:

- Give every issue exactly one `Type/*` label when labels are available.
- Do not add `Artifact`, `Theme`, or `Risk` labels by default.
- Put artifact, theme, and risk context in the title/body instead.
- Add new labels only when they power a real view, review ritual, automation, ownership rule, or recurring management decision.

Use this issue body:

```markdown
## Outcome

What exists, is answered, or is decided when this issue is complete?

## Context

Why this matters now. Include the hypothesis, dependency, or decision pressure if relevant.

## Scope

- Included:
- Excluded:

## Deliverable

Name the artifact or change that will exist.

## Done When

- Observable criterion:
- Observable criterion:
- Next step is linked, created, or explicitly rejected:
```

Add optional sections only when they clarify the work:

```markdown
## Method

1. Step:
2. Step:
3. Step:

## Unknowns / Risks

- Unknown:
- Risk:
- Review gate:

## References

- Link:
- Link:
```

## Title Rules

Good titles name the artifact and the action.

Use titles like:

- `Write the project framing memo`
- `Map the core workflow`
- `Create the v0 evaluation rubric`
- `Build the scripted prototype`
- `Decide the first implementation path`
- `Audit the onboarding flow`
- `Draft the launch readout`

Avoid titles like:

- `Think about strategy`
- `Explore ideas`
- `Prototype stuff`
- `Research competitors`
- `Figure out what to build`

## Review Checklist

Before creating or updating Linear structure, check:

- Does the project have a bounded outcome?
- Does the project summary say what becomes true?
- Do milestones represent lifecycle stages or evidence gates?
- Are milestone dates omitted unless the user provided date pressure?
- Does each concrete issue produce one artifact?
- Can each issue be accepted or rejected from `Done When` alone?
- Does each issue have exactly one `Type/*` label when labels are available?
- Is uncertainty written into descriptions instead of hidden in labels?

