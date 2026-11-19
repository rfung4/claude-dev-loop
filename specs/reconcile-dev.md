# Spec: /reconcile-dev

Reference for the `/reconcile-dev` command. The command file (`~/.claude/claude-dev-loop/commands/reconcile-dev.md`)
is the contract; this holds the reasons.

## Purpose

`/close-dev` is the loop's only exit, and it is run by hand at the end of a feature, which is
exactly when attention has moved to the next one. Docs therefore die open. Counted across
every repo using the loop: 147 open dev docs with 62 untouched for 30 days, then
182 open with 123 stale seven weeks later. An open dead doc is not inert: its checkboxes make
"task done" claims to the next `/begin-dev` reconcile, and it poisons `/begin-dev`'s
most-recently-modified inference in a repo with many open docs.

A prune was proposed three times in three months and never happened. Each attempt
ended in a list for later: a table of candidates, a shell line to paste, questions parked in a
research file. Hence the one design rule here: **the run that finds the dead docs is the run
that moves them.** Report, one go-ahead, archive, in the same session.

## Scope

One repo per run: the archive, the hub INDEX and the git evidence are all per repo, and the
questions only make sense with that repo in view. It is not `/close-dev` in bulk: no `Verify:`
runs, no diff review, no promotion, no completion report. A feature worth that ceremony gets
`/close-dev`; the docs this command archives are the ones that were never going to.

## Why these five verdicts

The split that matters is who can decide. Whether work **shipped** or was **superseded** is a
fact the repo can prove (commits on the default branch, a merged PR, a successor doc), so
those archive on a single go-ahead for the whole list. Whether a **stalled** or
**never-started** plan is dead or merely deferred is not in the repo at all: it is in the
user's head (a client who went quiet, a decision still owed), so each gets a question.
**Active** docs are left alone.

Shipped-with-loose-ends (an unmerged branch, a live worktree, unpromoted deliverables) drops
to a question, because archiving a doc whose branch still holds unmerged work is the one
mistake here that costs more than a `mv` to undo.

## Why subagents, and why a small model

Reading a dev doc is expensive (field median 25–45 KB per SPEC) and the reads are independent
and read-only, which is the case subagents are for (`~/.claude/claude-dev-loop/context/context-agentic.md`, "When
NOT to use agents": parallel implementers conflict; parallel readers do not). One doc per
agent keeps each verdict uncontaminated by the others and keeps 20 SPECs out of the
orchestrator's context; it sees eight lines per doc.

`sonnet` because the task is evidence gathering with a fixed reply shape, every archive
verdict must cite a hash or file the orchestrator re-checks, and the outcome is a reversible
move the user approves. Three or fewer quiet docs are read inline: a fan-out there costs more than it saves. From
four up the rule is fixed rather than left to a size judgment: in the eval, the orchestrator
skipped the fan-out on four docs in three of four runs when the rule left room to.

## Freshness and its blind spot

Fresh means a file inside the doc was edited within `--days` (default 14). Folder mtime is not
used: it changes only when an entry is added or removed. File mtime has its own blind spot: a
bulk edit across every doc, or a checkout copied with fresh timestamps, makes everything look
fresh. `--all` exists for that; the inventory line prints the counts so an implausible
"0 quiet" is visible.

## Parked

Without a record of the answer, every run would re-ask the same questions and the command
would stop being run. `**Parked:** {date} — {reason}` under the H1 is that record. It lives in
the doc, not the hub, so it travels with the doc and `/begin-dev` reads it too. It expires
after 90 days: a deferral nobody has revisited in a quarter is worth one more question.

## Writes

| Path | Write |
|------|-------|
| `docs/.archive/{stamp}_reconcile/` | archived folders, `INDEX.before.md`, `RECONCILE.md` (report table + answers) |
| `docs/development/{feature}/SPEC.md` or `INDEX.md` | one `**Parked:**` line, on a Park answer only |
| `docs/development/INDEX.md` | archived rows deleted, parked rows' Phase cell set |

Nothing else. `docs/development/` and `docs/.archive/` are normally gitignored, so the move is
the archive and the undo is the reverse `mv`. No commit in any case.

## Not goals

- Not estate-wide. Run it in each repo that has a pile.
- Does not restate the status of kept docs or fix their checkboxes; that is `/begin-dev`'s
  write-back, one doc at a time, with the working session's context.
- No scheduled or automatic run. Archiving is the user's call.
