# PROGRESS.md

Append-only, dated log of what's been done and what's next. Newest entries at
the bottom. Never edit past entries — only append. This is the project's memory;
`CONTEXT.md` is the current snapshot, this is the history.

Format per entry:
```
## YYYY-MM-DD — <short title>
- Agent: <tool + model used this session, e.g. "Claude Code (Sonnet)",
  "OpenCode (Musa Spark 1.3)", "Antigravity (Gemini 3 Pro)">
- Done: ...
- Decisions made: ADR-XXXX (if any)
- Next: ...
- Notes / suggestions parked: ...
```

---

## 2026-09-17 — Project scaffold created
- Agent: Claude (chat, scaffold assembled outside the repo's own agent loop)
- Done: Set up the agent-context system — AGENTS.md (canonical workflow rules,
  now tool-agnostic with a multi-agent handoff protocol), thin pointer files
  (CLAUDE.md, GEMINI.md, AGENT.md) for tool-specific auto-loading, PROJECT_MAP.md,
  CONTEXT.md, this file, ADR template + ADR-0001 (context system) + ADR-0002
  (domain, proposed), instruction template + task-0001 (scaffold brief), README.
- Decisions made: ADR-0001 (agent context system — accepted).
- Next: Rex chooses the domain/dataset → we accept ADR-0002 → run
  task-0001 (Phase 0 scaffold), whose first step is ADR-0003 (repo structure).
- Notes: No app code exists yet by design. First real engineering decision is
  the domain.

## 2026-09-24 -- ADR-0002 accepted + Phase 0 decisions (ADR-0003/0004/0005)
- Agent: Antigravity (Claude Sonnet 4.6 Thinking)
- Done: Rex accepted ADR-0002 (CFPB Consumer Complaint Database as domain).
  Walked through decision loop for all three Phase 0 structural decisions:
  ADR-0003 (repo structure), ADR-0004 (dependency management), ADR-0005
  (tooling baseline). All three ADRs written with Rex's own Why sections and
  marked ACCEPTED. CONTEXT.md updated to reflect domain chosen and open
  decisions updated to 0003/0004/0005.
- Decisions made: ADR-0002 (accepted), ADR-0003 (monorepo + src/ layout),
  ADR-0004 (uv), ADR-0005 (ruff + mypy + pre-commit + pytest).
- Next: Implement task-0001 scaffold -- create the folder structure per
  ADR-0003, initialise uv project, add dev dependencies (ruff, mypy,
  pre-commit, pytest), configure pyproject.toml tool sections, set up
  .pre-commit-config.yaml, write one trivial passing test, update
  PROJECT_MAP.md code-layout section.
- Notes: Rex flagged pace of decision loop as slow. For cheap-to-reverse
  decisions in future phases, consider accepting one-line Why answers quickly
  rather than pushing for longer explanations.

## 2026-09-24 -- Phase 0 scaffold implemented (task-0001 DONE)
- Agent: Antigravity (Claude Sonnet 4.6 Thinking)
- Done: Built the full Phase 0 scaffold per ADR-0003/0004/0005.
  src/cfpb_mlops/ package created with training/, serving/, monitoring/
  sub-packages. uv sync installs all dev dependencies from uv.lock.
  pyproject.toml configures ruff + mypy + pytest. .pre-commit-config.yaml
  installs git hooks. 2 smoke tests pass. All pre-commit hooks (ruff,
  ruff-format, mypy) passed on first commit [main a001e82].
  PROJECT_MAP.md code-layout section filled in.
- Decisions made: ADR-0003, ADR-0004, ADR-0005 (all ACCEPTED this session).
- Next: Phase 1 -- training code, MLflow experiment tracking, DVC data
  versioning, model registry. New decisions: ADR-0006 (experiment tracker),
  ADR-0007 (model registry / artifact store).
- Notes: PowerShell Set-Content adds BOM to UTF-8 files by default; this
  breaks TOML and causes ruff to crash. Use [System.IO.File]::WriteAllText
  with UTF8Encoding($false) for all file writes in this repo on Windows.

## 2026-09-24 -- Dataset downloaded and analyzed (Phase 1 start)
- Agent: Antigravity (Gemini 3.1 Pro High)
- Done: Explored three potential CFPB CSV datasets. Confirmed that the 3.5GB dataset (`Consumer_Complaints_03.csv`) contains ~1.9 million rows with consumer complaint narratives (the free-text column needed for NLP classification), out of 5.5 million total rows. Deleted the other files and renamed it to `complaints.csv`.
- Decisions made: None formal, just dataset selection.
- Next: Begin Phase 1 (task-0002). Write ADR-0006 for experiment tracker and ADR-0007 for model registry. Then implement data preprocessing, train/test split, and a basic text classification model.
- Notes: Preprocessing should drop rows where the narrative column is null, since consumers must opt in to share it and we need the text for training.

## 2026-09-29 — PROJECT_MAP.md created, Phase 1 files verified, ADR-0008 (retroactive)
- Agent: Claude Code (Sonnet 5)
- Done: Created PROJECT_MAP.md (was missing despite being referenced by
  AGENTS.md/README/CONTEXT.md) with detailed per-file explanations, including
  a full mechanical walkthrough of train.py's 7 steps and a "what is a smoke
  test" explainer, so future sessions don't have to re-derive them. Verified
  all uncommitted Phase 1 files are complete and functional: data/complaints.csv.dvc
  has a real DVC fingerprint (dvc add genuinely ran), uv run pytest
  tests/test_training.py passed 4/4, pyproject.toml/uv.lock/.gitignore diffs
  are consistent with ADR-0006/0007. Caught that the model choice inside
  train.py (TF-IDF + Logistic Regression, already implemented) had never gone
  through an ADR — flagged to Rex, walked the decision loop, Rex chose to
  keep it as the baseline and wrote the Why himself.
- Decisions made: ADR-0008 (baseline model = TF-IDF + Logistic Regression,
  ACCEPTED, retroactive).
- Next: Commit the Phase 1 work (train.py, test_training.py, ADR-0006/0007/0008,
  .dvc/ init, .gitignore/pyproject.toml/uv.lock changes). Run train.py against
  the real dataset (not just the fake-data smoke tests) to get real baseline
  accuracy/f1_macro numbers logged to MLflow. Implement the champion/challenger
  promotion logic ADR-0006 promised (--register currently always registers
  unconditionally instead of only-if-better). Add a dvc.yaml pipeline stage
  for preprocessing reproducibility (ADR-0007 consequence).
- Notes: README.md at the outer-folder level is stale (still says "Phase 0,
  not started") — worth a quick fix next session.

## 2026-09-30 — tqdm progress bars, mypy config fix, checked/rejected a load_data optimization
- Agent: Claude Code (Sonnet 5)
- Done: Added tqdm progress bars to train.py (per-chunk CSV read progress +
  6-stage pipeline progress). Fixed tool.mypy.python_version (was 3.11,
  mismatched installed numpy stubs / actual 3.12 venv — pre-existing,
  unrelated to this session's changes, caught while verifying tqdm edit with
  a clean mypy cache). Investigated whether complaints.csv is date-ordered
  (to let load_data skip scanning the full file when sample_n is small):
  scanned the Date received column in chunks across all 5.55M rows — file is
  NOT date-ordered, every chunk spans the full 2011-2024 range. Did not
  implement the optimization — would silently produce a non-recent sample
  on this file, defeating the point of the time-based split. Committed both
  changes (7c9af7b did not include this; see commits b1ef8a5 and this
  session's follow-up).
- Decisions made: None (the load_data change was investigated and correctly
  rejected on factual grounds, not a Rex decision point).
- Next: Rex runs train.py himself against the real dataset for the first
  time. Then: champion/challenger promotion logic (ADR-0006 gap), dvc.yaml
  pipeline stage (ADR-0007 gap).
- Notes: Full CSV column scan (date column only) took ~3 min on Rex's
  machine — sets expectation that the real load_data run (date + narrative
  text columns) will take several minutes, dominated by CSV parsing, not by
  TF-IDF/LogReg fitting. Do not re-attempt the tail-sampling optimization
  without re-verifying file order if the dataset file is ever replaced.

## 2026-10-07 — ponytail audit: small cleanups applied
- Agent: Claude Code (Sonnet 5.5)
- Done: Applied 5 low-risk cuts from a over-engineering audit. Removed
  `test_trivial` (1+1==2); removed no-op `n_jobs=-1` from LogisticRegression
  (also silences the sklearn FutureWarning); removed redundant
  `sort_values` in `time_split` (cutoff + boolean masks are order-independent);
  removed ruff `ignore = []`, `[tool.ruff.format]` block and mypy
  `warn_return_any = false` (all equal to defaults; `strict = false` kept as
  the ADR-0005 marker); removed `additional_dependencies: []` and the UTF-8
  BOM from .pre-commit-config.yaml. No ADR affected. `uv run --extra dev
  pytest` -> 5 passed, 0 FutureWarnings; ruff format + mypy clean.
- Decisions made: None.
- Next: unchanged (first real train.py run, champion/challenger logic,
  dvc.yaml).
- Notes / suggestions parked: (1) `ruff check` reports I001 (import order) in
  tests/test_training.py — not touched this session, likely a ruff-version
  difference vs the pinned v0.4.10 hook; `ruff check --fix` resolves it.
  (2) `dvc` sits in runtime deps but is only a CLI — consider dev extra
  (touches ADR-0007, Rex's call). (3) Plain `uv run pytest` fails here
  (dev tools are an optional extra, not synced); use `uv run --extra dev`.
  (4) train.py's docstring step 8 promises champion-only registration that
  isn't implemented. (5) Stage tqdm bar removal suggested, not applied.

## 2026-10-10 — First push to GitHub
- Agent: Claude Code (Sonnet 5.5)
- Done: Reviewed state (Phase 1 code committed; only ponytail cleanups were
  uncommitted). Extended mlops-platform/.gitignore (mlflow.db, mlartifacts/,
  .env.*, *.key, build/dist/egg-info, coverage, logs). Added a minimal
  mlops-platform/README.md. Committed and pushed `main` to
  https://github.com/Reehan09Sarmah/CFPB-Complaint-Routing (tracking set).
  Did NOT run `git init` / README-echo from the pasted snippet: repo already
  existed with 5 commits.
- Decisions made: None.
- Pending (Rex's call, not decided): AGENTS.md, CONTEXT.md, PROGRESS.md,
  PROJECT_MAP.md, GEMINI.md live in the OUTER folder, outside the git repo, so
  they are NOT on GitHub and git history is not the handoff for them (contradicts
  AGENTS.md "the only shared memory is this repo"). Options: move them into
  mlops-platform/, or make the outer folder the repo. Touches ADR-0003.
- Next: first real train.py run on the full dataset; champion/challenger
  promotion (ADR-0006 gap); dvc.yaml stage (ADR-0007 gap); DVC remote (data is
  not on GitHub, `dvc pull` will not work for others until a remote exists).

## 2026-10-10 — Agent-context files moved into the repo
- Agent: Claude Code (Sonnet 5.5)
- Done: Rex chose option 1. Moved AGENTS.md, CONTEXT.md, PROGRESS.md, PROJECT_MAP.md, GEMINI.md from the outer folder into mlops-platform/ so git history is the agent handoff. Updated PROJECT_MAP layout/path note; rewrote CONTEXT.md as a fuller snapshot. Outer stale README.md left in place (inner README.md is the real one).
- Decisions made: No ADR. Flagged as cheap-to-reverse (a file move); Rex declined to write a Why, which AGENTS.md allows only for cheap-to-reverse decisions. An ADR-0009 can still be added later with Rex's own Why.
- Next: first real train.py run; champion/challenger; dvc.yaml + DVC remote; Phase 2 FastAPI.
- Notes / suggestions parked: unchanged from 2026-10-07 entry.
## 2026-10-10 — Colab training notebook
- Agent: Claude Code (Sonnet 5.5)
- Done: Added notebooks/train_colab.ipynb (Drive-mounted CSV, clones the GitHub repo, calls train() directly so sample_n can be None, zips mlruns to Drive). Rex's machine cannot run the full dataset locally.
- Decisions made: None (Colab is a run environment, not an architecture change).
- Next: Rex uploads complaints.csv to Drive/cfpb/ and runs the notebook; record real accuracy/f1_macro here. Then champion/challenger, dvc.yaml + remote.
- Notes / suggestions parked: MLflow runs from Colab live in a zip; import into local mlruns or re-run locally on a sample if the UI is wanted.

## 2026-10-11 — First real baseline (Colab) read back
- Agent: Claude Code (Sonnet 5.5)
- Done: Rex ran train_colab.ipynb (sample_n=500000, max_features=10000, C=1.0, test_months=6) and extracted the result into mlruns/. Read mlruns/mlflow.db: 1 run, accuracy 0.6209, f1_macro 0.4638. The db's artifact paths point at /content/mlruns/... on Colab; only mlflow.db arrived locally, so the model.pkl is NOT on this machine.
- Decisions made: None.
- Next: confirm whether Drive mlruns.zip contains the model folder; add a per-class report (precision/recall/F1 per product) so the 0.62 vs 0.46 gap can be explained; then champion/challenger.
- Notes / suggestions parked: notebook has an uncommitted local edit to the zip line (not made by this session).

## 2026-10-11 — Per-class diagnostics + reproducible Colab outputs
- Agent: Claude Code (Sonnet 5.5)
- Done: Rex chose option 1 (add per-class report and rerun). Added diagnostics() to train.py and logged classification_report.json, confusion_matrix.csv, class_counts.json, baseline_accuracy, n_train/n_test/n_classes and split dates. Rewrote the Colab notebook so it gathers model + diagnostics + mlflow.db + run_info.json (git commit, library versions, settings) into run_outputs.zip and asserts completeness before download. Found why the first run's model was missing: MLflow 3 with a sqlite store writes artifacts to ./mlruns (not ./mlartifacts) and the model file is model.skops, not model.pkl. Tested end to end locally on synthetic data; pytest 6 passed, ruff and mypy clean.
- Decisions made: None (diagnostics are additive; metric definitions unchanged).
- Next: Rex reruns the notebook on Colab, drops run_outputs.zip into the repo folder (gitignored? check) and we verify it; then champion/challenger.
- Notes / suggestions parked: log the DVC data md5 as a param for data lineage; the first run (chill-crane-423) is superseded.
