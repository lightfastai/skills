# Log Shipper Specification

Status: Draft v1 (language-agnostic)

Purpose: Tail application log files and forward structured events to a downstream sink.

## 1. Problem Statement

Log Shipper is a long-running automation service that watches a configured set of log files, parses each new line into a structured event, and forwards events to a remote collector.

The service solves three operational problems:

- It replaces ad-hoc cron jobs and tail pipes with a single managed forwarder.
- It isolates log parsing per file so a malformed line in one file does not stall others.
- It keeps parsing rules in-repo (`SHIPPER.md`) so teams version their schema with their code.

Important boundary:

- Log Shipper is a forwarder.
- Log retention, indexing, and query live in the downstream collector.
- A successful run may end at sink-acknowledged delivery, not necessarily durable storage.

## 2. Goals and Non-Goals

### 2.1 Goals

- Tail configured log files and emit one event per new line.
- Parse each line against a per-file rule set before emission.
- Recover from transient sink failures with bounded retry.
- Persist a per-file read offset so restarts do not duplicate or drop events.

### 2.2 Non-Goals

- Downstream storage, indexing, or query. (Handled by the collector.)
- Log rotation or archival.

## 3. System Overview

### 3.1 Main Components

1. `File Watcher`
   - Observes configured paths for new lines.
   - Emits raw line events.

2. `Parser`
   - Applies per-file parse rules.
   - Produces structured events.

3. `Forwarder`
   - Batches events and posts to the sink.
