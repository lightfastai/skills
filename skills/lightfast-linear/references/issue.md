# Issue Reference

Use this reference when creating or updating Linear issues, sub-issues, issue labels, issue titles, or issue descriptions through Lightfast MCP.

Linear basis: Linear recommends writing short, simple issues in plain language instead of user stories. Issues should communicate the task clearly enough for the assignee to do the work and for teammates to understand what is happening.

Docs:

- https://linear.app/method/write-issues-not-user-stories
- https://linear.app/method/manage-design-projects
- https://linear.app/docs/projects
- https://linear.app/docs/project-milestones

## Issue Principle

Issues should be concrete, plain-language tasks. Prefer artifact-shaped issues when planning uncertain work: one issue usually produces one durable artifact, decision, prototype, evaluation, document, code change, design, or comparable object.

Avoid user-story boilerplate such as:

```text
As a <persona>, I want <feature>, so that <benefit>.
```

That format often hides the actual work. Name the task directly.

## When To Use An Issue

Use an issue when the work:

- Can be assigned, discussed, started, completed, or canceled as one unit.
- Produces a concrete task result or durable artifact.
- Belongs to one project or milestone.
- Has acceptance criteria that can be evaluated from the issue body.

Split into multiple issues or sub-issues when:

- Different people own separable parts.
- Design, engineering, research, or writing need distinct deliverables.
- The issue spans multiple projects; create project-specific sub-issues or sibling issues.
- The `Done When` section would need unrelated acceptance criteria.

## Issue Labels

Use one grouped label set when labels are available:

- `Type/Research`: creates evidence, comparison, synthesis, taxonomy, or structured understanding.
- `Type/Prototype`: creates runnable, inspectable, or interactive behavior.
- `Type/Evaluation`: scores, tests, audits, compares, or validates an artifact.
- `Type/Writing`: turns thinking into durable prose for others to use.
- `Type/Decision`: resolves a fork and records the rationale.

Rules:

- Give every issue exactly one `Type/*` label when labels are available.
- Do not add `Artifact`, `Theme`, or `Risk` labels by default.
- Put artifact, theme, and risk context in the title or body instead.
- Add new labels only when they power a real view, review ritual, automation, ownership rule, or recurring management decision.

## Issue Body

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

Good titles name the artifact or task and the action.

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

## Sub-Issues

Use sub-issues when a parent issue coordinates separable tasks:

- Keep the parent issue as the shared context or coordination artifact.
- Give each sub-issue a direct owner, deliverable, and `Done When` criteria.
- Use sub-issues for cross-functional handoff when design, engineering, research, or writing need different closure conditions.
- Avoid using sub-issues as a hidden backlog. If the sub-issue is optional or future-looking, capture it as a follow-up decision instead.

## Creation Workflow

When creating issues:

1. Identify the project, milestone, owner, labels, and immediate stage.
2. Discover existing labels and use available `Type/*` labels rather than inventing names.
3. Write direct task titles in plain language.
4. Keep each issue independently closeable.
5. Create only the issues needed for the current milestone or immediate execution stage.
6. Return created issue links and call out any follow-up issues intentionally deferred.
