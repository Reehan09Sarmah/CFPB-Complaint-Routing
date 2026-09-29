# ADR-0007: Data versioning

- **Status:** ACCEPTED
- **Date:** 2026-09-29
- **Decider:** Rex
- **Phase:** 1

## Context

The dataset is 3.5GB - too large for git. Without data versioning, we cannot
guarantee that a future retraining run uses the exact same data as a past run.
This matters most for Phases 6-7 (drift detection): we need to replay historical
data slices to prove drift is real. We need a tool that versions data files
alongside code commits.

## Options considered

### Option A - DVC (Data Version Control)
Works like git for large files. `dvc add data/complaints.csv` stores a
fingerprint in git and caches the file locally (or remotely). `dvc pull`
restores it on a fresh clone.
- Pros: purpose-built for ML data, integrates with git, supports remote storage,
  industry standard, enables genuine data reproducibility.
- Cons: one more tool to learn; adds a `.dvc` file per tracked file.

### Option B - MLflow Artifacts only
Log the data file path and hash inside each MLflow run. No separate versioning tool.
- Pros: zero extra tools.
- Cons: does not actually store or restore the data. Cannot replay historical
  data slices. Insufficient for Phases 6-7.

## Decision

DVC, with a local cache for now. Remote storage (e.g. S3 or GDrive) can be
added later when we reach deployment phases.

## Why

DVC because I want to learn it as a practical skill. Also, we want full
reproducibility of our model using the original dataset - if the CSV ever
changes, we can always restore the exact version the model was trained on.

## Consequences

- `data/complaints.csv` is tracked by DVC, not git. The `.dvc` file IS committed.
- `data/` is added to `.gitignore`; `data/*.csv` must not be committed directly.
- `dvc pull` on a fresh clone restores the data from cache.
- Future data updates (e.g. a newer CFPB export) become a new DVC version.
- DVC pipeline stages (dvc.yaml) will be added in Phase 1 to make preprocessing reproducible.