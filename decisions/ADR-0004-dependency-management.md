# ADR-0004: Dependency and environment management

- **Status:** ACCEPTED
- **Date:** 2026-09-24
- **Decider:** Rex
- **Phase:** 0

## Context

With the repo structure settled (ADR-0003: monorepo, src/ layout), we need a
tool that manages three things in one coherent workflow:

1. Declares direct dependencies in pyproject.toml.
2. Resolves and pins every transitive dependency into a lockfile (so any
   machine reproduces the exact same environment from a fresh clone).
3. Creates and manages the virtual environment so the installed package and
   tests run in isolation.

The choice affects every developer setup, every CI run, and the onboarding
story for the whole project lifetime. Changing tools mid-project means
regenerating the lockfile and updating CI scripts.

## Options considered

### Option A -- uv
A dependency manager and venv tool written in Rust. Single command covers
init, add, sync, and run. Generates a uv.lock lockfile.
- Pros: 10-100x faster installs than pip; single tool for venv + deps +
  lockfile; fully pyproject.toml-native; rapidly becoming industry standard;
  excellent CI support.
- Cons: relatively new (2024); rare edge-case packages with complex builds can
  occasionally have issues.

### Option B -- poetry
Previous gold-standard. Manages dependencies, virtualenvs, and publishing.
Generates poetry.lock.
- Pros: battle-tested, large community, excellent docs, robust lockfile.
- Cons: noticeably slower than uv; some non-standard pyproject.toml extensions;
  industry visibly migrating toward uv.

### Option C -- pip-tools + venv
Minimal approach: requirements.in -> pip-compile -> requirements.txt lockfile,
plain venv managed manually.
- Pros: maximum transparency, no tool lock-in beyond pip.
- Cons: more manual steps, no pyproject.toml integration, more surface area for
  drift; no advantage for a greenfield project.

## Decision

Use uv for all dependency and environment management. The lockfile will be
uv.lock (committed to git). The venv is managed by uv. The editable install
(uv pip install -e .) is required before imports work, per the src/ layout
chosen in ADR-0003.

## Why

<!-- Rex writes below this line -->

It is a fast package manager (written in Rust, not built on pip -- it replaces
pip entirely) and is used in the industry. It also provides a single tool to
cover most or all of the dependency and environment management needs.

## Consequences

- Developers set up with: uv sync (creates venv + installs from uv.lock).
- Adding a dependency: uv add <package> (updates pyproject.toml + uv.lock).
- Running anything: uv run <command> or activate the venv first.
- CI will run uv sync --frozen to install from the lockfile without updating it.
- uv.lock is committed to git; it is never hand-edited.
- The src/ layout means uv pip install -e . (or uv sync) must be run before
  pytest can find the cfpb_mlops package.
