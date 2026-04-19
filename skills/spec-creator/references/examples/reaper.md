# Reaper Service Specification

Status: Draft v1 (language-agnostic)

Purpose: Define a service that monitors deployments and rolls back failed releases automatically.

## 1. Problem Statement

Reaper is a long-running automation service that watches deployment pipelines, detects failures
using health checks, and triggers automatic rollbacks when thresholds are breached.

The service solves three operational problems:

- It replaces manual rollback decisions with configurable automated health evaluation.
- It isolates rollback execution per deployment so concurrent releases do not interfere.
- It keeps rollback policy in-repo (`ROLLBACK.md`) so teams version their thresholds and
  recovery steps with their code.

Important boundary:

- Reaper is a monitor and rollback executor.
- Deployment triggering and promotion logic live outside this service.
- A successful rollback ends at a policy-defined stable state, not necessarily the prior version.

## 2. Goals and Non-Goals

### 2.1 Goals

- Poll deployment status on a fixed cadence with bounded concurrency.
- Maintain a single authoritative state for active monitors, rollback decisions, and cooldowns.
- Evaluate health checks against configurable thresholds before triggering rollback.
- Support multiple deployment targets with per-target rollback policies.
- Recover from transient health-check failures with exponential backoff.
- Load rollback behavior from a repository-owned `ROLLBACK.md` contract.
- Expose operator-visible observability (at minimum structured logs).

### 2.2 Non-Goals

- Deployment orchestration or promotion pipelines.
- Rich web UI or multi-tenant control plane.
- General-purpose monitoring or alerting system.
- Built-in business logic for notification routing. (That logic lives in the rollback policy
  and external integrations.)

## 3. System Overview

### 3.1 Main Components

1. `Policy Loader`
   - Reads `ROLLBACK.md`.
   - Parses YAML front matter and policy body.
   - Returns `{config, policy_template}`.

2. `Config Layer`
   - Exposes typed getters for policy config values.
   - Applies defaults and environment variable indirection.

3. `Deployment Client`
   - Fetches active deployments from the deployment platform.
   - Fetches health metrics for specific deployments.
   - Normalizes platform payloads into a stable deployment model.

4. `Monitor`
   - Owns the poll tick.
   - Owns the in-memory runtime state.
   - Decides which deployments to watch, evaluate, rollback, or release.

5. `Rollback Executor`
   - Builds rollback command from deployment context and policy template.
   - Executes rollback as a subprocess.
   - Reports outcome back to the monitor.

6. `Logging`
   - Emits structured runtime logs to one or more configured sinks.

### 3.2 External Dependencies

- Deployment platform API (for example Kubernetes, Vercel, or custom).
- Health-check endpoint or metrics source.
- Rollback tooling accessible from the host environment.
- Host environment authentication for the deployment platform.

## 4. Core Domain Model

### 4.1 Entities

#### 4.1.1 Deployment

Normalized deployment record used by monitoring and rollback.

Fields:

- `id` (string)
  - Stable platform-internal ID.
- `name` (string)
  - Human-readable deployment identifier.
- `status` (string)
  - Current platform status.
- `health_score` (float, 0.0-1.0, or null)
  - Latest evaluated health metric.
- `created_at` (timestamp or null)

#### 4.1.2 Rollback Policy

Parsed `ROLLBACK.md` payload:

- `config` (map)
  - YAML front matter root object.
- `policy_template` (string)
  - Markdown body after front matter, trimmed.
