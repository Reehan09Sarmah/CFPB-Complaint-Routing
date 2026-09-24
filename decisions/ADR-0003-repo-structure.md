# ADR-0003: Repo structure and package layout

- **Status:** ACCEPTED
- **Date:** 2026-09-24
- **Decider:** Rex
- **Phase:** 0

## Context

Phase 0 requires establishing a folder structure before any code is written.
The structure shapes how every downstream phase (training, serving, monitoring,
CI/CD) imports code, how Docker locates build context, and how the test runner
discovers tests. Changing it after multiple phases are built is expensive -
every import path, Dockerfile, and CI config would need updating. It must be
decided now, while the repo is empty.

Constraints: solo developer, learning project, the goal is to build and observe
the entire ML lifecycle (train -> serve -> monitor -> retrain) in one coherent
loop - not to isolate independent teams.

## Options considered

### Option A -- Monorepo, src/ layout (one package, all phases inside)

```
mlops-platform/
  src/
    cfpb_mlops/
      training/
      serving/
      monitoring/
  tests/
  pyproject.toml
```

- Pros: single repo, single lockfile, atomic commits across phases; src/ layout
  prevents Python from accidentally importing source instead of the installed
  package; one CI pipeline; easy cross-phase imports.
- Cons: production containers bundle all phases even when only one is needed at
  runtime (negligible overhead at this scale); does not scale to fully
  independent teams with separate release cadences (not a concern here).

### Option B -- Monorepo, flat layout (no src/, folders at root)

```
mlops-platform/
  training/
  serving/
  monitoring/
  tests/
  pyproject.toml
```

- Pros: visually simpler; one fewer directory level.
- Cons: Python can import from the working directory before the installed
  package, masking real import errors until production; subtler to reason
  about during pytest.

### Option C -- Polyrepo (separate git repo per service)

- Pros: each service can be released, versioned, and CI'd independently;
  mirrors how large companies isolate teams.
- Cons: for a solo learning project, the coordination overhead (three sets of
  configs, three CIs, shared-utility duplication) is pure friction with no
  benefit; hard to make atomic changes that span training and serving.

## Decision

Monorepo with src/ layout (Option A). All phases live inside one git
repository under src/cfpb_mlops/, installed as a single editable package.

## Why

<!-- Rex writes below this line -->

Option A felt the sane option to select as it is what I have been doing since
forever. Also, this project is solo - a learning project of mine; I have
nothing to hide and no reason to use polyrepo. It is a small project and the
cost of bundling them together in production containers is negligible.

## Consequences

- All phases import from cfpb_mlops.* - consistent, predictable namespace.
- A single pyproject.toml + lockfile governs the whole project (ADR-0004 will
  decide which tool manages it).
- Docker build contexts will point at the repo root and install the package;
  per-service images can be created by varying the entry point, not the layout.
- The src/ layout means the package must be installed (even in editable mode:
  pip install -e .) before imports work - this is enforced in ADR-0004.
- If the project ever grows to need independent team releases, this decision
  would need to be superseded. Flag it in PROGRESS.md if that moment comes.
