# ML Platform — end-to-end production lifecycle

An end-to-end ML platform built as a full production loop, with a deliberately
swappable model. The engineering — not the model — is the point.

**The loop:** train → track → version → serve → containerize → CI/CD → deploy →
monitor → detect drift → retrain → safely roll out.

## Why this project

Every ML-adjacent role (AI engineer, ML engineer, ML systems, R&D) assumes you
can take a model to production and keep it healthy there. Almost no early-career
candidate can demonstrate the whole loop. This builds exactly that, and it's the
skeleton a real B2B/B2C product later slots into — swap the model, add a UI.

## How this repo is run

Built with a coding agent under a strict workflow: **the agent proposes, Rex
decides, decisions are recorded as ADRs, then the agent implements.** See
`CLAUDE.md`.

- `CLAUDE.md` — the working agreement (read first)
- `PROJECT_MAP.md` — repo index
- `CONTEXT.md` — current state snapshot
- `PROGRESS.md` — dated history
- `decisions/` — Architecture Decision Records (the "why" behind everything)
- `instructions/` — per-task briefs

## Phases

0. Scaffold · 1. Train+track+version · 2. Serve · 3. Containerize ·
4. CI/CD · 5. Deploy · 6. Monitor+drift · 7. Retrain loop · 8. Extensions

## Status

Phase 0, not started. Domain being chosen (see `decisions/ADR-0002`).
