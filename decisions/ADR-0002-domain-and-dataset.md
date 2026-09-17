# ADR-0002: Domain and dataset

- **Status:** PROPOSED — awaiting Rex's decision
- **Date:** 2026-09-17
- **Decider:** Rex
- **Phase:** 0

## Context

The platform is model-agnostic, but we need a concrete domain + dataset to build
against. Hard requirements:

1. **Real data only** — no synthetic generation.
2. **Large** — enough volume to be credible and to stress serving.
3. **Timestamped** — so history can be replayed month-by-month and drift emerges
   naturally. This is non-negotiable: Phases 6–7 (drift detection + retraining)
   are only genuine if the data has a time axis.
4. Clear business value → a plausible B2B or B2C product later.
5. Model stays simple enough not to steal focus from the MLOps work.

## Options considered

### Option A — NYC TLC taxi trip records
- Real, huge, timestamped to the minute across years. Predict trip
  duration / fare / demand.
- Pros: purest systems/tabular route (least ML distraction, most MLOps focus);
  drift is vivid and datable (COVID, seasonality, 2025 congestion pricing);
  trivially replayable by slicing on date; strong B2B dispatch/fleet story.
- Cons: tabular regression is unglamorous on its own (fine — the platform is
  the star).

### Option B — CFPB Consumer Complaint Database
- Millions of real, timestamped consumer complaints with product-category
  labels. Text triage / routing problem.
- Pros: plays to Rex's NLP background; obvious B2B SaaS extension
  (ticket routing); real text data; drifts as complaint mix shifts.
- Cons: text pipeline adds a bit more preprocessing than tabular.

### Option C — IEEE-CIS Fraud (Kaggle)
- Large, real, has a time-delta feature. Fraud classification.
- Pros: best drift *drama* — fraud is adversarial, so drift is real and sharp;
  fintech story.
- Cons: heavy class imbalance adds ML complexity that competes with the MLOps
  focus.

### Option D — MovieLens 25M / 32M
- Huge, real, timestamped ratings. Recommender.
- Pros: strong B2C story; large.
- Cons: recsys evaluation is fiddly and can rabbit-hole; drift is subtler.

## Decision

<!-- Rex: fill this in, flip Status to ACCEPTED, then we proceed to task-0001. -->

## Why

<!-- Rex writes this, in Rex's own words — not the agent. One paragraph you
     could defend in an interview. If you can't yet, ask for a re-explanation
     first. -->

## Consequences

<!-- What the choice locks in: model family, preprocessing needs, product angle. -->
