# PROJECT_MAP.md

The index of this repository. The agent reads this first to know where things
live, so it loads only what a task needs. Keep it current: if you add, move, or
remove something that matters, update this file in the same task.

---

## Workflow / context files (root)

| File            | Purpose                                                      |
|-----------------|-------------------------------------------------------------|
| `AGENTS.md`     | **Canonical.** How we work together, incl. multi-agent handoff protocol. Read every session, whichever tool is running. |
| `CLAUDE.md`, `GEMINI.md`, `AGENT.md` | Thin pointer files, one per tool's expected filename. Content lives only in `AGENTS.md`. |
| `PROJECT_MAP.md`| This file. The repo index.                                  |
| `CONTEXT.md`    | Current state of the world (a snapshot).                    |
| `PROGRESS.md`   | Append-only dated log of what's been done (notes which agent did it). |
| `README.md`     | Human-facing overview of the project.                       |
| `decisions/`    | Architecture Decision Records (ADRs). Source of truth.      |
| `instructions/` | Per-task briefs Rex writes before handing off a task.       |

---

## Code layout

> NOT YET DECIDED. The repo structure (monorepo vs multi-service, package
> layout, dependency manager) is Phase 0's job and is Rex's decision — see
> `instructions/task-0001-scaffold.md`. Fill this section in as Phase 0 lands.

<!--
As modules appear, list them here, e.g.:

| Path              | What it is                                    | Read when...            |
|-------------------|-----------------------------------------------|-------------------------|
| `src/training/`   | Model training + experiment tracking          | working on Phase 1      |
| `src/serving/`    | FastAPI prediction service                     | working on Phase 2      |
| `deploy/`         | Docker, CI/CD, infra                            | working on Phases 3–5   |
| `monitoring/`     | Prometheus/Grafana/drift config                | working on Phases 6–7   |
-->

---

## The phase plan (where we are in the big picture)

- [ ] **Phase 0** — Scaffold: repo, context files, packaging, test skeleton.
- [ ] **Phase 1** — Train + track (MLflow) + version data (DVC) + registry.
- [ ] **Phase 2** — Serve: FastAPI prediction service.
- [ ] **Phase 3** — Containerize: Docker.
- [ ] **Phase 4** — CI/CD: GitHub Actions.
- [ ] **Phase 5** — Deploy to real infra.
- [ ] **Phase 6** — Monitor + detect drift.
- [ ] **Phase 7** — Close the loop: retrain + safe rollout.
- [ ] **Phase 8** — Open-ended extensions.

Check a box only when that phase runs end-to-end, even if crudely.
