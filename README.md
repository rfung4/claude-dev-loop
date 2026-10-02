# claude-dev-loop

[![test](https://github.com/rfung4/claude-dev-loop/actions/workflows/test.yml/badge.svg)](https://github.com/rfung4/claude-dev-loop/actions/workflows/test.yml)

**Plan on disk, check the plan against the code, resume cleanly, close against the plan.**

A documentation-driven development loop for [Claude Code](https://code.claude.com): four slash
commands that plan a change, gate the plan against the real codebase, resume it in a fresh
session, and close it out with a check that the diff matches the plan. *Documentation-driven*
means the plan document is written first and drives the work: it lives on disk in
`docs/development/{feature}/`, every task carries a runnable `Verify:` line written at plan
time, and state survives `/clear`, compaction and model switches because it is in files and
git, not in the conversation. Each task also gets a `Route:` line, a suggested model tier and
effort such as `sonnet · medium`: a cheaper model when a runnable check will catch its mistakes,
the strongest when nothing will. It is built for long, multi-session work in repos you don't
own, where the agent loses context and a plausible-wrong change is expensive.

**In use:** first written in January 2026; the four commands ran 544 times across 11
repositories in the five weeks the session logs cover (2026-08-29 to 2026-10-02).

## Why not plan mode, Spec Kit or Kiro?

| | Claude Code plan mode | Spec Kit / Kiro | This loop |
|---|---|---|---|
| Where the plan lives | A scratch file outside the repo by default | Spec files committed to the repo | `docs/development/{feature}/`, in the repo but gitignored, so it works in repos you don't own |
| What the plan is checked against | Your own read of it | The other spec artifacts (Spec Kit's `/analyze`) | The codebase, in a fresh context: each cited `file:line` opened, each "nothing else calls this" grepped |
| Ceremony for small work | Light | A full spec set (one review saw Kiro turn a bug fix into 4 stories and 16 acceptance criteria) | `--light` is one SPEC.md; a diff that fits in one sentence gets no plan |

## Install

Needs Claude Code and bash. Clone anywhere, then link:

```bash
git clone https://github.com/rfung4/claude-dev-loop.git
cd claude-dev-loop && ./install.sh
```

`install.sh` creates three kinds of symlink and nothing else:

| Link | Points at | Why |
|---|---|---|
| `~/.claude/commands/{init,review,begin,close}-dev.md` | `commands/` | makes the four commands invocable in every repo |
| `~/.local/bin/setup-docs` | `scripts/setup-docs.sh` | scaffolds `docs/` in a project |
| `~/.claude/claude-dev-loop` | this clone | the fixed prefix the commands use to `Read` their specs, context and templates from inside any project |

It never replaces an existing regular file. `./install.sh --uninstall` removes exactly those
links. Then, in a project:

```bash
setup-docs . "My Project"
```

That creates `docs/` with six INDEX files (four in tracked hubs, two in the local-only
`research/` and `development/`), gitignores `docs/{research,development,report,.archive}/`,
and installs a local pre-commit hook that stops those local-only docs from being committed.

## The loop

| Command | When | What it writes |
|---|---|---|
| [`/init-dev`](commands/init-dev.md) `<feature> [--light]` | A decision is made and the change is more than one sentence | `docs/development/{feature}/SPEC.md` — tasks, each with `Verify:` + `Route:`, acceptance criteria, an end-to-end check. Full mode adds INDEX, PROGRESS and COMMANDS |
| [`/review-dev`](commands/review-dev.md) `<feature>` | After planning, before any code | No report file — verifies the plan's claims against the repo in a fresh context; on your go-ahead, folds findings into SPEC.md where they apply |
| [`/begin-dev`](commands/begin-dev.md) `[feature]` | Returning to work, or leaving a cluttered session | Reconciles the doc against the repo; in handoff mode writes back evidenced corrections. Then briefs inline or writes a `/tmp` handoff file for a fresh session |
| [`/close-dev`](commands/close-dev.md) `<feature>` | Every task's `Verify:` passes | Runs the checks, a fresh-context diff-vs-plan compliance pass, promotes deliverables into `docs/`, writes `docs/report/{feature}.md`, moves the dev doc into `docs/.archive/` |

`--light` (SPEC.md only) is the normal case. Full structure has to be earned: the work spans
sessions, or it produces a document worth promoting. If the diff fits in one sentence, don't
plan at all.

## Design rules

Most were learned by something failing quietly.

- **`Verify:` is the routing key.** Every task carries a command or a named test file, written
  by the planner. In the studies reviewed, supplied checks moved agent success rates and
  agent-written ones didn't. The same
  line decides which model can take the task: a runnable check makes a cheaper model safe,
  no runnable check means the strongest model, because nothing downstream will catch it.
- **`@`-include is eager.** `@path` in a command or CLAUDE.md loads the file every time,
  unconditionally — a condition written beside it does nothing, and a code fence doesn't stop
  it. The commands use plain-text pointers and let the model `Read` what the work triggers.
- **A trailing `/command` is a no-op.** Slash commands only fire as the first token of a
  prompt. "…then run /review-dev" mid-sentence silently does nothing, so `/init-dev` ends by
  printing `Next: /review-dev …` for the human to run rather than trying to chain into it.
- **Archive before delete.** `docs/development/` is gitignored, so an overwrite is
  unrecoverable. `--refresh` copies SPEC.md and COMMANDS.md to `docs/.archive/{timestamp}/`
  before rewriting; `/close-dev` moves the whole dev doc there.
- **Fresh context for review, evidence over prose.** A session grading its own plan favours its
  own reasoning. Reviews run in a subagent or a session that didn't write the plan, and must
  cite the repo.

## What it looks like

**`/init-dev`** asks only the questions whose answers change a task, each with a recommendation:

```
> /init-dev user-preferences

Analyzing context...
Found: JSON column decision, models/user.py, api/preferences.py

Analyzing codebase...

2 branches. Answer, or press enter to take the recommendation.

[1/2] Existing rows have no preferences value — backfill or default-on-read?
      → Recommend: default-on-read. 40k rows, column is nullable, and a
        data migration blocks later deploys if it fails.
> enter

[2/2] Validate keys against a schema, or store free-form JSON?
      → Recommend: free-form for now, listed under Out of scope. No caller
        needs validation yet and it is additive later.
> free-form, agreed

Created: development/user-preferences/
  - SPEC.md (6 tasks, each with Verify: + Route:; 2 Decisions)
  ...

Next: /review-dev user-preferences
```

**`/review-dev`** checks the plan's claims against the repo before judging anything — each
cited `file:line` is opened, each "nothing else calls this" is grepped. Illustrative output, in
the shape the spec defines:

```
# Development Review: user-preferences

**Verdict:** Blocked
**Context read:** none

## Claim verification
- models/user.py:45 "preferences column is nullable" → verified (nullable=True)
- "only api/preferences.py reads preferences" → wrong: also jobs/export.py:112

## Blockers
### 1. Export job not covered
- **Location:** `SPEC.md:Task 3`
- **Issue / Impact / Required:** export reads the raw column; default-on-read
  never reaches it. Add a task, or move the default into the model.

## Security
N/A — no auth, input or migration surface
```

A wrong claim is a Blocker however good the rest of the plan is. The verdict follows from the
findings — **Blocked**, **Ready with notes**, or **Ready** — and on your go-ahead the findings
are folded into SPEC.md where they apply rather than written to a report.

**`/begin-dev`** decides whether a fresh session is worth what it costs, and says so:

```
> /begin-dev        (mid-session, context cluttered → handoff mode)

Inferring dev doc... branch `feat/user-preferences` → docs/development/user-preferences/
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

**`/close-dev`** reruns the checks and has a fresh subagent compare the diff with the plan:

```
> /close-dev user-preferences

Found: development/user-preferences/ (2 deliverables)

Pre-flight... ✓
Verify (6 tasks + e2e)... ✓
Compliance (fresh subagent)... 4/4 criteria implemented; 1 file outside plan: src/utils/fmt.py (noted)

Promoting:
  ✓ design.md → architecture/user-prefs.md
  ✓ api-changes.md → api/users.md

Report: docs/report/user-preferences.md
Archived: docs/.archive/20260709_101530/
```

## Why

[docs/why.md](docs/why.md) is the evidence review behind the loop — a scorecard against
Anthropic's guidance, spec-driven tools and the research literature, which claims survived
fact-checking, and what was cut as a result.

## Layout

```
commands/    the four slash commands (what the model executes)
specs/       full behavioural spec per command (rationale and edge cases)
context/     short rule libraries the commands Read on demand
templates/   dev-doc templates /init-dev fills in; docs/ is the skeleton setup-docs copies
scripts/     setup-docs.sh
tests/       structural tests: pointers resolve, setup-docs output, install/uninstall
```

Run the tests with `pytest`.

## Not included (yet)

The loop is extracted from a larger personal toolkit; `/commit`, a CLAUDE.md linter and
session-usage reports may follow.

## Author

**Author:** Ross Fung, freelance Python backend developer.

## Licence

[MIT](LICENSE)
