# ADR-0006: Experiment tracking

- **Status:** ACCEPTED
- **Date:** 2026-09-29
- **Decider:** Rex
- **Phase:** 1

## Context

Every training run produces metrics (accuracy, F1) and a model artifact.
Without tracking, there is no way to compare runs, reproduce a result, or know
which model version is in production and why it was promoted. We need a tool
that logs parameters, metrics, and model artifacts automatically on every run
and provides a model registry for promoting versions to production.

## Options considered

### Option A - MLflow (local, self-hosted)
Open-source. Runs a local server. Logs params, metrics, artifacts. Has a
built-in model registry.
- Pros: free, offline, no accounts, industry standard, native scikit-learn
  integration, built-in model registry.
- Cons: you run the server yourself (one command).

### Option B - Weights and Biases (hosted SaaS)
- Pros: polished UI, zero server management.
- Cons: requires account and internet, data on their servers, external dependency.

### Option C - Plain logs + CSV
- Cons: no artifact storage, no model registry, no comparison UI. Not a real solution.

## Decision

MLflow, running locally. All runs stored in `mlruns/` inside the repo (gitignored).
Model registry also in MLflow. Promotion decision: a new model is only pushed to
production when it beats the current champion on the held-out test set, verified locally.

## Why

MLflow because it is open source - no certain accounts are needed - we only push
a model to production when it is better than the previous which we check locally.
Also, it is an industry standard - an easy to use system that tracks the entire
lifecycle.

## Consequences

- `mlflow server` must be running locally during training (or use the file-store
  backend, which needs no server at all - default for this project).
- `mlruns/` is gitignored. Only the ADR records which MLflow run ID was promoted.
- Model registry lives in the same MLflow instance.
- Training script always calls `mlflow.start_run()` - no bare training runs.