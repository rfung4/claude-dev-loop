---
description: Reconcile every dev doc under docs/development/ in this repo against the code — find the stale ones, archive what shipped or was superseded on one go-ahead, ask one question per deferred doc, leave fresh work alone. Use whenever the user asks which dev docs are stale, dead or could be archived, says dev docs have piled up or were never closed, or wants them tidied, pruned or reconciled, including when they only want the report (--dry-run). Read-only subagents check each quiet doc against git. For one finished feature use /close-dev; to resume one, /begin-dev.
argument-hint: [feature…] [--days N] [--all] [--dry-run]
effort: medium
---

# Reconcile Development Docs

`/close-dev` is skipped more often than it is run, so dev docs die open: shipped work still
reads "in progress", abandoned plans still claim tasks, and the next `/begin-dev` trusts both.
This command clears the backlog for one repo in one pass. It reports first and moves nothing
before the user says so.

```
inventory ──► fresh (edited inside the window) ──────────────────────────► keep, unread
    │
    └─► quiet ──► one subagent per doc ──► verdict + evidence
                                              │
              shipped / superseded ───────────┼─► archive list ──► one go-ahead ──► docs/.archive/
              stalled / never started ────────┼─► one question each ──► archive | park | keep
              active / parked / not a plan ───┴─► keep
```

It never promotes deliverables, writes reports, edits task bodies or commits. A feature that
deserves a completion report gets `/close-dev`; this is for the ones that will never get it.

## Arguments

| Arg | Effect |
|-----|--------|
| `$1…` | Limit the sweep to these features. Default: every entry in `docs/development/` |
| `--days N` | Freshness window. A doc with a file edited in the last N days is kept unread. Default 14 |
| `--all` | Check fresh docs too (use after a bulk edit or a copied checkout has reset every mtime) |
| `--dry-run` | Print the report and stop: no questions, no moves, no edits |

## Process

### 1. Inventory

One row per entry in `docs/development/` (folders and loose `.md` files; skip the hub
`INDEX.md`). Split fresh from quiet on file edits, not folder mtime (`14` is `--days`); the
line also prints each doc's size and any `**Parked:**` line:

```bash
for d in docs/development/*/; do s=quiet; [ -n "$(find "$d" -type f -mtime -14 -print -quit)" ] && s=fresh; echo "$s $(du -sk "$d" | cut -f1)K $d $(grep -hs -m1 '^\*\*Parked:\*\*' "$d"SPEC.md "$d"INDEX.md)"; done
```

A doc carrying a `**Parked:** {date} — {reason}` line younger than 90 days is **parked**
whatever its mtime: listed, not sent to an agent, not re-asked. An entry with no SPEC.md, INDEX.md or task list (a folder of
client deliverables, a scratch pad) is **not a plan**: listed, never touched.

Nothing quiet → say so and stop. One to three quiet docs → check them yourself with the
brief below. Four or more → fan out, even when each doc looks short: an agent per doc keeps
one doc's story from colouring the next verdict, and keeps the docs out of this context.

### 2. Fan out

One read-only subagent per quiet doc, model `sonnet`, all launched in a single message (waves
of ten when there are more). A doc that names a `Parent:` goes to the same agent as its
parent. Each agent gets this brief with the paths filled in — it has none of this session's
context:

```
Classify one dev doc against the repo. Read-only: change nothing, run no tests.
Repo: {abs path} · default branch: {name} · doc: docs/development/{feature}/ · today: {date}

1. Read SPEC.md, INDEX.md, PROGRESS.md (whichever exist): header/status lines, the task
   list, the newest dated notes.
2. Probe the repo for what the doc claims: `git log --oneline --all -i --grep "{feature}"`,
   `git branch -a --list "*{feature}*"` (merged into the default branch or not),
   `git worktree list`, the files and symbols two or three tasks name, a PR number the doc
   cites (`gh pr view N --json state,mergedAt` when gh is available).
3. Pick one verdict:
   shipped        the tasks' code is on the default branch (or the cited PR merged)
   superseded     another dev doc or later commits replaced this plan — name them
   stalled        some tasks have code, the rest do not, and nothing has moved since
   never-started  no task has code or commits
   active         commits, an unmerged branch or a worktree show work in the last {N} days
4. Reply in exactly this shape, nothing else:

feature: {name}
verdict: {one of the five}
progress: {n}/{total} tasks evidenced (checkboxes claim {x}/{y})
last activity: {date} — {commit hash or "doc edit"}
evidence: {up to 3 lines, each a commit hash, branch name or file:line}
loose ends: {unmerged branch, live worktree, unpromoted deliverables, a question the doc
            says someone owes — or "none"}
reason: {one sentence a person who forgot this doc can decide from}

A claim you could not check is "unverified", not evidence. No evidence for shipped or
superseded means the verdict is stalled.
```

### 3. Check, then report

Before trusting an archive verdict, confirm each cited hash exists
(`git cat-file -e {hash}^{commit}`). A shipped or superseded row with no hash or file that
resolves, or with any loose end, drops to the question pile — a wrong archive of a doc with
an unmerged branch is the one expensive mistake here.

Print one table, oldest first, grouped Archive / Ask / Keep:

```
| Doc | Verdict | Progress | Last activity | Why |
```

then the counts. `--dry-run` stops here.

### 4. Ask

Use the question tool, four questions per call, until the pile is empty or the user stops.
Unanswered docs stay exactly as they are.

- First question: the archive list as a whole — archive all N, let me pick, or none.
- Then one question per stalled / never-started / loose-end doc. Each stands alone: the doc
  name, when it was created, evidenced progress, last activity and the agent's one-sentence
  reason, because the report may have scrolled away. Options, the recommendation first:
  **Archive** · **Park** (keep it, stop asking) · **Still active**.

No question tool (headless run) → print the questions numbered and stop.

### 5. Apply

```bash
A="docs/.archive/$(date +%Y%m%d_%H%M%S)_reconcile" && mkdir -p "$A" && cp docs/development/INDEX.md "$A/INDEX.before.md"
mv docs/development/{feature} "$A/"
```

- **Archive** — move the folder. Write `$A/RECONCILE.md`: the report table plus each
  answer, so the reason a doc left survives the move. A parent is archived only when every
  child is.
- **Park** — insert `**Parked:** {date} — {the user's reason, or the agent's}` under the H1
  of SPEC.md (INDEX.md when there is no SPEC). Nothing else in the doc changes.
- **Still active** — no write.
- **Hub** — in `docs/development/INDEX.md`, delete the rows of archived docs and set a
  parked row's Phase cell to `Parked {date}`. Leave every other row alone.

End with what moved, what was parked, what was left, and the undo:
`mv docs/.archive/{stamp}_reconcile/{feature} docs/development/`. If `docs/development/` is
tracked in this repo the moves show up in `git status`; say so, and do not commit.

## Example

```
> /reconcile-dev

docs/development/: 14 entries — 4 fresh, 1 parked, 1 not a plan, 8 quiet → 8 agents

| Doc | Verdict | Progress | Last activity | Why |
|-----|---------|----------|---------------|-----|
| Archive |
| rate-limits | shipped | 6/6 | 2026-08-02 — a41c9e0 | PR #41 merged; never closed |
| prefs-v1 | superseded | 2/9 | 2026-07-19 — doc edit | replaced by prefs-v2 (3f0b2aa) |
| Ask |
| export-csv | stalled | 3/7 | 2026-08-30 — 77d01c2 | branch feat/export-csv unmerged, 4 tasks left |
| sso | never-started | 0/12 | 2026-07-01 — doc edit | waiting on the IdP choice (Open Questions) |
| Keep |
| billing-retry | active | 4/5 | 2026-11-12 — 9be2f10 | worktree checked out |
…

Archive 2 · ask 4 · keep 8

[archive both? → yes]  [export-csv → Still active]  [sso → Park: "no IdP decision"]  …

Archived → docs/.archive/20261119_143022_reconcile/ (rate-limits, prefs-v1, old-importer)
Parked: sso, audit-log · Left: export-csv
Undo: mv docs/.archive/20261119_143022_reconcile/{feature} docs/development/
```

## See Also

- `/close-dev` — one finished feature, with verification, promotion and a report
- `/begin-dev` — reconcile one doc against the repo and resume it

*Full spec: `~/.claude/claude-dev-loop/specs/reconcile-dev.md`*
