# PROJECT_MAP.md

Repo index. Tells you where things live and, for anything non-obvious, what it
actually does and why. Read this every session (AGENTS.md ritual, step 1) —
then read only the specific files your task touches.

This file is detailed on purpose: it is the place every future agent (Claude
Code, OpenCode, Antigravity, whichever) reads BEFORE writing new code, so
nobody re-derives or silently re-decides something that's already settled.
If you change what a file does, update its entry here in the same session.

---

## Top-level layout

```
mlops-platform/                        <- the git repo root (and uv project)
├── AGENTS.md                          <- canonical workflow rules (read first, always)
├── GEMINI.md                          <- thin pointer to AGENTS.md (CLAUDE.md/AGENT.md: not created)
├── CONTEXT.md                         <- current state snapshot (short, overwritten)
├── PROGRESS.md                        <- append-only dated history
├── PROJECT_MAP.md                     <- this file
├── README.md                          <- one-page pitch of the project
├── decisions/                         <- ADRs, one file per decision
├── src/cfpb_mlops/                    <- installable Python package
├── tests/                             <- pytest suite
├── notebooks/train_colab.ipynb        <- Colab runner: clones repo, reads CSV from Drive, calls train()
├── data/                              <- DVC-tracked dataset (gitignored CSV, tracked .dvc file)
├── .dvc/                              <- DVC's own config + local cache
├── pyproject.toml, uv.lock            <- dependency + tool config
└── .pre-commit-config.yaml            <- git hook config (ruff, mypy on commit)
```

**Note on paths:** as of 2026-10-10 the agent-context files live INSIDE the
repo, so git history is the handoff. (A stale pre-move `README.md` may remain
in the outer `CFPB Consumer Complaint/` folder; ignore it.)
---

## `decisions/` — ADRs (source of truth for every engineering choice)

| ADR | Decision | Status |
|---|---|---|
| ADR-0001 | Agent context system (this file system itself) | ACCEPTED |
| ADR-0002 | Domain/dataset = CFPB Consumer Complaint Database | ACCEPTED |
| ADR-0003 | Repo structure = monorepo, `src/` layout | ACCEPTED |
| ADR-0004 | Dependency manager = uv | ACCEPTED |
| ADR-0005 | Tooling baseline = ruff + mypy + pre-commit + pytest | ACCEPTED |
| ADR-0006 | Experiment tracking = MLflow, local file-store | ACCEPTED |
| ADR-0007 | Data versioning = DVC, local cache | ACCEPTED |
| ADR-0008 | Baseline model = TF-IDF + Logistic Regression | ACCEPTED |
| ADR-0009 | Renamed CFPB labels: crosswalk to 2023 taxonomy + 2017-04-24 date floor + fail on unknown label | ACCEPTED |
| ADR-0010 | Best model = rank by macro-F2, gated by per-class recall floors and a critical-class review-queue budget | ACCEPTED |

Each ADR has a Context / Options / Decision / **Why** (Rex's own words) /
Consequences. The Why is never written by an agent — see AGENTS.md.

Note: ADR-0008 was written retroactively — the model choice had already been
implemented in code by a previous session without going through the decision
loop. Caught during this session's file review, walked through the loop
after the fact, Rex confirmed the choice and gave the Why himself.

---

## `src/cfpb_mlops/` — the installable package

### `training/train.py` — the training pipeline (Phase 1)

Full mechanics, step by step, because this is the file most likely to be
extended next:

1. **`load_data(path, sample_n)`** — reads `data/complaints.csv` with
   `pandas.read_csv`, loading only 3 columns (`Date received`,
   `Consumer complaint narrative`, `Product`) instead of all ~18 columns —
   keeps memory use down on a 3.5GB file. Drops every row where the
   narrative column is null (per ADR context: narrative is opt-in, so most
   of the 5.5M rows don't have one — only ~1.9M do, and those are the only
   usable rows for a text classifier). If `sample_n` is set, it sorts by
   date and takes the most recent N rows, rather than a random sample —
   this keeps the sample date-contiguous, which matters for the time split
   below.

2. **`preprocess(df)`** — lowercases and strips whitespace on the narrative
   text. Nothing else. TF-IDF (next step) does most of the real work, so
   this is deliberately minimal — no stemming, no stopword removal, no
   punctuation stripping yet.

3. **`time_split(df, test_months)`** — splits into train/test **by date**,
   not randomly: everything up to `(max_date − test_months)` is train,
   everything after is test. This exists because a random split would leak
   future complaints into training and make accuracy look better than it
   would be in real deployment, where you always predict on complaints that
   haven't happened yet. Default holds out the most recent 6 months.

4. **`build_pipeline(max_features, C)`** — an sklearn `Pipeline` with two
   steps chained together:
   - `TfidfVectorizer`: turns raw text into numeric vectors. `max_features`
     caps vocabulary size; `ngram_range=(1,2)` keeps both single words and
     two-word phrases; `min_df=5` drops words seen in fewer than 5
     complaints (cuts noise/typos); `sublinear_tf=True` applies
     `log(1+count)` so a word appearing 100 times doesn't dominate a word
     appearing 10 times.
   - `LogisticRegression`: a linear classifier. `C` is inverse
     regularization strength (higher = fits training data more tightly,
     more overfitting risk). `class_weight="balanced"` auto-corrects for
     the fact that "Credit card" complaints vastly outnumber some other
     product categories — without it the model could just predict the
     majority class and look accurate while being useless.

5b. **`diagnostics(pipeline, X_test, y_test, y_train)`** - per-class report, confusion matrix, and the majority-class baseline accuracy. `train()` logs them as MLflow artifacts under `diagnostics/` plus `baseline_accuracy` and data-size/date params.

5. **`evaluate(pipeline, X_test, y_test)`** — computes `accuracy` and
   `f1_macro`. Macro-F1 (not micro/weighted) is used because it averages
   the score across classes equally regardless of size — this matters
   because the product categories are imbalanced (see step 4).

6. **`train(...)`** — orchestrates all of the above inside
   `mlflow.start_run()`. Logs hyperparameters (`log_params`), logs the two
   metrics (`log_metrics`), and logs the trained pipeline itself as an
   artifact (`mlflow.sklearn.log_model`). If `register_model=True`, also
   registers it in the MLflow model registry under the name
   `cfpb-complaint-classifier`. **Not yet implemented:** the ADR-0006
   promise that a model is "only pushed to production when it beats the
   current champion" — right now `--register` always registers
   unconditionally. That comparison logic is a Phase 1 TODO.

7. **CLI (`if __name__ == "__main__"`)** — run via
   `uv run python -m cfpb_mlops.training.train --sample-n 50000`. Defaults
   to a 50k-row sample so local runs are fast; pass `--sample-n` with no
   value semantics changed (None = full dataset) only via code, not CLI
   flag currently (argparse default is `50_000`, not `None`).

Model choice (TF-IDF + LogReg) was originally implemented without going
through Rex first — retroactively covered by ADR-0008 (baseline, chosen
because every real model needs something simple to be measured against).
Split strategy (time-based) and metric choice (macro-F1, for class balance)
are implementation details consistent with the project's known constraints
in CONTEXT.md, not separately ADR'd.

### `serving/__init__.py`, `monitoring/__init__.py`

Empty placeholder packages for Phase 2 (FastAPI serving) and Phase 6 (drift
detection). Nothing implemented yet.

---

## `tests/` — pytest suite

### `test_smoke.py` — package smoke test

Two trivial tests: (1) `import cfpb_mlops` succeeds, (2) `1 + 1 == 2`. See
"What is a smoke test" below.

### `test_training.py` — training pipeline smoke tests

Four tests, all against a 10-row **fake** in-memory DataFrame (never touches
the real 3.5GB CSV, so it runs in ~seconds, not minutes):
- `test_preprocess_lowercases` — confirms `preprocess()` actually lowercases.
- `test_time_split_respects_cutoff` — confirms no date overlap between train
  and test after `time_split()`.
- `test_pipeline_trains_and_predicts` — fits `build_pipeline()` on the fake
  data and checks predictions come back as valid product labels, with no
  crash.
- `test_evaluate_returns_expected_keys` — confirms `evaluate()` always
  returns both `accuracy` and `f1_macro`, each in `[0, 1]`.

**Status: verified passing** (`uv run pytest tests/test_training.py -q` →
4 passed, run this session). One harmless `FutureWarning`: sklearn is
deprecating `n_jobs` on `LogisticRegression` in a future version — not
urgent, note for later cleanup.

### What is a smoke test?

A smoke test is the cheapest possible test that answers one question: **"did
I wire this together correctly, at all?"** — not "is the model good," not
"is the accuracy high enough," just "does the code run end-to-end without
crashing and produce output shaped the way I expect." The name comes from
hardware testing: power on a circuit and check smoke doesn't come out: if it
survives that, you can move on to real testing.

Why fake data instead of the real CSV: a smoke test's whole value is being
**fast and cheap to run constantly** (every commit, every pre-commit hook).
If it loaded the real 3.5GB file, it would take minutes and require the
dataset to be present locally — that defeats the purpose. Fake data proves
the *pipeline plumbing* works (does `time_split` actually split by time, does
the sklearn `Pipeline` actually fit and predict) without proving anything
about model *quality* on real complaints. Model quality gets checked
separately, later, via the actual MLflow metrics from real training runs —
that's a different kind of test (evaluation, not smoke).

---

## `data/` — dataset (DVC-tracked, not git-tracked)

| File | What it is |
|---|---|
| `data/complaints.csv` | The actual 3.5GB CSV, ~5.5M rows, ~1.9M with narratives. **Gitignored.** Lives only on disk + in DVC's local cache (`.dvc/cache/`). |
| `data/complaints.csv.dvc` | Small text file DVC generates: records the file's MD5 hash (`23d4a2b76e64894780340e4a5e5a5bfd`) and size (3,726,621,842 bytes). **This IS committed to git** — it's the fingerprint that lets anyone reproduce exactly this dataset via `dvc pull`, per ADR-0007. |
| `data/.gitignore` | Auto-generated by DVC (`dvc add`) to exclude `complaints.csv` from git while letting `complaints.csv.dvc` through. Don't hand-edit; DVC manages it. |

Verified this session: `dvc add` has actually been run (the `.dvc` file
contains a real hash, not a stub), so this ADR-0007 implementation is
complete and functional, just not yet committed to git.

---

## `.dvc/` — DVC's own config

`config` — currently empty (no remote storage configured yet; ADR-0007 says
remote storage is deferred to a later phase). `.gitignore` — excludes DVC's
local cache/tmp dirs from git (`/cache`, `/tmp`, `/config.local`).
`.dvcignore` — empty template, no patterns needed yet.

---

## Root config files

| File | What changed / what it does |
|---|---|
| `pyproject.toml` | Added `dvc`, `mlflow`, `scikit-learn` to `dependencies`. Added `-p no:hydra` to pytest's `addopts` — disables a pytest plugin named `hydra-core` that MLflow's dependency tree pulls in and that otherwise interferes with test collection. |
| `uv.lock` | Regenerated lockfile reflecting the above (uv's equivalent of `package-lock.json` — pins exact resolved versions for reproducible installs). |
| `.gitignore` | Rewrote the data section: previously blanket-ignored `data/` and `*.csv`; now only ignores the specific artifact types DVC/MLflow produce (`models/`, `*.parquet`, `mlruns/`, `*.pkl`, `*.joblib`), because `data/complaints.csv.dvc` now needs to be committed and a blanket `data/` ignore would have swallowed it too. |

---

## Verification performed this session (2026-09-29)

- `data/complaints.csv.dvc` confirmed real (actual MD5 + size, not a stub) —
  DVC tracking is functional, not just scaffolded.
- `uv run pytest tests/test_training.py -q` → **4 passed**. Training pipeline
  code is functional against fake data (not yet run against the real CSV).
- `pyproject.toml` / `uv.lock` diffs reviewed — dependency additions are
  consistent with ADR-0006 (mlflow) and ADR-0007 (dvc).
- `.gitignore` diff reviewed — consistent with DVC needing `.dvc` files
  committed while the CSV itself stays out of git.
- **Conclusion: all currently-uncommitted files are complete and working**,
  not half-finished. Nothing here blocks a commit on functional grounds.
  The only open item is the undocumented model-choice decision flagged
  above.


## Update 2026-10-11 (ADR-0009 / ADR-0010 implemented)
- `train.py`: `normalize_labels()` (date floor, crosswalk, card split by Sub-product, `ValueError` on unknown label) runs per chunk inside `load_data` (which now also reads `Sub-product`). `evaluate()` adds `f2_macro`. `pr_curves()` saves per-class cutoff/precision/recall at recall levels 0..1 to `diagnostics/pr_curves.json`. `train_min_date` is logged as a param.
- `tests/test_training.py`: 10 tests, now including the crosswalk, the unknown-label failure, `load_data` end to end, and `pr_curves`.
- Numeric floors, the queue budget and the critical-class list are NOT set yet (ADR-0010 defers them to baseline v2); they will live in a config file.
