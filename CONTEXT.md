# CONTEXT.md

A short SNAPSHOT of the current state of the world. History lives in `PROGRESS.md`.

---

## Where we are

- **Last session:** 2026-10-10 - Claude Code (Sonnet 5.5). Moved agent-context files into the repo; all on GitHub.
- **Repo:** https://github.com/Reehan09Sarmah/CFPB-Complaint-Routing (root = this folder, branch `main`).
- **Phase:** 1 baseline run on Colab (500k recent narratives, commit 212cd39), bundle in `run_outputs/` (gitignored): accuracy 0.6209 (majority-class baseline 0.7181), f1_macro 0.4638 (0.590 over the 11 classes present in test). Main cause: CFPB product-label renames (3 old labels only in train).
- **ADRs:** 0001-0008 ACCEPTED. Decisions pending for Rex: (1) how to handle renamed labels, (2) which metric defines the best model.
- **Known gaps:** label-taxonomy handling (3 renamed CFPB labels, see PROGRESS 2026-10-11); champion/challenger (ADR-0006); `dvc.yaml` (ADR-0007); no DVC remote; Colab sklearn 1.6.1 vs local 1.9.1 (pin versions before serving).
- **Env:** Windows; run tests with `uv run --extra dev pytest`; write files without BOM.
- **Next:** first real train run -> champion/challenger -> dvc.yaml + remote -> Phase 2 FastAPI serving.