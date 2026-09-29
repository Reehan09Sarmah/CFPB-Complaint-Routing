# ADR-0008: Baseline model choice

- **Status:** ACCEPTED
- **Date:** 2026-09-29
- **Decider:** Rex
- **Phase:** 1

## Context

`train.py` was already implemented (previous session) with a specific model:
TF-IDF vectorizer + Logistic Regression classifier, feeding a time-based
train/test split. This choice was made directly in code, without going
through the decision loop — a gap caught during this session's file review.
Retroactively documenting it here so the decision has a recorded Why, per
AGENTS.md's prime directive that no architectural choice ships un-recorded.

The underlying question: what should the FIRST model for this classification
task be? Every later model (heavier, fancier, embedding-based) will need
something to be measured against — a baseline. Reversibility is high: nothing
downstream (MLflow tracking, DVC, serving, CI/CD) depends on what's inside
the pipeline beyond it exposing `.fit()` / `.predict()`, so swapping the
model later costs one file, not an architecture change.

## Options considered

### Option A — TF-IDF + Logistic Regression (chosen)
Classic, simplest possible text-classification baseline. TF-IDF turns text
into weighted word-frequency vectors; Logistic Regression draws a linear
boundary between product categories using those weights.
- Pros: fast to train, fast to run, interpretable (can inspect which words
  drove a prediction), minimal moving parts, industry-standard first
  baseline for text classification.
- Cons: no understanding of word meaning/context — "not received" and
  "received" look similar to it; ceiling on accuracy is lower than
  context-aware models.

### Option B — Naive Bayes + bag-of-words
Even simpler/cheaper baseline than A.
- Pros: extremely fast, classic starting point for text classification.
- Cons: strong independence assumption between words tends to underperform
  Logistic Regression on TF-IDF in practice; no real advantage over A here.

### Option C — Pretrained transformer embeddings (e.g. sentence-transformers) + classifier
Context-aware text representation instead of word-frequency counts.
- Pros: substantially better accuracy ceiling, understands word context.
- Cons: heavier compute/dependency footprint, slower to iterate on, and
  skips having an actual baseline to compare against — the project would
  never know how much complexity was "worth it."

## Decision

TF-IDF + Logistic Regression, as already implemented in `train.py`.

## Why

Because it is the baseline. Whenever we develop or try to develop a good
model for a task, we always compare it with the baseline - and it cannot be
more simpler than using tf-idf with logistic regression.

## Consequences

- Every future model change (Option C, or anything else) must be compared
  against this baseline's MLflow-logged accuracy/f1_macro before being
  considered an improvement — no model change is "better" without that
  comparison.
- The pipeline's model-swap point stays isolated to `build_pipeline()` in
  `train.py` — future model changes should not require touching
  `load_data`, `preprocess`, `time_split`, or the MLflow logging around them.
- No accuracy target is set yet; the baseline's own numbers (once run against
  real data, not just the fake smoke-test rows) become the number to beat.
