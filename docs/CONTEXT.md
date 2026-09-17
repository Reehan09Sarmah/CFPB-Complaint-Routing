# CONTEXT.md

A short SNAPSHOT of the current state of the world. This is not a history —
history lives in `PROGRESS.md`. Keep this file tight; update the lines that
change, don't append.

---

## Where we are

- **Last session:** setup only (Claude, chat) — no agent-driven work session
  has run yet.
- **Phase:** 0 (scaffold) — not started.
- **Domain/dataset:** NOT CHOSEN. See `decisions/ADR-0002-domain-and-dataset.md`
  (status: PROPOSED, awaiting Rex).
- **What's running:** nothing yet.
- **Repo structure:** not yet created (Phase 0 decision).

## One-paragraph architecture (fill in as it takes shape)

> Nothing built yet. After Phase 0/1 this should describe, in a few sentences,
> how the pieces fit: what trains the model, where the model is stored, what
> serves it, how it's deployed, how it's monitored.

## Open decisions pending Rex

1. **ADR-0002** — domain + dataset (choose from the shortlist in that ADR).
2. **ADR-0003** — repo structure + dependency manager (Phase 0).

## Known constraints / preferences

- Real data only — no synthetic data generation.
- Dataset must be timestamped so drift/retraining phases are genuine.
- One tool per layer; whole loop working before deepening any single part.
- Every engineering decision goes through Rex (see CLAUDE.md).
