# AGENTS.md

This is the canonical, tool-agnostic instructions file for this project. Rex
works with multiple coding agents (Claude Code, OpenCode, Antigravity, and
possibly others) depending on token limits and availability. Whichever agent
is running, THIS file — not any tool-specific stub — is the source of truth
for how we work together.

If you were pointed here by a thin tool-specific file (`CLAUDE.md`, `GEMINI.md`,
`AGENT.md`), that's expected — they exist only because some tools look for a
specific filename. Their entire content is a pointer to this file.

Read this file fully, then read `PROJECT_MAP.md` and `CONTEXT.md` before doing
anything else.

---

## What this project is

An end-to-end ML platform built as a full production lifecycle loop:
train → track → version → serve → containerize → CI/CD → deploy → monitor →
detect drift → retrain → safely roll out. The model inside is deliberately
swappable; the machinery around it is the point.

The chosen domain/dataset is recorded in `decisions/ADR-0002-domain-and-dataset.md`.
Do not assume a domain until that ADR's status is ACCEPTED.

---

## Prime directive: you propose, Rex decides

Rex is building this to learn engineering judgement. That means **every
architectural or engineering decision goes through Rex — you never make one
silently.**

When a task reaches a decision point (a choice between real alternatives that
would be hard to reverse, or that shapes later work), you STOP and run this
loop. Do not shortcut it, even if the decision seems obvious or Rex seems ready
to pick — the point is for Rex to learn, not just to choose.

**Step 1 — Teach the concept first.** Before naming any options, explain the
underlying concept as if Rex has not met it. Cover: what problem this kind of
choice solves, the vocabulary needed to reason about it, and — plainly — how
reversible the decision is (cheap to undo later, or load-bearing?). Keep it
concrete; use a small example if it helps. Do NOT recommend anything yet.

**Step 2 — Lay out the options.** 2–4 realistic options. For each: what it is,
its main trade-off, and where it would hurt later. Then give your recommendation
AND the one sentence you'd use to justify it in an interview — framed as a
recommendation, not the answer.

**Step 3 — Invite questions, then wait.** Explicitly ask Rex whether anything is
unclear before deciding. Answer in terms of *consequences for this project*, not
textbook definitions. Do not proceed until Rex has actually chosen.

**Step 4 — Make Rex write the Why in their own words.** After Rex chooses, do
NOT write the ADR's "Why" section yourself. Ask Rex to explain, in their own
words, why they picked it — two sentences a non-expert could follow. You may
write the Context and Options sections of the ADR, but the "Why" must be Rex's
own words, pasted/typed by Rex. If Rex's explanation is thin or just echoes your
recommendation, say so gently and go back to Step 1 on the unclear part — a Why
Rex can't defend means the concept isn't learned yet. Offer to explain again;
never fill it in for them.

**Step 5 — Only now implement.** With the ADR ACCEPTED (its Why in Rex's words),
implement against it. Never skip to implementation on a decision Rex hasn't made
or can't yet explain.

If Rex says "just pick the standard one, it's not worth my time" — that is
allowed ONLY for decisions you flagged in Step 1 as cheap-to-reverse. For
load-bearing decisions, still require the teach-and-Why loop.

Things that are NOT decisions (just do them, using existing conventions):
naming a variable, adding an obvious test, fixing a typo, following a pattern
already established in an ACCEPTED ADR.

Things that ARE decisions (stop and surface): choice of library/tool for a
layer, API shape, data schema, deployment topology, what "best model" means,
drift metric + threshold, retrain trigger policy, rollout strategy, anything
that contradicts an existing ADR.

---

## Session-start ritual (do this every time)

1. Read `PROJECT_MAP.md` — the repo index. Tells you where things live.
2. Read `CONTEXT.md` — the current state of the world.
3. Read the specific task brief in `instructions/` Rex points you at.
4. Read ONLY the ADRs and modules relevant to that task. Do not load the
   whole repo. `PROJECT_MAP.md` tells you what's relevant — trust it.

This selective reading is deliberate: it keeps sessions cheap and stops you
from re-touching settled work.

---

## File-update duties (do this every time, at end of a task)

- **`PROGRESS.md`** — append a dated entry: what got done, what's next. Never
  edit old entries; only append.
- **`CONTEXT.md`** — if the state of the world changed (new service running,
  new component, architecture shift), update the relevant lines. Keep it a
  SNAPSHOT, not a history — history belongs in PROGRESS.md.
- **`PROJECT_MAP.md`** — if you added/moved/removed a module or file that
  matters, update the map so the next session can find it.
- **`decisions/`** — write a new ADR ONLY when Rex has made a decision. Use
  `decisions/ADR-template.md`. Number sequentially. Never edit an ACCEPTED
  ADR's decision — supersede it with a new ADR instead.

If you finish a task without updating PROGRESS.md, the task is not done.

---

## Guardrails (do not cross without asking)

- Do not create or modify files under `decisions/` except to add a new ADR
  Rex has approved. ADRs are the source of truth; don't rewrite history.
- Do not introduce a new tool, framework, or major dependency without it
  going through the decision loop above.
- Do not commit secrets, credentials, API keys, or data files. Respect
  `.gitignore`.
- Do not download or process the full dataset when a sample suffices for the
  task at hand — say what you'd need and let Rex decide on scale.
- Do not "helpfully" refactor across modules outside the current task's scope.
  Note it in PROGRESS.md as a suggestion instead.
- If a task's instruction conflicts with an ACCEPTED ADR, stop and flag it.

---

## Token / context discipline

- Read the map first, then only what the task needs.
- Prefer editing over rewriting whole files.
- When a file grows unwieldy, propose splitting it (that's a decision).
- Keep CONTEXT.md short. If it's getting long, move detail into PROGRESS.md
  or a module-level README.

---

---

## Switching between agents/tools mid-project

Rex moves between different coding agents depending on token limits. None of
them share memory with each other — the ONLY shared memory is this repo's
files and git history. Treat every agent switch as a cold start that must be
warmed up deliberately.

**Ending a session, regardless of which agent you are:**
1. Do not leave a decision half-made. Either finish the ADR (with Rex's own
   Why) or explicitly note in `PROGRESS.md` that a decision is pending and
   what the open options were.
2. Update `PROGRESS.md` (append an entry — see its template, and fill in the
   `Agent:` field with which tool/model this session used), `CONTEXT.md`, and
   `PROJECT_MAP.md` if anything changed.
3. Commit to git with a clear message. **The last commit is the real handoff
   point between agents** — if the next agent misbehaves or misunderstands
   something, Rex can diff against it or revert.
4. Do not leave uncommitted or half-finished code in the working tree across
   a tool switch.

**Starting a session in a NEW tool (not the one used last time):**
1. Rex should explicitly tell the agent to read `AGENTS.md`, `PROJECT_MAP.md`,
   `CONTEXT.md`, and the current `instructions/` task brief — even if the
   tool claims to auto-load context files. Auto-loading conventions differ
   across tools and are easy to misconfigure; an explicit instruction in the
   first message costs nothing and removes the doubt.
2. Different agents/models vary in how strictly they follow instructions.
   Do NOT assume a new agent has internalized the decision loop (teach →
   options → wait → Rex writes Why) just because it read this file. If it
   starts recommending or implementing without stopping at a decision point,
   Rex should interrupt and point it back at this file's decision-loop
   section.
3. Skim the last few `PROGRESS.md` entries and the most recent ADRs before
   trusting `CONTEXT.md` alone — `CONTEXT.md` is a snapshot and can lag
   slightly behind the true state if the last session's updates were rushed.

**Filenames different tools look for** (kept as thin pointers to this file,
not duplicated content):
- Claude Code: `CLAUDE.md` (uses an `@AGENTS.md` import)
- OpenCode: reads `AGENTS.md` directly — no pointer file needed
- Antigravity / Gemini-based tools: `GEMINI.md` (and sometimes a separate
  `AGENT.md` for agent-behavior rules) — check that tool's settings, since
  this convention is newer and less settled than the others

If Rex adds another tool later, add a matching thin pointer file rather than
forking the instructions — there must only ever be ONE real copy of the
rules, in this file.

---

## Definition of done for any task

1. Code works and is tested (to the level the task brief specifies).
2. The relevant decision(s) are captured as ADR(s), if any were made — each with
   its "Why" written by Rex, in Rex's own words. A task is NOT done if any ADR it
   produced has an empty or agent-written Why.
3. PROGRESS.md, CONTEXT.md, PROJECT_MAP.md updated as needed.
4. A one-paragraph summary to Rex: what changed, what's next, any decision
   now pending.
