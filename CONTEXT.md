# CONTEXT.md

A short SNAPSHOT of the current state of the world. History lives in `PROGRESS.md`.

---

## Where we are

- **Last session:** 2026-10-10 - Claude Code (Sonnet 5.5). Moved agent-context files into the repo; all on GitHub.
- **Repo:** https://github.com/Reehan09Sarmah/CFPB-Complaint-Routing (root = this folder, branch `main`).
- **Phase:** 1. Run 507b2b3d (500k recent narratives) is NOT a valid baseline (contaminated by renamed labels: acc 0.6209, f1_macro 0.4638). ADR-0009 crosswalk and ADR-0010 metric are coded/accepted; baseline v2 must be rerun on Colab.
- **ADRs:** 0001-0010 ACCEPTED. No decision pending.
- **Known gaps:** rerun baseline v2; champion/challenger implementing ADR-0010 (needs config: critical classes, floors, queue budget); validation split before tuning cutoffs; `dvc.yaml` stage; no DVC remote; Colab sklearn 1.6.1 vs local 1.9.1.
- **Env:** Windows; run tests with `uv run --extra dev pytest`; write files without BOM.
- **Next:** push, rerun `notebooks/train_colab.ipynb` (baseline v2), analyze `run_outputs/` incl. `pr_curves.json`, then set floors/budget and build champion/challenger.