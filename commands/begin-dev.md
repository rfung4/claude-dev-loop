---
description: Resume development work — reconcile a dev doc against actual repo state, validate readiness, then brief inline (fresh session) or write a /tmp handoff briefing (mid-session); handoff mode writes the evidenced reconciliation back to the dev doc (--sync forces it in any mode, --no-sync reports only), --next appends the next chunk of work as tasks. Use when returning to a project after a break, or when the user asks "where was I", "what's left", or "pick this back up".
argument-hint: [dev-doc] [--check] [--handoff] [--run-tests] [--sync|--no-sync] [--next "task"]
effort: medium
---

# Begin Development

Bridge across sessions. Point a context at an existing `docs/development/{feature}/`, reconcile what the doc *claims* against what the repo *shows*, and confirm it is coherent enough to continue. Then deliver the briefing in one of three ways:

- **Handoff** (mid-session: the default there) — write a self-contained "start here" briefing to `/tmp/` so the next session can `Read` it after you `/clear` this one.
- **Inline** (fresh session: this invocation is the first substantive action in the conversation) — you *are* the fresh session. Print the briefing to the terminal, write **no file**, and continue working here.
- **Continue-here** (mid-session, but the next run is one short task on the model you are running) — print the footer and the next action. No file.

## The footer: every outcome ends with it

Handoff, inline, continue-here, Blocked, Plan exhausted, `--check`: the reply ends with this one line, and nothing replaces it.

```
Next: {alias} · {effort} — you are on {model}: {stay, /effort {effort} | /model {alias} then /effort {effort} | new session: claude --model {alias} --effort {effort}}
```

- `{model}` is the model you are running, from your system prompt. You cannot see your own effort level, so never claim one; the effort you print is the absolute value the next run wants.
- `{alias}` is the next task's `Route:` tier when it carries one; otherwise the model you are on. An implementation run never goes below `opus`. Aliases only (`sonnet` / `opus` / `fable`), never a versioned id.
- **Escalation overrides the Route:** when PROGRESS.md or the reconcile shows the next task was already attempted at `opus · xhigh` and its `Verify:` still fails, the line is `fable · high`, new session, marked `escalated: task N failed Verify on opus · xhigh`.
- When the next step is the user's (an approval, an env step, a question), name the model for the first task after it.

Why: the model line went missing exactly where the old rule did not reach (Blocked replies, pasted kickoffs, closings written by other commands), and inline briefings never said what the session was already running. The footer is the only output rule here with no exception; the evidence is in the spec.

**Mode detection:** no meaningful prior work before this invocation → inline. Otherwise → handoff, unless the next run is one short task on the current model → continue-here. `--handoff` forces the file in every case, Blocked included; `--check` skips the briefing in every mode. Unknown flags (`--refresh` is an `/init-dev` flag) are refused in one line, not silently ignored.

**A pending question comes first, and a trailing one does not cancel the command.** If the previous turn left a question open, resolve it (or say it is being skipped) before running. If the user's next message arrives within the same minute ("Model?", "yes"), answer it *and* run the command; a `/begin-dev` typed just before a short reply has been swallowed by the reply.

**Context size is not yours to judge.** You cannot see it. If a context-size hook is installed, it puts a `Context is Nk tokens` line in your input once the session passes 300k, and again after each commit past that line. It means: hand off at the next clean stop — a task's passing `Verify:` and its commit — never mid-task. Past 400k, finish the task in hand to its commit, hand off, and start nothing else. Auto-compaction is the backstop, not the trigger.

**Workflow:** `/init-dev` → `/review-dev` → [implement] ⟳ **`/begin-dev`** → [paste the path into a fresh session] → [implement] → `/close-dev`

## Arguments

| Arg | Effect |
|-----|--------|
| `$1` | Dev doc / feature name. **Optional — infer from context** (see below) |
| `--check` | Validation only: report readiness + gaps + the footer, skip the briefing |
| `--handoff` | Force the file: in a fresh-looking session, or over a Blocked verdict (the question goes to the top of the file) |
| `--run-tests` | Run the SPEC's `Verify:` lines to ground the baseline (the COMMANDS.md pytest line on a legacy doc whose SPEC has none) |
| `--sync` | Force the write-back regardless of mode detection — mid-work flush, or after reconciling by hand. Evidenced rows only, same as the default |
| `--no-sync` | Skip the write-back; report drift in the briefing instead |
| `--next "<desc>"` | Append the next chunk to SPEC.md — 1–4 tasks, each with a runnable `Verify:` |

## Dev Doc Inference (when `$1` omitted)

Resolve in order; stop at first confident hit:

1. **Session context** — a `docs/development/{x}/` file already read/edited/discussed this session. If the session is discussing a ticket/card/feature that has **no** matching folder, stop here: say so and suggest `/init-dev` — do not fall through to the branch (the branch's doc is not the work under discussion, and a write-back there edits a doc the session never touched)
2. **Git branch** — branch name matching a `docs/development/{x}/` folder
3. **Most recent** — most recently modified `docs/development/*/SPEC.md`

```bash
docs/development/{arg}/SPEC.md    → Feature folder (normal; INDEX.md too unless --light)
docs/development/{arg}.md         → Legacy single-file
```

If zero candidates → tell the user, suggest `/init-dev`. If multiple plausible and none dominant → list them, ask which. Never guess silently.

## Process

### 1. Load the dev doc set
Read `SPEC.md`, `INDEX.md`, `PROGRESS.md`, `COMMANDS.md` (whichever exist; a `--light` feature has only SPEC.md and that is not a gap; COMMANDS.md is legacy and no longer generated). PROGRESS.md's `**Current task:**` line — near the top under the H1, not reliably line 1, and absent in most files — is the primary claim about where we are when present; reconcile it like any other, and fall back to the last log entry when it's missing.

### 2. Reconcile claim vs reality
| Source (claim) | Ground against (reality) |
|----------------|--------------------------|
| SPEC task checkboxes | Code evidence at referenced `file:line` |
| PROGRESS.md "last done" | `git log`, working-tree diff |
| Deliverable targets | Do the source/target paths still exist? |
| SPEC `Verify:` lines | Run green? (only if `--run-tests`) |

Surface **drift**: tasks marked done with no code, code written past the plan, uncommitted changes not reflected in PROGRESS.md, stale file references.

### 3. Validate readiness
| Check | Ready | Gap |
|-------|-------|-----|
| Dev doc set present | SPEC exists (INDEX too, unless `--light`) | missing SPEC |
| Next action unambiguous | one clear next task | plan exhausted / unclear |
| No unresolved blockers | blockers closed or noted | ⚫ open in INDEX.md Blockers table |
| References resolve | `file:line` still valid | dangling paths |
| Env/commands known | `Verify:` lines runnable | no way to run or test |
| Protected paths | next tasks edit nothing under `.claude/` or settings files | they do — warn: auto mode's self-modification guard blocks those edits, so the session will stall until the user runs them |

Two verdicts end the command early. Both still end with the footer:
- **Plan exhausted** (every task done, nothing open) → print the verdict and `run /close-dev`. No file.
- **Blocked** on the user → print the blocker as a question and stop. No file, **unless `--handoff` was passed**: then write the file with the question as the first line under **Owed by you**, so the fresh session opens on the question instead of hitting the wall. Blocked is narrow: the blocker prevents *any* next action (an open ⚫, a missing SPEC, an env step nothing can proceed without). A question that only affects a later task is a Landmine, not a verdict.

Claims about systems the reconcile did not probe — Slack apps, boxes, prod env vars, external dashboards — are **from SPEC, unverified** and are labelled so wherever they appear. Probing is the highest-value thing this command does (it has caught a task already shipped and not fixing the bug, a daemon down with open orders, a merged branch, a parallel session switching the checkout); when a claim decides the next action and can be checked with one ssh/curl/git call, check it.

### 3a. Write back (handoff default; `--sync` forces, `--no-sync` skips; `--next` in either mode)
Handoff mode writes the evidenced reconciliation back to the dev doc before composing the
briefing, so the session that *holds the context* fixes the doc instead of posting the job
forward to a session that will read nothing but the briefing. Mode detection is a guess, so
the flags override it: `--sync` writes in any mode, `--no-sync` reports drift instead.

- **Inline mode does not write unless told** (`--sync` or `--next`). A fresh session has no
  session work to flush, but the write-back reconciles doc vs *repo*, not doc vs memory — so an
  explicit `--sync` there is safe and is how you flush a manual reconcile. `--no-sync` in inline
  mode is a no-op. Both flags together → refuse, say why.
- **`--check` writes nothing.** It means "validation only", so it refuses `--next` rather than
  half-honouring it. Same for a **Blocked** verdict with a missing
  SPEC.md — `--next` has nothing to append to; say so and stop.
- **Evidence rule.** Write only rows backed by code at a `file:line`, a commit, or the
  working-tree diff. Session recollection is not evidence — it stays a flagged claim in the briefing.
- **In scope:** SPEC checkboxes (both directions), the SPEC `**Status:**` header line (on a
  `--light` SPEC it is the only state the doc carries, and the field that actually drifts),
  the PROGRESS `**Current task:**` line, a PROGRESS log entry, and — only on a legacy doc that
  has one — COMMANDS.md's `<!-- MERGE_START(VERIFY) -->` block when it is stale against SPEC.
  **Out of scope:** task bodies, existing `Verify:`/`Route:` lines, acceptance criteria,
  deliverable paths, **INDEX.md** (blockers and phase status live there — report, never write),
  anything outside `docs/development/{feature}/`, and any commit.
- **PROGRESS anchor — never write "line 1".** Line 1 is the H1 title; `**Current task:**` is
  usually absent and, when present, sits a few lines below it. Rewrite the existing line
  wherever it is, or insert one under the H1. `--light` (no PROGRESS.md) → SPEC checkboxes
  only; the file is not created.
- **A failing check outvotes code evidence.** With `--run-tests`, never flip a task to `[x]`
  when its `Verify:` fails, however convincing the code looks — that pairing is the drift
  the write-back exists to end.
- **No confirm.** Write, then print the diff that landed (file · line · before → after) and
  anything withheld for lack of evidence. The evidence rule and the failing-check rule are the
  safeguards.

`--next "<desc>"` appends the next chunk of work. The description sets the scope, not the task
count — slim or broad; decompose into as many tasks as it warrants, one runnable check each.
Every appended task **must carry `Verify:`** derived as `/init-dev` derives it (`/close-dev`
runs every Verify). A `Route:` only where the task needs one: `fable · high` when its Verify
can check shape but not correctness. A chunk with no derivable check is not a task — it lands
under `## Open Questions` tagged with who unblocks it.

**Ceiling.** Write nothing and recommend `/init-dev --refresh` if: the decomposition exceeds
**4 tasks**; the new work invalidates an existing task or acceptance criterion; it adds or
changes a deliverable target; or existing tasks would need renumbering. Append never renumbers.

COMMANDS.md is legacy: when the doc has one with a `<!-- MERGE_START(VERIFY) -->` block, append
the new `Verify:` lines inside it; never create the file or restructure one that predates the markers.

Questions follow the grill rule — only where the answer changes a task, a file, or a `Verify:`
line; zero is the common outcome, cap at 3, answers land in `## Decisions`.

The briefing is composed **after** the write, so it describes state that is already true on disk.

### 3b. Handoff gate: hand off by default mid-session
You cannot observe this session's context size or idle time, so do not estimate them; the
statusline shows the human, and a context-size hook, if installed, shows you. Mid-session the verdict is
**handoff** unless the next run is **one short task on the model you are running now**, in
which case continue-here. A `Context is Nk tokens` line in your input settles it: handoff.

- **A model change is never a stop.** A task whose `Route:` names another tier runs here on
  this session's model. The one exception is a `fable` escalation (footer rules), which is a
  fresh session.
- **Prod / deploy / destructive tasks are an approval stop, not a model change.** The `Run:`
  line names the task and the exact phrase that authorises it (`say "promote to production"`).
  A bare "go", "continue" or "yes" never authorises such a step; only the named phrase does.
- `--handoff` forces the file; so does the user saying so.

### 4. Deliver the briefing
Compose the kickoff (template below), then deliver by mode:

**Inline (fresh session):** print the briefing directly to the terminal. No file. End with the next action, then the footer, so work continues immediately in this session.

**Continue-here:** no kickoff. The footer, then the next action with its `file:line` and `Verify:`.

**Handoff:** write it to a file and print the absolute path:

```bash
OUT="/tmp/begin-dev-{feature}-$(date +%Y%m%d_%H%M%S).md"
# write briefing to "$OUT"
```

**Run `date`; never type the stamp.** An invented stamp (`_100000`, `_task2`) sorts wrongly
and can collide. The same `date` output fills the `Generated:` line.

The file must be **self-contained** — the successor's first message is this file's path and it
`Read`s the file before doing anything else, so it names the dev-doc paths to open, the next
action, and the commands. End the terminal reply with exactly two things: the footer, and the
path on its own line with the nudge *"Paste the path into a fresh session, then `/clear`."*
Nothing else from the briefing is read in the outgoing session.

With `--check`, skip the briefing in every mode — print readiness + gaps, then the footer.

## Briefing file contents

**Lead with the problem.** The first body line says in one sentence what is being fixed and why
it matters, in user-facing terms. "What are we fixing here exactly?" was the most common
question after a briefing; a readiness table does not answer it.

**Reconciliation table only on drift.** When every row is ✓ (the common case), replace the
table with one line: `State: doc and repo agree (N tasks checked)`. The successor re-reads SPEC
regardless.

**`Model / effort:`** in the file is the footer's `Next:` value with its launch command.

**`Run:`** extends forward from the next task over every task the session should take, and
stops only at an **approval stop** (prod, deploy, destructive — named with the phrase that
authorises it) or a **blocker**. A model change is not a stop. The instruction at the stop is
*print the footer and stop*; the human decides what happens next.

```markdown
# Session Kickoff: {feature}

**Fixing:** {one sentence — the user-facing problem and why it matters}
**Readiness:** Ready | Gaps found
**Dev doc:** docs/development/{feature}/  ·  branch `{branch}` ({create off X | exists | already merged})
**Model / effort:** {alias} · {effort} — `claude --model {alias} --effort {effort}` {from task {N}'s Route: | this session's model}
**Run:** tasks {N–M} here. Stop at task {J}: {needs your go-ahead — say "{exact phrase}" | blocked on {X}} — print the footer and stop; don't start it.
**Generated:** {output of `date`}

## Where we are
{2-3 sentences: what's built, what's left, from PROGRESS + code reconciliation}

## State
{`doc and repo agree (N tasks checked)` — or, only when something drifted:}
| Item | Claimed | Actual | Note |
|------|---------|--------|------|
| Task 4 (rate limit) | done | no code found | ⚠ drift — written back |
| working tree | — | 3 files uncommitted | not in PROGRESS |

## Next action
{The single next task, with `file:line` references, its `Verify:` line, and the reason}

## Landmines
- {working-tree files not to stage, a daemon not to restart, fixtures that may have expired, a protected `.claude/` path — or "none"}
- {claims from SPEC the reconcile could not probe, marked `from SPEC, unverified`}

## Owed by you
- {anything only the user can do before or during the run — env step, approval with its exact phrase, credential — or "nothing"}

## Commands
```bash
{run + test lines: the SPEC's Verify: lines and e2e check}
```

## Continue with
{One concrete instruction to hand to the working session.} Working rules: re-read the
current task's block in SPEC.md before starting it; run its Verify and commit before
moving on; keep PROGRESS.md's Current task line true; a bare "go" or "continue" never
authorises a prod, deploy or destructive step — only the named phrase does; at the named
stop, print the footer and stop — do not start the next task and do not run /begin-dev
yourself.
```

## Examples

```
> /begin-dev        (mid-session → handoff)

Inferring dev doc... branch `feat/user-preferences` → docs/development/user-preferences/
Reconciling plan vs repo...

Readiness: Gaps found (Task 4 checkbox drift; working tree clean)

Written to dev doc:
  SPEC.md   task 4 [x] → [ ]   no code at src/limits.py (claimed done)
  PROGRESS  + log entry 2026-07-06

/tmp/begin-dev-user-preferences-20260706_142210.md
Paste the path into a fresh session, then /clear.

Next: opus · medium — you are on opus: new session: claude --model opus --effort medium
```

```
> /begin-dev        (mid-session, task 4 just committed, task 5 is a 10-line change → continue-here)

Reconciling plan vs repo... doc and repo agree (4 tasks checked).

Next: opus · medium — you are on opus: stay, /effort medium
Then task 5 (preference cache invalidation), src/prefs/cache.py:61
  Verify: pytest tests/prefs/test_cache_invalidation.py
  Stop at task 7 (prod migration — needs your go-ahead: say "run the prod migration").
```

```
> /begin-dev        (mid-session, next task blocked on the user)

Readiness: Blocked — task 12 needs the staging TLS answer (plain http acceptable, or key first?).
No file written. Answer here and re-run, or pass --handoff to carry the question into the file.

Next: opus · medium — you are on fable: /model opus then /effort medium
```

## See Also

- `/init-dev` — create the dev doc (use first)
- `/review-dev` — pre-implementation gate (before first code)
- `/init-dev --refresh` — update the plan when scope shifts mid-flight
- `/close-dev` — promote + archive when done

*Full spec: `~/.claude/claude-dev-loop/specs/begin-dev.md`*
