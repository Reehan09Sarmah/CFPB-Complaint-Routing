# ADR-0009: Handling the CFPB's renamed product labels

- **Status:** ACCEPTED
- **Date:** 2026-10-11
- **Decider:** Rex
- **Phase:** 1

## Context

The CFPB changed its `Product` taxonomy twice: on 2017-04-21/24 (12 pre-2017
names ended, the 2017 names started) and on 2023-08-24/25. Run 507b2b3d (500k
most recent narratives) trained on the 2017 names but was tested on the 2023
names. Three labels had 67,548 training rows (27%) and zero test rows, yet the
model made 53,889 test predictions into them. Accuracy was 0.6209; mapping those
labels to their successors would give about 0.81. Evidence (full-CSV scan of
Product x Sub-product x date):

| 2017-2023 name (ends 2023-08-24/25) | 2023 name (starts 2023-08-24/25) |
|---|---|
| Credit reporting, credit repair services, or other personal consumer reports | Credit reporting or other personal consumer reports |
| Payday loan, title loan, or personal loan | Payday loan, title loan, personal loan, or advance loan |
| Credit card or prepaid card | Credit card OR Prepaid card (decided by `Sub-product`) |

"Debt or credit management" is new in 2023 (784 narratives) and has no history
to recover. Only about 419k narratives exist after 2023-08-24.

This is a data-schema decision: it fixes the label set the model, the serving
API and drift monitoring all use, and models trained under different label sets
cannot be compared fairly. The raw CSV is never edited, so the mapping lives in
code and is cheap to change, but every metric produced before it is not
comparable with metrics produced after it.

## Options considered

### Option A — Map old names to new names (crosswalk), with a date floor
- Pros: keeps all 2017-2023 data (well over a million narratives), which
  matters most for rare classes (e.g. Payday: about 17k old plus 3k new
  narratives); label set matches the current taxonomy.
- Cons: the mapping must be maintained at the next rename; 2017 wording may
  differ from 2024 wording (concept drift); a wrong mapping silently corrupts
  labels unless guarded.

### Option B — Train only after the rename (2023-08-24)
- Pros: no mapping risk; labels are exactly current.
- Cons: about 160k training rows over about 4 months instead of 248k; rare
  classes get thinner; hard-coded date breaks at the next rename.

### Option C — Drop the old-name rows
- Pros: simplest.
- Cons: loses 27% of training rows and almost all history for the payday class.

### Option D — Leave as is, report only live-class metrics
- Pros: no work.
- Cons: hides the problem; the model keeps predicting labels that no longer
  exist.

## Decision

Option A. Map the three 2017-2023 labels onto the 2023 taxonomy (the card label
is split using `Sub-product`; rows whose sub-product cannot decide are dropped),
train only on rows dated 2017-04-24 or later (the first day of the 2017
taxonomy, so the 12 pre-2017 names never enter), and fail loudly if any label
outside the current 11 classes appears after mapping.

## Why

> Rex's own words.

cutting the old rows would decrease our corpus and would cut the rare classes even more which we don't want

## Consequences

- `train.py` gains `normalize_labels()`, applied to every chunk in `load_data`;
  `load_data` now also reads the `Sub-product` column. Unknown labels raise
  `ValueError`, so a future CFPB rename stops the run instead of silently
  training on a dead label.
- Run 507b2b3d is NOT a valid baseline (labels contaminated). Baseline v2 must
  be rerun after this change; its numbers become the number to beat.
- Whether 2017-era wording hurts 2024 performance is an empirical question:
  compare training start dates (2017, 2020, 2023) on the same test set, and
  consider recency weighting. Drift monitoring (Phase 6) covers the long run.
- "Debt or credit management" stays a cold-start class (no history to map).
- Revisit when the CFPB next changes the taxonomy: extend the mapping and the
  class list, and record a new ADR.
