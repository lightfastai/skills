---
name: lightfast-linear
description: General-purpose Linear planning and creation guidance for Lightfast MCP work. Use only when the user explicitly invokes $lightfast-linear and the task involves creating, updating, triaging, or planning Linear initiatives, projects, milestones, or issues through mcp__lightfast provider routines. Do not invoke implicitly and do not use for general Linear planning outside Lightfast MCP.
---

# Lightfast Linear

Use this skill only after the user explicitly invokes `$lightfast-linear` for Lightfast-driven Linear work. Shape Linear into a lightweight operating system: initiatives for strategic goals, projects for bounded outcomes, milestones for project stages, and issues for concrete tasks or artifacts.

## Operating Rule

When using `mcp__lightfast` with Linear:

1. Discover available Linear routines before assuming schemas or IDs.
2. Shape the initiative, project, milestone, or issue before calling a write routine.
3. Keep Linear structure lightweight enough to maintain.
4. Do not generate full future issue batches before the current stage has produced evidence.
5. Report what changed, including Linear links or IDs returned by the routine.

Skip this skill if the user did not explicitly invoke it, or if Lightfast MCP is not part of the task.

## Reference Routing

Read only the references needed for the requested Linear layer:

- `references/initiative.md`: Use for creating or updating initiatives, deciding initiative vs project, linking projects to initiatives, initiative descriptions, or initiative updates.
- `references/project.md`: Use for creating or updating projects, project briefs, project properties, project milestones, or deciding project vs issue.
- `references/issue.md`: Use for creating or updating issues, sub-issues, labels, issue titles, issue descriptions, or deciding how much work belongs in one issue.

When a request spans layers, read the references in hierarchy order: initiative, then project, then issue.

## Lightfast Routine Discovery

Before calling a Linear provider routine:

1. If needed, check availability with `mcp__lightfast.lightfast_system_health`.
2. Find available Linear routines with `mcp__lightfast.proxy_find` using `provider: "linear"` and `includeSchema: true`.
3. Select the routine that matches the requested operation.
4. Call the routine with the exact schema returned by Lightfast.
5. Report created or changed entities with Linear links or IDs.

Do not assume routine IDs, argument names, team IDs, initiative IDs, project IDs, milestone IDs, label IDs, or workspace configuration. Discover them through Lightfast or ask the user if discovery does not provide enough information.

## Core Model

Use this hierarchy:

- Initiative: workspace-level objective that manually groups projects around a strategic goal.
- Project: bounded outcome or deliverable with a planned completion path.
- Milestone: meaningful stage of completion inside a project.
- Issue: plain-language task or artifact-shaped unit of work.

Choose the lightest Linear layer that fits:

- Use an initiative when the work spans multiple projects, teams, or a long timeline and leadership needs progress context.
- Use a project when the work has one bounded outcome, owner, scope, and completion path.
- Use a milestone when a project needs visible stages, evidence gates, or release checkpoints.
- Use an issue when the work is a concrete task, artifact, decision, prototype, or code/design change.

Avoid using initiatives or projects for permanent ongoing areas. If the work is ongoing or dynamic, prefer smaller time-bounded projects, custom views, or maintenance-style projects only when that is explicitly the desired workflow.

## Planning Workflow

Before creating or updating Linear structure:

1. Identify the requested layer and read the matching reference file.
2. Extract the user's objective, audience, owner, teams, timeline, scope, constraints, and known links.
3. Decide whether the requested layer is too heavy or too light for the work.
4. Draft the Linear shape before writing: title, summary, description, properties, and relationships.
5. Discover Lightfast routines and required IDs.
6. Create or update the minimum useful structure.
7. Return a concise summary of the resulting hierarchy and any unresolved decisions.

## Review Checklist

Before creating or updating Linear structure, check:

- Is an initiative needed, or would a project or custom view be lighter?
- Does each initiative express a strategic objective rather than a folder or theme?
- Does each project have a bounded outcome?
- Does each project summary say what becomes true?
- Do milestones represent lifecycle stages or evidence gates?
- Are milestone dates omitted unless the user provided date pressure?
- Does each concrete issue describe a plain-language task or produce one artifact?
- Can each issue be accepted or rejected from `Done When` alone?
- Does each issue have exactly one `Type/*` label when labels are available?
- Is uncertainty written into descriptions instead of hidden in labels?
