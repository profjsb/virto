# ADR 001: Orchestration Primitive

Date: 2025-10-01

## Status
Proposed

## Context
We need a predictable, observable way to coordinate many persona-driven agents.

## Decision
Adopt a graph/event-driven orchestration with a lightweight message bus abstraction. Meetings and hiring flows are explicit graph nodes.

## Consequences
+ Traceable runs, easier retries, clearer boundaries
- Slightly more upfront structure compared to pure chat loops
