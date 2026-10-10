# CONTEXT.md

A short SNAPSHOT of the current state of the world. History lives in `PROGRESS.md`.

---

## Where we are

- **Last session:** 2026-10-10 - Claude Code (Sonnet 5.5). Moved agent-context files into the repo; all on GitHub.
- **Repo:** https://github.com/Reehan09Sarmah/CFPB-Complaint-Routing (root = this folder, branch `main`).
- **Phase:** 1 coded (TF-IDF + LogReg, MLflow local, DVC local cache); `train.py` NOT yet run on the full dataset.
- **ADRs:** 0001-0008 ACCEPTED. No decision pending.
- **Known gaps:** champion/challenger registration (ADR-0006), `dvc.yaml` stage (ADR-0007), no DVC remote (data not on GitHub).
- **Env:** Windows; run tests with `uv run --extra dev pytest`; write files without BOM.
- **Next:** first real train run -> champion/challenger -> dvc.yaml + remote -> Phase 2 FastAPI serving.