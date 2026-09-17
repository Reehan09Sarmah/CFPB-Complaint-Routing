# ADR-0001: Agent context system (markdown files + ADR log, no knowledge graph)

- **Status:** ACCEPTED
- **Date:** 2026-09-17
- **Decider:** Rex
- **Phase:** 0

## Context

This project is built primarily with a coding agent (Claude Code), across many
sessions. The agent needs persistent memory of project state and past decisions
so it doesn't drift, re-litigate settled choices, or touch things it shouldn't.
It also needs to stay cheap on context/tokens. A knowledge graph was considered
as the memory mechanism.

## Options considered

### Option A — Structured markdown: PROJECT_MAP + CONTEXT + PROGRESS + ADR log
- Pros: industry-standard (ADRs are a real professional practice); doubles as
  Rex's learning record and interview script; zero maintenance overhead beyond
  writing prose; token-efficient via a map file + selective reading.
- Cons: manual discipline required to keep files current.

### Option B — Knowledge graph for agent memory
- Pros: structured queryable relationships; sounds sophisticated.
- Cons: solves a problem this project doesn't have (the bottleneck is agent
  drift/scope, not token cost or relational queries); adds schema + extraction +
  sync burden; becomes a second project competing with the real one.

## Decision

Use structured markdown with an ADR log (Option A). No knowledge graph as
project plumbing.

## Why

At solo-project scale the real risk is the agent making silent decisions and
wandering, not token spend. A map file plus selective reading handles cost; an
ADR log handles "why is it this way — don't change it" better than a KG would,
and it does triple duty as Rex's learning trail and interview material. A
knowledge graph's cost (maintenance, sync) buys nothing the markdown system
doesn't already provide here.

## Consequences

- Every decision Rex makes becomes one ADR — this is the mechanism that enforces
  "decisions go through Rex."
- If a knowledge-graph / GraphRAG capability is wanted later, it should be built
  as its own resume project, not retrofitted as plumbing here.
- Requires discipline: PROGRESS/CONTEXT/MAP updated at the end of each task.
