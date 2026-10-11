---
description: Resume development work — reconcile a dev doc against actual repo state, validate readiness, then brief inline (fresh session) or write a /tmp handoff briefing (stale session); handoff mode writes the evidenced reconciliation back to the dev doc (--sync forces it in any mode, --no-sync reports only), --next appends the next chunk of work as tasks. Use when returning to a project after a break, or when the user asks "where was I", "what's left", or "pick this back up".
argument-hint: [dev-doc] [--check] [--handoff] [--run-tests] [--sync|--no-sync] [--next "task"]
effort: medium
---

# Begin Development

Bridge across sessions. Point a context at an existing `docs/development/{feature}/`, reconcile what the doc *claims* against what the repo *shows*, and confirm it's coherent enough to continue smoothly. Then deliver the briefing in one of two modes:

- **Handoff mode** (stale session: large or post-compaction context, hours idle, or a model-tier change with real work on the other side) — write a self-contained "start here" briefing to `/tmp/` so the next session can `Read` it after you `/clear` this one.
- **Inline mode** (fresh session: this invocation is the first substantive action in the conversation) — you *are* the fresh session; there is nothing to escape. Print the briefing content to the terminal, write **no file**, and continue working here.
- **Continue-here** (mid-session, but nothing worth escaping) — print one line (`/effort {level}` or `/model {alias}`, then continue) plus the next action. No file. See the handoff gate in step 3b.

**Mode detection:** no meaningful prior work before this invocation → inline. Otherwise run the handoff gate (step 3b): it decides between continue-here and handoff. `--handoff` forces the file; `--check` skips the briefing in every mode. Unknown flags (`--refresh` is an `/init-dev` flag) are refused in one line, not silently ignored.

**A pending question comes first.** If the previous turn left a question open, resolve it (or say it is being skipped) before running — a `/begin-dev` typed while a y/N is pending has been swallowed by the answer that followed it.

**When to use:** Before opening a new session on in-flight work (handoff), or as the first command when re-anchoring a fresh session on a dev doc (inline).

**Workflow:** `/init-dev` → `/review-dev` → [implement] ⟳ **`/begin-dev`** → [paste the path into a fresh session] → [implement] → `/close-dev`

## Arguments

| Arg | Effect |
|-----|--------|
| `$1` | Dev doc / feature name. **Optional — infer from context** (see below) |
| `--check` | Validation only: report readiness + gaps to the terminal, skip the briefing |
| `--handoff` | Force handoff mode (write the `/tmp/` file) past the gate — fresh-looking session, or a continue-here verdict you disagree with |
| `--run-tests` | Execute the pytest line from COMMANDS.md to ground the baseline |
| `--sync` | Force the write-back regardless of mode detection — mid-work flush, or after reconciling by hand. Evidenced rows only, same as the default |
| `--no-sync` | Skip the write-back; report drift in the briefing instead |
| `--next "<desc>"` | Append the next chunk to SPEC.md (+ COMMANDS.md verify block) — 1–4 tasks, each with `Verify:` + `Route:` |

## Dev Doc Inference (when `$1` omitted)

Resolve in order; stop at first confident hit:

1. **Session context** — a `docs/development/{x}/` file already read/edited/discussed this session. If the session is discussing a ticket/card/feature that has **no** matching folder, stop here: say so and suggest `/init-dev` — do not fall through to the branch (the branch's doc is not the work under discussion, and a write-back there edits a doc the session never touched)
2. **Git branch** — branch name matching a `docs/development/{x}/` folder
3. **Most recent** — most recently modified `docs/development/*/INDEX.md`

```bash
docs/development/{arg}/INDEX.md   → Feature folder (normal)
docs/development/{arg}.md         → Legacy single-file
```

If zero candidates → tell the user, suggest `/init-dev`. If multiple plausible and none dominant → list them, ask which. Never guess silently.

## Process

### 1. Load the dev doc set
Read `INDEX.md`, `SPEC.md`, `PROGRESS.md`, `COMMANDS.md` (whichever exist; a `--light` feature has only SPEC.md and that is not a gap). PROGRESS.md's `**Current task:**` line — near the top under the H1, not reliably line 1, and absent in most files — is the primary claim about where we are when present; reconcile it like any other, and fall back to the last log entry when it's missing.

### 2. Reconcile claim vs reality
| Source (claim) | Ground against (reality) |
|----------------|--------------------------|
| SPEC task checkboxes | Code evidence at referenced `file:line` |
| PROGRESS.md "last done" | `git log`, working-tree diff |
| Deliverable targets | Do the source/target paths still exist? |
| COMMANDS.md pytest | Runs green? (only if `--run-tests`) |

Surface **drift**: tasks marked done with no code, code written past the plan, uncommitted changes not reflected in PROGRESS.md, stale file references.

### 3. Validate readiness
| Check | Ready | Gap |
|-------|-------|-----|
| Dev doc set present | SPEC exists (INDEX too, unless `--light`) | missing SPEC |
| Next action unambiguous | one clear next task | plan exhausted / unclear |
| No unresolved blockers | blockers closed or noted | ⚫ open in INDEX.md Blockers table |
| References resolve | `file:line` still valid | dangling paths |
| Env/commands known | COMMANDS.md usable | no run/test commands |
| Protected paths | next tasks edit nothing under `.claude/` or settings files | they do — warn: auto mode's self-modification guard blocks those edits, so the session will stall until the user runs them |

Two verdicts end the command without a briefing file, in any mode:
- **Plan exhausted** (every task done, nothing open) → print the verdict and `run /close-dev`. Nothing to hand off.
- **Blocked** on the user (open ⚫, a question only they can answer, an env step only they can take) → print the blocker as a question and stop. A handoff written over a blocker gets opened by a fresh session that starts the blocked task and hits the wall inside a minute.

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
  the PROGRESS `**Current task:**` line, a PROGRESS log entry, COMMANDS.md `Verify:` lines
  appended by `--next`, and — when the reconcile finds the `<!-- MERGE_START(VERIFY) -->` block
  stale against SPEC — regenerating that block (it is machine-owned).
  **Out of scope:** task bodies, existing `Verify:`/`Route:` lines, acceptance criteria,
  deliverable paths, **INDEX.md** (blockers and phase status live there — report, never write),
  anything outside `docs/development/{feature}/`, and any commit.
- **PROGRESS anchor — never write "line 1".** In 140 of 142 real PROGRESS.md files line 1 is the
  H1 title; `**Current task:**` is present in only 30 and sits on line 3 in 28 of those. Rewrite
  the existing line wherever it is, or insert one under the H1. `--light` (no PROGRESS.md,
  no COMMANDS.md) → SPEC checkboxes only; neither file is created.
- **A failing check outvotes code evidence.** With `--run-tests`, never flip a task to `[x]`
  when its `Verify:` fails, however convincing the code looks — that pairing is the drift
  the write-back exists to end.
- **No confirm.** Write, then print the diff that landed (file · line · before → after) and
  anything withheld for lack of evidence. The evidence rule and the failing-check rule are the
  safeguards; a y/N on top of them would be a third gate.

`--next "<desc>"` appends the next chunk of work. The description sets the scope, not the task
count — slim or broad; decompose into as many tasks as it warrants, one runnable check each.
Every appended task **must carry `Verify:` and `Route:`** derived as `/init-dev` derives them
(`/close-dev` runs every Verify; the `Run:` line reads Route). A chunk with no derivable
check is not a task — it lands under `## Open Questions` tagged with who unblocks it.

**Ceiling.** Write nothing and recommend `/init-dev --refresh` if: the decomposition exceeds
**4 tasks**; the new work invalidates an existing task or acceptance criterion; it adds or
changes a deliverable target; or existing tasks would need renumbering. Append never renumbers.

**COMMANDS.md is part of the append.** `/close-dev` executes the `Verify:` lines in *SPEC.md*,
so an append there is not lost — but COMMANDS.md is what the briefing's Commands block and
`--run-tests` read, and it is the **fallback gate** for the 134 of 168 SPECs carrying no
per-task `Verify:` lines (`~/.claude/claude-dev-loop/specs/close-dev.md` → 2b. Verify), where its content decides close-out.
Append each new `Verify:` inside the `<!-- MERGE_START(VERIFY) -->` block (when the file
exists); if the file predates the markers, append to `## Validation` and say so rather than
restructuring it. **Match the host SPEC's dialect:** `Route:` appears in the wild as
`- Route: opus`, `- Route: opus · medium`, `**Route:** sonnet · medium` and `Route: value` —
copy the shape the target file already uses rather than importing a second vocabulary. The
briefing's `Model / effort:` line is never omitted; its run of tasks simply ends at the first
task that carries no `Route:`, which is named as the break.

Questions follow the grill rule — only where the answer changes a task, a file, or a `Verify:`
line; zero is the common outcome, cap at 3, answers land in `## Decisions`.

The briefing is composed **after** the write, so it describes state that is already true on disk.

### 3b. Handoff gate — is there a context worth escaping?
A fresh session costs more than this command does: the human's `/clear` + `/model` + `/effort`
+ paste (1–5 min), the successor re-reading SPEC and code the outgoing session already holds
(3–16 tool calls), and a cold prompt cache. Pay it only when at least one of these holds:

| Hand off when | Why |
|---|---|
| Context is large (roughly >100k tokens) or compaction has happened | the briefing replaces re-orientation instead of adding to it |
| Hours idle since the last turn | cache is cold anyway; the doc may have drifted from the repo |
| The **model tier** changes *and* the run on the new tier is more than one short task | a tier switch is only honoured at a session boundary |

Otherwise → **continue-here**: print `/effort {level}` (or `/model {alias}`) on one line, the
next action, and stop. In particular:
- **An effort-only change is never a break.** `/effort` mid-session costs a prompt-cache miss, nothing else (`context-agentic.md` → Model Routing).
- **Absorb tiny lower-tier tasks** (a one-line config or doc edit, a 2-minute script) into the current run at its tier. A 1-minute task does not get its own session; two handoffs for a 4-minute task is the failure this gate exists to stop.
- **Prod / deploy / destructive tasks are an approval stop, not a model change.** Name them as "needs your go-ahead" in the run line; do not route them down.
- The gate is a judgment, not arithmetic. `--handoff` overrides it; so does the user saying so.

### 4. Deliver the briefing
Compose the kickoff (template below), then deliver by mode:

**Inline mode (fresh session):** print the briefing directly to the terminal. No file. End with the next action so work continues immediately in this session.

**Continue-here (gate said no):** no kickoff. One line of model/effort instruction if anything changes, then the next action with its `file:line` and `Verify:`.

**Handoff mode (gate said yes):** write it to a file and print the absolute path:

```bash
OUT="/tmp/begin-dev-{feature}-$(date +%Y%m%d_%H%M%S).md"
# write briefing to "$OUT"
```

**Run `date`; never type the stamp.** 8 of 27 handoff files in one week carried invented
timestamps (`_100000`, `_1600`, `_task2`) — they sort wrongly and can collide. The same `date`
output fills the `Generated:` line.

The file must be **self-contained** — the successor's first message is this file's path and it
`Read`s the file before doing anything else, so it names the dev-doc paths to open, the next
action, and the commands. End the terminal reply with exactly two things: the briefing's
`Model / effort:` line (the model is chosen at launch, before the file is opened) and the path on
its own line, with the nudge *"Paste the path into a fresh session, then `/clear`."* Nothing else
from the briefing is read in the outgoing session.

With `--check`, skip the briefing in every mode — print readiness + gaps to the terminal only.

## Briefing file contents

**The `Model / effort:` line is mandatory in both modes** — inline and handoff, every time, no
conditional. Derive it, never omit it: from the next task's `Route:` when it has one; otherwise
from its `Verify:` line per `~/.claude/claude-dev-loop/context/context-agentic.md` → Model Routing
(runnable + mechanical → value tier; keystone → opus xhigh; Verify checks only shape → fable), saying
in the line that it was derived. **Escalation overrides the Route:** when PROGRESS.md or the
reconciliation shows the next task was already attempted at `opus · xhigh` and its `Verify:` still
fails, the line is `fable · high`, marked `escalated: task N failed Verify on opus · xhigh`, and the
run is that one task in a fresh context. A `Route:` carrying no effort takes that tier's default effort from the same file
(sonnet medium · opus medium, high for review/security · fable high). Name the model by its CLI **alias** (`sonnet`/`opus`/`fable`), never a versioned id — an alias always launches the latest model in that tier. A task marked manual / owned by the user gets no route — a model line for a human step is noise.

**The `Run:` line** extends forward from the next task over every task the session should take:
same tier, any effort; tiny lower-tier tasks absorbed; and stops at the first task that is a
genuine break — a tier change with real work behind it, a task needing the user's go-ahead
(prod, deploy, destructive), a blocker, or a task with no `Route:` and no derivable `Verify:`.
The stop is named with its **reason**, and the instruction at the stop is *stop and report* — the
human decides whether that is a handoff.

**Lead with the problem.** The first body line says in one sentence what is being fixed and why
it matters, in user-facing terms. "What are we fixing here exactly?" was the most common
question after a briefing; a readiness table does not answer it.

**Reconciliation table only on drift.** When every row is ✓ (the common case — doc and repo
agreed in roughly three of four handoffs), replace the table with one line: `State: doc and repo
agree (N tasks checked)`. The successor re-reads SPEC regardless.


```markdown
# Session Kickoff: {feature}

**Fixing:** {one sentence — the user-facing problem and why it matters}
**Readiness:** Ready | Gaps found
**Dev doc:** docs/development/{feature}/  ·  branch `{branch}` ({create off X | exists | already merged})
**Model / effort:** {alias} · {effort} — `claude --model {alias} --effort {effort}` (in an open session: `/effort {effort}`) {`from task {N}'s Route:` | `derived from task {N}'s Verify: — SPEC carries no Route: line`}
**Run:** tasks {N–M} here{, absorbing {K} (one-line edit) at this tier}. Stop at task {J}: {tier change to {alias} with {n} tasks behind it | needs your go-ahead (prod deploy) | blocked on {X}} — stop and report; don't start it.
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
- {anything only the user can do before or during the run — env step, approval, credential — or "nothing"}

## Commands
```bash
{run + test lines from COMMANDS.md}
```

## Continue with
{One concrete instruction to hand to the working session.} Working rules: re-read the
current task's block in SPEC.md before starting it; run its Verify and commit before
moving on; keep PROGRESS.md's Current task line true; at the named stop, stop and report —
do not start the next task and do not run /begin-dev yourself; the human decides whether
the stop is a handoff.
```

## Example

```
> /begin-dev        (mid-session, context cluttered → handoff mode)

Inferring dev doc... branch `feat/user-preferences` → docs/development/user-preferences/
Loading INDEX.md, SPEC.md, PROGRESS.md, COMMANDS.md
Reconciling plan vs repo...

Readiness: Gaps found (Task 4 checkbox drift; working tree clean)

Written to dev doc:
  SPEC.md   task 4 [x] → [ ]   no code at src/limits.py (claimed done)
  PROGRESS  + log entry 2026-07-06

Handoff gate: context ~140k after plan + review, next run is opus (tasks 5-7, task 6 sonnet·low absorbed) → hand off.

Model / effort: opus · medium (task 5's Route:) — claude --model opus --effort medium
/tmp/begin-dev-user-preferences-20260706_142210.md

Paste the path into a fresh session, then /clear.
```

```
> /begin-dev        (mid-session, 20 minutes in, task 4 just committed → gate says continue here)

Reconciling plan vs repo... doc and repo agree (4 tasks checked).

Nothing worth escaping: context is small, task 5 is opus · medium and this session runs opus.
  /effort medium — then continue with task 5 (preference cache invalidation), src/prefs/cache.py:61
  Verify: pytest tests/prefs/test_cache_invalidation.py
  Stop at task 7 (prod migration — needs your go-ahead).
```

```
> /begin-dev        (mid-session, every task done)

Reconciling plan vs repo... 8/8 tasks done, PR #12 merged.

Plan exhausted — run /close-dev. No briefing written.
```

```
> /begin-dev        (mid-session, next task blocked on the user)

Readiness: Blocked — task 12 needs the staging TLS answer (plain http acceptable, or key first?).
No briefing written. Answer here and re-run, or say "go ahead with task 12" and I continue.
```

```
> /begin-dev user-preferences        (first command in a fresh session → inline mode)

Loading INDEX.md, SPEC.md, PROGRESS.md, COMMANDS.md
Reconciling plan vs repo...

Readiness: Ready — SPEC current, next task clear.

# Session Kickoff: user-preferences
{...briefing printed here, no file...}

Next action: implement Task 5 (preference cache invalidation), src/prefs/cache.py
```

```
> /begin-dev --next "invalidate prefs cache on tenant delete"

Inferring dev doc... branch `feat/user-preferences` → docs/development/user-preferences/
Reconciling plan vs repo...

Readiness: Gaps found — 2 evidenced corrections, 1 unevidenced claim

Written to dev doc:
  SPEC.md   task 4 [x] → [ ]   no code at src/limits.py (claimed done)
  SPEC.md   task 5 [ ] → [x]   implemented src/prefs/cache.py:61
  SPEC.md   + task 7 "emit invalidation event on tenant delete"
            Verify: pytest tests/tenants/test_delete_emits_invalidation.py
            Route:  value
  SPEC.md   + task 8 "consume event in prefs cache"
            Verify: pytest tests/prefs/test_cache_invalidation.py
            Route:  value
  PROGRESS  Current task → "6 — cache metrics"   (line 3, under the H1)
  COMMANDS  + 2 verify lines (tasks 7, 8)
  PROGRESS  + log entry 2026-09-12 (tasks 5; 3 commits)

--next decomposed into 2 tasks (emit / consume) — separate runnable checks.

Not written (no repo evidence): "task 2 rework discussed but not started" — kept as a claim in the briefing.

Briefing composed from updated state.

Model / effort: sonnet · medium (task 6's Route:) — claude --model sonnet --effort medium
/tmp/begin-dev-user-preferences-20260912_161104.md

Paste the path into a fresh session, then /clear.
```

```
> /begin-dev auth-system --check

Readiness: Ready — SPEC current, next task clear, tests green.
No file written (--check).
```

```
> /begin-dev user-preferences --sync        (first command in a fresh session; doc reconciled by hand)

Readiness: Gaps found — 1 evidenced correction
Written to dev doc (--sync, inline mode):
  SPEC.md   task 5 [ ] → [x]   implemented src/prefs/cache.py:61 (commit a1f2c3d)

# Session Kickoff: user-preferences
{...briefing printed here, no file...}
```

```
> /begin-dev user-preferences --no-sync        (mid-session → handoff mode, read-only)

Readiness: Gaps found — 1 evidenced correction, not written (--no-sync):
  SPEC.md   task 4 [x] → [ ]   no code at src/limits.py (claimed done)

Briefing written to /tmp/begin-dev-user-preferences-20260913_091500.md — carries the drift as a gap.
```

```
> /begin-dev --next "move the whole prefs layer onto the new tenant model"

Not appended — that is a re-plan, not an append:
  · decomposes to 7 tasks (ceiling is 4)
  · invalidates task 2 (assumes the old tenant FK)
  · adds a deliverable (architecture/tenancy.md)

Run: /init-dev user-preferences --refresh
```

## See Also

- `/init-dev` — create the dev doc (use first)
- `/review-dev` — pre-implementation gate (before first code)
- `/init-dev --refresh` — update the plan when scope shifts mid-flight
- `/close-dev` — promote + archive when done

*Full spec: `~/.claude/claude-dev-loop/specs/begin-dev.md`*
