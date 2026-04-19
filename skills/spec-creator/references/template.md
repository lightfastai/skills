# {Service Name} Specification

Status: Draft v1 (language-agnostic)

Purpose: {One sentence — what this service does.}

## 1. Problem Statement

{Service Name} is a long-running automation service that {core verb phrase describing the main loop}.

The service solves {N} operational problems:

- {Problem 1: what manual/broken process it replaces.}
- {Problem 2: what isolation or safety property it provides.}
- {Problem 3: what versioning or configuration benefit it adds.}

Important boundary:

- {Service Name} is a {role description — what it IS}.
- {What it is NOT — what adjacent concerns live elsewhere.}
- A successful run may end at {handoff condition}, not necessarily {naive completion state}.

## 2. Goals and Non-Goals

### 2.1 Goals

- {Verb-led phrase. Specific enough to test.}
- {Each goal is one bullet.}

### 2.2 Non-Goals

- {Noun/gerund phrase. Clarifies scope boundary.}
- {Parenthetical context when useful: "(That logic lives in {X}.)" }

## 3. System Overview

### 3.1 Main Components

1. `{Component Name}`
   - {Verb-led sentence: what it does.}
   - {Second sentence if needed for scope.}

2. `{Component Name}`
   - {Description.}

### 3.2 Abstraction Levels

{Service Name} is easiest to port when kept in these layers:

1. `Policy Layer` (repo-defined)
   - {What the team owns and versions.}

2. `Configuration Layer` (typed getters)
   - {What the config system provides.}

3. `Coordination Layer` (orchestrator)
   - {Core scheduling and state management.}

4. `Execution Layer` ({execution unit})
   - {Filesystem, subprocess, or external call lifecycle.}

5. `Integration Layer` ({adapter name})
   - {External API interaction and normalization.}

6. `Observability Layer` (logs + optional surfaces)
   - {Operator visibility.}

### 3.3 External Dependencies

- {External API or service.}
- {Filesystem or storage.}
- {Tooling or executables.}
- {Authentication requirements.}

## 4. Core Domain Model

### 4.1 Entities

#### 4.1.1 {Entity Name}

{One sentence: what this entity represents and where it is used.}

Fields:

- `field_name` (type)
  - {Semantic description.}
- `field_name` (type, constraints)
  - {Description.}
  - Default: `value`
