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
