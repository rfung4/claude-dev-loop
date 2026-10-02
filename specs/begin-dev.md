# Spec: /begin-dev

Full behavioral spec for the `/begin-dev` command. The command file (`~/.claude/claude-dev-loop/commands/begin-dev.md`) is the concise contract; this is the reference.

## Purpose

`/begin-dev` is the **session-resume / handoff** step of the dev loop. `/review-dev` gates *before* the first line of code; `/begin-dev` re-anchors *between* coding sessions. It exists because long-running features outlive a single context window — the dev doc is the durable state, but a fresh session needs (a) confidence the doc still matches the repo and (b) a compact, self-contained starting instruction.

It answers three questions:
1. **Which** feature are we resuming? (inference)
2. **Is the state trustworthy?** (reconcile claim vs reality, validate readiness)
3. **What's the single next move?** (the briefing — delivered inline or as a `/tmp/` handoff file, see delivery modes)

It does not promote deliverables or write code. Inline mode writes nothing; handoff mode writes the `/tmp/` briefing and, by default, the evidenced reconciliation back to the dev doc (`--sync` forces the write in any mode, `--no-sync` reports drift in the briefing instead of fixing it). A third outcome, **continue-here**, writes nothing and prints one line: the session is mid-flight but holds nothing worth escaping, so the next move is `/effort` or `/model` in place.

**Field audit.** Measured on a week of real use (34 invocations across five projects: 17 necessary, 5 useful-but-heavy, 12 overkill): the command was cheap and its repo claims held, the cost was the session boundary, and most of the overkill came from one rule ("at a route break, stop and run /begin-dev") — hence the handoff gate, the `Run:` line, stop-and-report, and the no-file verdicts below.

**Write-back** exists for the one case where deferring the fix is wrong. In handoff mode the *outgoing* session is the only one holding the context that explains the drift; posting the fix forward to a session that will read nothing but the briefing is backwards — and the briefing's own working rule ("keep the Current task line true") is an admission that the write is owed. In handoff mode, evidenced reconciliation results are written back to the dev doc *before* the briefing is composed, so the briefing describes state that is already true on disk. `--next` appends the next chunk of work — one or more tasks — to SPEC.md in the same pass.

Still non-goals of the write-back: promoting deliverables (`/close-dev`), re-planning (`/init-dev --refresh`), writing code, committing.

## Inference algorithm (`$1` omitted)

The feature name should almost always be inferable. Resolve in strict order, stop at first confident hit:

1. **Session context** — any `docs/development/{x}/*` path read, edited, or named in the current conversation. Highest signal: the user was just working on it. **Negative hit:** when the conversation is about a ticket, card or feature that has *no* matching folder, resolution stops here with "no dev doc for X — `/init-dev X`". Falling through to the branch once produced a briefing *and a write-back* into the doc of an unrelated branch (the branch's feature, not the card under discussion); the file went unused and the user ran `/init-dev` two hours later.
2. **Git branch** — `git branch --show-current`; strip common prefixes (`feat/`, `feature/`, `fix/`, `dev/`) and match against `docs/development/*/`.
3. **Most recent** — `docs/development/*/INDEX.md` sorted by mtime, newest wins.

Resolution outcomes:
- **One confident hit** → proceed, echo which and why ("branch `feat/x` → …").
- **Zero candidates** → no dev docs exist or none match; tell the user, suggest `/init-dev {name}`.
- **Multiple, none dominant** → list candidates with their last-modified date + status, ask which. Never guess silently when ambiguous.

Path forms:
```
docs/development/{arg}/INDEX.md   → feature folder (normal)
docs/development/{arg}.md         → legacy single-file
```

## Process detail

### 1. Load dev doc set
Read whichever exist: `INDEX.md`, `SPEC.md`, `PROGRESS.md`, `COMMANDS.md`. Missing `SPEC.md` is a readiness gap (surface it, don't abort). Missing `INDEX.md` is normal for a `--light` feature — not a gap. PROGRESS.md's `**Current task:** N — …` line (near the top, under the H1 — *not* reliably line 1, see the anchor rule under Write-back) is the feature's own claim about where it is; it enters the reconcile table like any other claim (checked against SPEC checkboxes and git). Most PROGRESS.md files don't carry the line at all — its absence is a soft gap, not a blocker: fall back to the last log entry.

### 2. Reconcile claim vs reality
The core value. For each claim source, find corroborating repo evidence:

| Claim source | Reality probe | Drift signal |
|--------------|---------------|--------------|
| SPEC task checkbox `[x]` | code at the referenced `file:line` | checked but no code → re-open |
| SPEC task `[ ]` | code that clearly implements it | done but unchecked → note |
| PROGRESS.md "last done" | `git log --oneline`, working-tree diff | commits past what PROGRESS records |
| uncommitted changes | `git status --short` | edits not reflected in PROGRESS |
| deliverable source/target | path existence | dangling promotion target |
| COMMANDS.md pytest | run it (only with `--run-tests`) | red baseline |

Keep probes cheap: grep/read at referenced locations, not a full audit. The goal is *trust calibration*, not a code review.

### 3. Validate readiness
Produce a Ready / Gaps found / Blocked verdict from:

| Check | Ready | Gap |
|-------|-------|-----|
| Dev doc set present | SPEC exists (INDEX too, unless `--light`) | missing SPEC |
| Next action unambiguous | exactly one clear next task | plan exhausted, or several equally-next |
| No unresolved blockers | ⚫ items closed or explicitly parked | open ⚫ in INDEX.md's Blockers & Decisions table (where they actually live) |
| References resolve | referenced `file:line` still valid | dangling paths |
| Env/commands known | COMMANDS.md has run + test lines | no way to run/test |

**Blocked** if a hard blocker (open ⚫, missing SPEC) prevents any next action. **Gaps found** if work can continue but something needs attention (drift, stale ref). **Ready** otherwise.

**Two verdicts never produce a briefing file:**
- **Plan exhausted** — every task done, nothing open. Print the verdict and point at `/close-dev`. A handoff recommending "`sonnet · low` for `/close-dev`" was written once and answered with "Lets just close then".
- **Blocked on the user** — an open ⚫, a question only they can answer, an env step only they can take. Print the blocker as a question and stop. A handoff written over a Blocked verdict was opened by a fresh session that started the blocked task, hit the blocker within a minute, and had to ask the same question.

**Protected-path check.** If the next tasks edit anything under `.claude/` or a settings file, say so under Landmines: auto mode's self-modification guard blocks those edits, and a successor that doesn't know stalls until the user runs them by hand (25 minutes lost once).

**Unprobed claims are labelled.** Reconciliation grounds the doc against the repo. Anything about an external system — a Slack app, a box, a prod env var, a dashboard — that reaches the briefing from SPEC without a probe is marked `from SPEC, unverified`; one unmarked SPEC line can send the user to configure the wrong system. Where a claim decides the next action and one ssh/curl/git call settles it, make the call: the probe is the highest-value thing the command does (it has caught a next task already shipped and not fixing the bug, a production worker that had stopped, a merged branch, and a parallel session switching the checkout).

### 3b. Handoff gate

The `/tmp/` file exists to *transport* the briefing out of a session whose context is worth escaping. Mid-session, that is a question, not a given. The gate asks it before anything is written. A fresh session costs the human 1–5 min (`/clear`, `/model`, `/effort`, paste), costs the successor 3–16 tool calls re-reading what the outgoing session already holds, and throws away a warm prompt cache. Hand off when at least one holds:

| Hand off when | Evidence |
|---|---|
| Context large (~>100k) or post-compaction | every necessary handoff in the audit had a 130–160k context or a compaction behind it; the successor's first edit came ~45 s after the paste |
| Hours idle | cache is cold regardless; the doc has had time to drift from the repo (overnight resumes found stale PROGRESS twice) |
| **Model tier** changes *and* the new-tier run is more than one short task | a tier is only switched at a boundary — but a 1-minute note edit got its own session, and a 4-minute task cost two handoffs |

Otherwise the verdict is **continue-here**: print the `/effort` or `/model` line if anything changes, the next action with `file:line` and `Verify:`, and stop. No kickoff, no file. Rules the gate applies:

- **Effort-only is never a break.** `/effort` mid-session costs one cache miss (`context-agentic.md` → Model Routing). Four of 27 handoffs in the audit were opus·high → opus·medium or the reverse; the user aborted one of them in 5 s and flipped `/effort` by hand.
- **Absorb tiny lower-tier tasks** into the current run at its tier. One session argued this against the old spec ("tasks 3–6 are sonnet · low but each is a one-line edit, too small to be worth a handoff") and was right; the spec now says it.
- **Prod / deploy / destructive = approval stop, not model change.** In the field data, prod work was never down-routed. Name such a task "needs your go-ahead" in the `Run:` line and leave the tier alone.
- Judgment, not arithmetic. `--handoff` overrides the gate; so does the user.

### 4. Deliver briefing — three outcomes

**Inline mode** — the invocation is at/near the start of the conversation (no meaningful prior work). Print the briefing content directly to the terminal, write no file, and let work continue in the current session. This is the common case when the user opens a new session and immediately points at a dev doc. The reconcile still runs in full — it is the inline runs that caught a shipped-but-not-fixing next task and a stale "waiting on backfill" PROGRESS.

**Continue-here** — mid-session, gate said no. One line, no kickoff (see 3b).

**Handoff mode** — mid-session, gate said yes. Write the briefing to:
```bash
OUT="/tmp/begin-dev-${FEATURE}-$(date +%Y%m%d_%H%M%S).md"
```
**The stamp comes from running `date`, never from typing one.** 8 of 27 files in the audit week had invented stamps (`_100000`, `_1600`, `_task2`, `_handoff`) — they sort wrongly and can collide. The same output fills `Generated:`. End the terminal reply with exactly the briefing's `Model / effort:` line, then the absolute path on its own line, plus: *"Paste the path into a fresh session, then `/clear`."* The model/effort recommendation is acted on *before* the file is opened — it decides how the next session is launched — so it must be readable in the terminal. Nothing else from the briefing is read in the outgoing session; don't echo it.

Mode detection (inline vs mid-session) is a judgment call on conversation length/content; the gate (continue-here vs handoff) is a second judgment. When either is wrong, `--handoff` forces the file. Steps 1–3 are identical in all three outcomes.

**Self-containment requirement:** successors never paste the briefing text — in 25 of 25 cases the first user message was the bare `/tmp/…md` path and the model `Read` it. The file is still opened by a context that has read nothing else, so it must restate — not merely link — the next action, the exact `docs/development/{feature}/` paths to open, and the run/test commands. A fresh session acting only on the file's text must be able to make the next commit.

**`Run:` line — computed here, not at plan time:** derived from the SPEC's per-task `Route:` lines at resume. Take the next task's tier and extend forward over every task the session should take: same tier at any effort, plus tiny lower-tier tasks absorbed. Stop at the first *genuine* break and name its **reason**: a tier change with more than one short task behind it; a task needing the user's go-ahead (prod, deploy, destructive); a blocker; a task with no `Route:` and no derivable `Verify:`. The instruction at the stop is **stop and report** — the human decides whether that is a handoff. The old `**This session:**` line stopped at *any* route difference and told the session to run `/begin-dev` there; that rule produced the chains the audit measured (8 handoffs in a day, 3 in 15 minutes, two self-invocations). The SPEC-header `Sessions:` plan remains legacy and ignored. The briefing recommends; it never switches models. A task marked manual / owned by the user carries no model line at all.

**Lead with the problem.** The briefing's first body line states, in one sentence, what is being fixed and why it matters to a user. "What are we fixing here exactly?" was asked three times in one project after briefings that opened with a readiness table.

**Reconciliation table only on drift.** Doc and repo agreed in roughly three of four handoffs, and every successor re-read SPEC anyway. When all rows are ✓, the `State` section is one line: `doc and repo agree (N tasks checked)`.

**Model / effort is a required briefing field.** Every briefing, inline and handoff alike, carries a `**Model / effort:**` line naming a model, an effort, and the launch command. It has no omit case — the previous "omit unless every task from the current one forward carries `Route:`" rule made the field optional in exactly the population that needs it most (57 of 168 SPECs carry `Route:` at all), and a rule whose satisfying move is silence gets satisfied by silence. Resolution order, each step stated in the line so the reader knows what it rests on:

| Situation | Line says |
|---|---|
| Next task has `Route: {tier} · {effort}` | that model and effort, `from task N's Route:` |
| Next task has `Route: {tier}` only | that tier plus the tier's default effort from `context-agentic.md` → Effort = thinking mode (Sonnet medium; Opus medium, high for review/security; Fable high) |
| No `Route:` on the next task | a tier derived from its `Verify:` line per `context-agentic.md` → Model Routing, marked `derived from task N's Verify: — SPEC carries no Route: line` |
| Prose-only or absent `Verify:` too | workhorse tier, marked as derived from an unroutable task — a task nothing downstream checks never routes down |

The model is always named by CLI alias (`sonnet`, `opus`, `fable`) and the line carries the launch command `claude --model <alias> --effort <level>` (`/effort <level>` for a session already open). Aliases, not versioned ids: an alias resolves to the latest model in the tier, so briefings and SPECs do not go stale on a point release — see `context-agentic.md` → Effort = thinking mode for the full set of places effort can come from.

A derived recommendation is honest guidance, not invented planning: it is the same rubric `/init-dev` would have applied, applied late. The `Run:` line keeps its run-and-stop form and ends at the first genuine break as defined above — one untyped task no longer erases the whole field, and one effort change no longer ends the run.

**Working rules the briefing hands over:** re-read the current task's SPEC block before starting it (plan influence decays as context fills; one-paper directional evidence that periodic re-reading helps); run the task's `Verify:` and commit before the next task; keep PROGRESS.md's Current task line true (or let `/begin-dev` do it at the handoff); at the named stop, **stop and report — do not start the next task, do not run `/begin-dev`**. The previous wording ("stop and `/begin-dev` rather than `/model`") made the working session the one deciding to hand off; it self-invoked the command twice in one afternoon and handed off 90-second tasks. The Stop-hook idea (compare Current task's Route to the session model) is withdrawn with it: the audit showed the user blowing through tier breaks was *correct* behaviour in every case observed, not drift to enforce against.

### `--check`
Validation-only. Print readiness verdict + reconciliation table + gaps to the terminal; no briefing in either mode. Use when you just want to know "is this resumable?" without switching sessions.

### `--handoff`
Force handoff mode (write the `/tmp/` file) when mode detection would pick inline — e.g. you want the file anyway to seed a different machine or a parallel session.

### `--run-tests`
Execute the pytest line from COMMANDS.md and fold pass/fail into the reconciliation ("baseline green" vs "3 failing — fix before continuing"). Off by default to keep the command fast and side-effect-light.

### Write-back (handoff default; `--sync` forces, `--no-sync` skips)
Write the reconciliation back to the dev doc, then compose the briefing from the corrected state.

**Default in handoff mode.** An earlier design made this opt-in (`--sync`) on the principle that a read-only command must not start editing `docs/` because the mode detector guessed. In use it cost two prompts at every session end — handoff found drift and printed a re-run line, then the re-run asked y/N — for a write the briefing's own working rule already admits is owed. Reversed: handoff mode writes evidenced rows without asking. Mode detection is not deterministic, so both overrides stay: `--sync` forces the write whatever the detector decided (mid-work flush, or after a manual reconcile), `--no-sync` restores report-only. Passing both is refused. The detector's guess is bounded by the evidence rule below, not by a flag.

**Inline mode writes only on `--sync` (or `--next`); `--check` never writes.** A fresh session has no session state to flush, so the default there is read-only. But the write-back reconciles the doc against the *repo* (code, commits, diff), never against session memory — so an explicit `--sync` in inline mode is safe, and is the path for "I fixed things by hand, make the doc match". `--no-sync` in inline mode is a no-op.

**Evidence rule.** Only reconcile-table rows with repo evidence (code at a `file:line`, a commit, a working-tree diff) are written. A claim sourced from the session's own recollection is *not* evidence: it stays in the briefing as a claim, flagged. A compacted session is the one you least want writing confident state.

**No confirm.** Write, then print the diff that landed and what was withheld. The evidence rule and the failing-check rule are the safeguards; a y/N on top of them would be a third gate. Still all-or-nothing: either the whole diff lands or none of it.

**A failing check outvotes code evidence.** With `--run-tests`, a task whose `Verify:` line fails is never flipped to `[x]` no matter how convincing the code at its `file:line` looks — "code exists" is the weaker claim, and a green checkbox over a red check is the drift the write-back exists to end. Flip it to `[ ]` (or leave it open) and put the failure in the briefing's gaps.

| May write | May not write |
|-----------|---------------|
| SPEC task checkboxes, both directions (`[x]` → `[ ]` when no code exists; `[ ]` → `[x]` when code clearly implements it) | SPEC task bodies, `Verify:` lines, `Route:` lines, acceptance criteria |
| The PROGRESS.md `**Current task:**` line (see anchor rule below) | Deliverable source/target paths |
| A PROGRESS.md log entry: date, tasks completed, commit shas | INDEX.md — including its Blockers & Decisions table and phase status |
| The SPEC `**Status:**` header line (on `--light` SPECs it is the only state the doc carries and the field that actually drifts — three sessions in the audit hand-edited it right after the command said "nothing to write") | Anything outside `docs/development/{feature}/` |
| COMMANDS.md — appended `Verify:` lines from `--next`, and regenerating the `<!-- MERGE_START(VERIFY) -->` block when the reconcile finds it stale against SPEC (the block is machine-owned; "flagged, can't fix" left it stale twice in one week) | Hand-written COMMANDS.md content outside the VERIFY block |
| | Git objects — it never commits |

**PROGRESS.md anchor rule.** Do **not** write "line 1". Across 142 real PROGRESS.md files, line 1 is a markdown H1 title (`# Progress Log`, `# {Feature} — Progress`) in 140 of them; `**Current task:**` appears in only 30 files, and on line 3 in 28 of those. So: find the existing `**Current task:**` line wherever it sits and rewrite it in place; if none exists, insert it as the first metadata line under the H1 — above `**Current Phase:**`/`**Started:**`, exactly where `~/.claude/claude-dev-loop/templates/development-progress.md` puts it. Overwriting line 1 would eat the title.

**Blockers are not in PROGRESS.md.** `⚫` appears only in INDEX.md's Blockers & Decisions table (8 files, zero in PROGRESS.md). The write-back therefore reports blocker state and never writes it — INDEX.md is out of scope entirely, which also keeps phase-status ownership with `/close-dev` step 6.

A `--light` feature has no PROGRESS.md and no COMMANDS.md: it gets SPEC checkbox corrections only, and neither file is created.

### `--next "<description>"`
Append the next chunk of work to the end of SPEC.md's task list. Works in either mode and independently of the write-back (same no-confirm rule: append, then print the block that landed).

**The description sets the scope, not the task count.** It may be slim ("fix the retry backoff") or broad ("wire the cache invalidation path end to end"); decompose it into however many tasks it actually warrants, by the same standard `/init-dev` uses — a task is a unit with its own runnable check. One sentence of work is one task; a broad description that needs a migration, a handler change and a test fixture is three. Never pad a slim description into multiple tasks to look thorough, and never collapse three real checks into one task to stay under a limit.

Every appended task **must carry `Verify:` and `Route:`**, derived exactly as `/init-dev` derives them — `Verify:` is a command or a named test file, never prose; `Route:` follows from that Verify line per `~/.claude/claude-dev-loop/context/context-agentic.md` → Model Routing. This is not ceremony: `/close-dev` runs every `Verify:` line, and the briefing's `Run:` line reads `Route:` to find the genuine stop. A prose-only task silently degrades both. If a chunk has no derivable runnable check, that chunk is not a task — it is appended under `## Open Questions` tagged with who unblocks it, and the briefing says so.

**Ceiling — the re-plan boundary.** `--next` is an *append*, not a re-plan. Stop and recommend `/init-dev --refresh` instead when any of these is true:

| Trip | Why it is a re-plan |
|------|---------------------|
| Decomposition exceeds **4 tasks** | At that size it is a new phase, and it deserves the full grill |
| The new work invalidates an existing task or acceptance criterion | Appending cannot express "task 3 is now wrong" |
| It changes a deliverable target, or adds one | Promotion targets belong to `/init-dev`, per the write table above |
| Existing tasks would need renumbering or reordering to make sense | `--next` never renumbers |

When a trip fires, write nothing, say which trip and why, print the `/init-dev --refresh` line. The point of the ceiling is not the number; it is that a resume-time append has no grill behind it, and unearned plan growth is how a SPEC starts lying.

**Questions.** Same rule as the `/init-dev` grill: ask only where the answer would change a task, a file, or a `Verify:` line. Zero questions is the common outcome. Cap at **3** — past that the work needed planning, not appending. Answered questions land in `## Decisions` exactly as `/init-dev` records them.

**COMMANDS.md is part of the append.** `/init-dev` step 8 copies every `Verify:` into COMMANDS.md. `/close-dev` executes the lines in *SPEC.md* (`~/.claude/claude-dev-loop/specs/close-dev.md` → 2b. Verify — "COMMANDS.md collects them"), so a SPEC-only append still runs at close-out; the cost of skipping COMMANDS.md is narrower but real in two ways: it is what the briefing's Commands block and `--run-tests` read, and for a dev doc whose SPEC has no per-task `Verify:` lines — 134 of 168 in the field — close-dev *falls back* to COMMANDS.md's pytest line, so there its content is the gate. A stale collection in that population is a green close-out that checked the wrong thing. When COMMANDS.md exists, each appended `Verify:` line goes into its `<!-- MERGE_START(VERIFY) -->` block in the same write (no confirm) — or, for a file without the markers, under `## Validation` with a note; `--next` never restructures an existing COMMANDS.md. When the file doesn't exist (`--light`), nothing is created.

**Match the host SPEC's dialect.** `Route:` lines in the wild come in several shapes — `- Route: opus`, `- Route: opus · medium`, `**Route:** sonnet · medium`, `Route: value` — i.e. both model names and tier names are in use (model names dominate: ~380 lines vs ~30). Copy the shape and vocabulary the target SPEC already uses; introducing a second dialect into one file breaks nothing loudly but makes the tier-break comparison read two vocabularies.

**Typed-task invariant.** Only 34 of 168 SPECs carry task-level `Verify:` lines and 57 carry `Route:`. Appending typed tasks to an untyped SPEC is fine and desirable, and it is how an untyped SPEC becomes routable. A partially typed SPEC no longer costs the briefing its routing field: the `**Model / effort:**` line is always emitted (derived from `Verify:` where `Route:` is absent, and said to be derived), and the `Run:` line ends at the first untyped task that has no derivable `Verify:`, naming it as the stop rather than guessing past it.

Never renumbers or reorders existing tasks; new tasks are appended in dependency order after the last existing one.

## Output contract

- Terminal: a short status (inference result, readiness verdict), plus the full briefing (inline mode), the `Model / effort:` line + file path (handoff mode), or one model/effort line + next action (continue-here). Plan-exhausted and Blocked verdicts print only the verdict and the pointer/question.
- File (`/tmp/`, handoff mode only): the full kickoff briefing, self-contained, stamped by `date`.
- Dev doc (`docs/development/{feature}/`, handoff mode, `--sync`, or `--next`): SPEC.md and PROGRESS.md, plus COMMANDS.md via `--next`; the diff is printed after it lands.
- Never commits. With `--no-sync` and no `--next` it writes nothing outside `/tmp/`; nothing at all in inline mode (bar `--sync`/`--next`) or with `--check`.

## Relationship to sibling commands

| Command | Timing | Writes to |
|---------|--------|-----------|
| `/review-dev` | before first code | terminal (review report) + one PROGRESS.md line |
| `/begin-dev` | between sessions, mid-flight | terminal (inline) or `/tmp/` briefing (handoff) |
| `/begin-dev` (handoff) | end of a session, before `/clear` | `SPEC.md` checkboxes + `PROGRESS.md` (evidenced rows only) |
| `/begin-dev --next` | when the next move is known | one appended `SPEC.md` task |
| `/init-dev --refresh` | when scope shifts | `SPEC.md` |
| `/close-dev` | after last code | `docs/`, `.archive/` |

**Precedent for writing:** `/review-dev` already appends a verdict line to PROGRESS.md, so the write-back is not the first loop command to touch the dev doc mid-flight — it is the same move at the other end of the session.

**Interaction with `--refresh`:** `/init-dev --refresh` rewrites SPEC.md while preserving COMMANDS.md, which used to leave orphaned `Verify:` lines behind for `/close-dev` to run against tasks that no longer exist. `--refresh` now reconciles COMMANDS.md's `VERIFY` block against the rewritten SPEC (`~/.claude/claude-dev-loop/specs/init-dev.md` → Refresh mode). Tasks appended by `--next` are ordinary tasks there and are re-planned, preserved or dropped on their merits.

`/begin-dev` is the only loop command whose output can be meant to *leave* the current session (handoff mode). In inline mode it's simply the re-anchor that starts a fresh session's work.

## Edge cases

- **No `docs/development/` at all** → suggest `/init-dev`; nothing to resume.
- **Legacy single-file `{arg}.md`** → treat the file as INDEX+SPEC combined; reconcile what's present.
- **Feature already 🟢 complete, or plan exhausted** → note it's done, point to `/close-dev` (or that it was closed); don't fabricate a next action and don't write a handoff file.
- **Readiness Blocked on the user** → print the blocker as a question; no file.
- **Mid-session, nothing worth escaping** (small context, no idle gap, same tier or effort-only change) → continue-here; no file.
- **Unknown flag** (`--refresh` is `/init-dev`'s) → refuse in one line; never ignore silently.
- **Invoked while a question is pending** → resolve or explicitly skip the question first; the command has been swallowed by a "Yes" typed two seconds after it.
- **Everything green, plan clear** → briefing is short and that's correct; readiness Ready, next action = next unchecked SPEC task.
- **Handoff mode with zero evidenced drift** → nothing to write; say so and continue to the briefing. Not an error.
- **`--sync` or `--next` with `--check`**, or **`--sync` with `--no-sync`** → refused with the reason, briefing still delivered. `--no-sync` in inline mode → silent no-op.
- **`--next` on a feature already 🟢 complete** → refuse; a finished feature growing a task is either a new dev doc or `/init-dev --refresh`.
- **Write-back when the working tree is dirty in ways the plan never mentions** → write the PROGRESS log entry, but record the out-of-plan files as such rather than attributing them to a task. `/close-dev`'s compliance pass will surface them again.
