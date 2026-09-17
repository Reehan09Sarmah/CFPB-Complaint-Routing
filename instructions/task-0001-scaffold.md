# task-0001: Phase 0 — repo scaffold

## Goal
A clean, reproducible Python project skeleton that everything else is built on:
package layout, dependency management, formatting/linting, a test skeleton that
runs, and a `.gitignore` that keeps secrets and data out of git. No ML code yet.

## Why / context
Phase 0. Everything downstream (training, serving, deploy) assumes a sane,
reproducible base. Getting this right once prevents "works on my machine" later.

## Read first
- `CLAUDE.md` (workflow rules)
- `PROJECT_MAP.md`
- `decisions/ADR-0002-domain-and-dataset.md` (must be ACCEPTED before starting —
  the domain shapes some naming)

## Decisions expected in this task
The agent must STOP and surface options for each of these — do NOT decide them:

1. **ADR-0003 — repo structure.** Monorepo (all layers in one repo, one package)
   vs multi-service (separate services). Package/folder layout.
2. **ADR-0004 — dependency + environment management.** e.g. `uv` vs `poetry` vs
   `pip-tools` + venv. Consider reproducibility, speed, lockfiles.
3. **ADR-0005 — tooling baseline.** Formatter/linter (e.g. ruff, black), type
   checker (mypy?), test runner (pytest), pre-commit hooks. Which, and how strict.

For each: present 2–3 options with trade-offs, recommend one, wait for Rex.

## Out of scope / do not touch
- No model, training, serving, Docker, or CI code yet — later phases.
- Do not download the dataset yet (a later task handles data with a size
  decision). A tiny sample for wiring tests is OK if Rex approves.

## Definition of done
- [ ] Repo structure created per ADR-0003
- [ ] Environment reproducible from a lockfile per ADR-0004 (a fresh clone can
      install and run)
- [ ] `pytest` runs and one trivial test passes
- [ ] Formatter/linter/pre-commit configured per ADR-0005
- [ ] `.gitignore` excludes data/, secrets, model artifacts, caches
- [ ] ADR-0003, 0004, 0005 written and ACCEPTED
- [ ] PROGRESS.md / CONTEXT.md / PROJECT_MAP.md updated (fill in the code-layout
      section of the map)
