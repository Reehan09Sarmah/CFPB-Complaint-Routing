# ADR-0005: Tooling baseline (formatter, linter, type checker, pre-commit)

- **Status:** ACCEPTED
- **Date:** 2026-09-24
- **Decider:** Rex
- **Phase:** 0

## Context

With repo structure (ADR-0003) and dependency management (ADR-0004) settled,
we need a quality-gate baseline: tools that run automatically to enforce
consistent style, catch code smells, and surface type errors before they
become runtime bugs. These run locally on every commit (via pre-commit hooks)
and again in CI. The goal is to set the standard once in Phase 0 and never
think about it again.

Four categories: formatter (style consistency), linter (code smells), type
checker (type safety), and pre-commit (runs the above automatically on commit).
pytest is the test runner -- not a decision, confirmed here.

## Options considered

### Formatter + Linter

#### Option A -- ruff (does both formatting and linting)
Single tool written in Rust. Replaces black + flake8 + isort.
- Pros: one tool, one config block in pyproject.toml; faster than black + flake8
  combined; no conflicts between formatter and linter; industry standard as of 2024.
- Cons: newer, so some older tutorials show the three-tool stack instead.

#### Option B -- black + flake8 + isort (older three-tool stack)
- Pros: familiar to developers who learned Python pre-2023.
- Cons: three tools to configure; occasional conflicts between them; slower;
  no meaningful advantage for a new project today.

### Type Checker

#### Option A -- mypy
The original Python type checker. Reads type annotations and flags mismatches.
- Pros: well-documented; large community; gradual typing (annotate some things,
  ignore others); every tutorial and book uses it.
- Cons: slower on large codebases; config can be fiddly.

#### Option B -- pyright
Microsoft's type checker, same engine as VS Code Pylance.
- Pros: faster; stricter.
- Cons: stricter defaults cause more false positives when starting out; less
  learning material than mypy.

#### Option C -- skip type checking, add later
- Pros: less friction immediately.
- Cons: retrofitting annotations onto existing code is painful; better to build
  the habit from the first line.

## Decision

- Formatter + linter: ruff (format + check), configured in pyproject.toml.
- Type checker: mypy, run via pre-commit and CI.
- Pre-commit: yes -- runs ruff format, ruff check, mypy on every git commit.
- Test runner: pytest (confirmed, not a decision).

## Why

<!-- Rex writes below this line -->

ruff + mypy because ruff covers the job of two tools with better proficiency
and mypy is the basic tool that would help me learn immensely for this basic
project.

## Consequences

- pyproject.toml will have [tool.ruff] and [tool.mypy] config sections.
- .pre-commit-config.yaml will run: ruff format, ruff check --fix, mypy.
- A commit that fails any of these is rejected locally before it reaches CI.
- Strictness starts permissive (mypy non-strict mode); can be tightened later
  without changing the tool.
- All three tools are added as dev dependencies via: uv add --dev ruff mypy pre-commit pytest.
