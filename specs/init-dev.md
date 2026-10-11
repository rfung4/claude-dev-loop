# Initialize Development

Create a development structure in `docs/development/` with optional AI-powered implementation planning. Consolidates the creation of development docs from either conversation context or research files.

**Workflow:**
```
[research notes] → /init-dev auth --from-research → /review-dev → [implement] → /close-dev
                   /init-dev auth                  → /review-dev → [implement] → /close-dev
                                                              ↓
                                                   /init-dev --refresh (updates existing)
```

## Arguments

- `$1` - Feature name in kebab-case (required)
- `--from-research` - Source from `docs/research/{name}.md` instead of context
- `--light` - SPEC.md only (+ PROGRESS.md if multi-session); no INDEX.md / COMMANDS.md
- `--refresh` - Regenerate SPEC.md for an existing dev doc, preserving PROGRESS.md, checkmarks, `Route:`/`Verify:` lines; reconciles COMMANDS.md's `VERIFY` block against the rewritten plan

## Modes

### Mode 1: From Context (Default)

Create development doc from current conversation context. Use when you already know what you're building.

```
/init-dev user-preferences
```

**When to use:**
| Write a research note first | Use `/init-dev` |
|------------------------|-----------------|
| Exploring options | Decision already made |
| Uncertain about approach | Clear implementation path |
| Need to compare trade-offs | Ready to build |
| Early investigation | Feature scope defined |

### Mode 2: From Research (`--from-research`)

Promote a research document to development. Use when research is complete.

```
/init-dev auth-system --from-research
```

**When to use:**
- Research file exists in `docs/research/`
- Status is `decided` (or you confirm promotion of incomplete research)
- Ready to convert exploration into structured implementation

### Mode 3: Light (`--light`)

The plan is the artifact. Creates `SPEC.md` only (add `PROGRESS.md` if the work will span sessions). For multi-step work that fits one sitting and promotes nothing. The old `--no-plan` (scaffolding without a plan) is gone — it produced the files that matter least and skipped the one that matters.

```
/init-dev fix-retry-backoff --light
```

**Don't invoke at all** when the diff fits in one sentence. Planning is overhead there (Anthropic best-practices: "if you could describe the diff in one sentence, skip the plan").

---

## Process

### 1. Determine Feature Name

If not provided as argument, prompt:
```
Feature name (kebab-case):
```

### 2. Check Prerequisites

```bash
# Verify development directory exists
if [ ! -d "docs/development" ]; then
  echo "Error: docs/development/ not found"
  echo "Run setup-docs . \"<name>\" first, or create manually"
  exit 1
fi

# Check for collisions - stop; never overwrite an existing dev doc
if [ -e "docs/development/{name}" ]; then
  echo "development/{name} already exists - re-plan it with /init-dev {name} --refresh, or pick another name"
  exit 1
fi
```

### 3. Source Content

#### From Context (default)
Analyze current conversation to extract:

| Element | Source | Maps To |
|---------|--------|---------|
| Feature purpose | Discussion | Background section |
| Implementation details | Technical discussion | SPEC.md |
| Files to modify | Code references | Tasks / Impacted Files |
| Open questions | Uncertainties mentioned | Open Questions |
| Key decisions | Conclusions reached | Background / Decisions |

#### From Research (`--from-research`)

Locate research file:
```bash
# Check various forms
docs/research/{arg}
docs/research/{arg}.md
```

If not found, list available and prompt:
```
Available research docs:
1. auth-strategy.md (decided)
2. caching-options.md (exploring)
3. queue-backend.md (paused)

Which research doc to promote? [1-3 or name]:
```

Validate research status:
- `decided` - Proceed
- `exploring` or `paused` - Warn and confirm:
  ```
  Warning: research/auth-strategy.md status is "exploring"
  Promoting incomplete research may result in unclear deliverables.
  Continue anyway? [y/N]:
  ```

Parse research document:

| Research Section | Maps To |
|------------------|---------|
| `## Question` | Background context |
| `## Requirements` | Background context |
| `## Decision` | Background (key decision) |
| `## Open Questions` (checked) | Resolved, include in background |
| `## Open Questions` (unchecked) | Grill input (step 7) — resolved into a Decision, converted to a task, or re-tagged `blocked on:`. Never promoted into work unanswered |
| Key insights from options | Background |

### 4. Determine Deliverables

Based on content, suggest which permanent docs will be created:

| Content Type | Suggested Target |
|--------------|------------------|
| Architecture decisions | -> `architecture/{feature}.md` |
| API changes | -> `api/{resource}.md` |
| Schema changes | -> `schema/{entity}.md` |
| Gotchas/lessons | -> `notes/{topic}.md` |
| Process changes | -> `ops/{process}.md` |

Prompt user to confirm/edit deliverables.

### 5. Create Development Structure

Always a directory:

```
docs/development/{feature}/
├── INDEX.md          # From template. Status, decisions, deliverables. LINKS to SPEC's tasks — never copies them
├── SPEC.md           # The plan. Always present
├── PROGRESS.md       # From template. **Current task:** line under the H1
└── COMMANDS.md       # From template. Collects every task's Verify: + the e2e check
```

`--light`: `SPEC.md` only (+ `PROGRESS.md` if multi-session). `/review-dev`, `/begin-dev` and `/close-dev` all tolerate a missing INDEX.md.

**Full structure is earned, not default.** Emit INDEX/PROGRESS/COMMANDS only when the work
spans more than one session or has a deliverable to promote into `docs/`; otherwise `--light`.
Ticket-shaped work (one ticket, one sitting) is the `--light` case. Rationale: of 147 open dev docs
in several real projects, 62 sat untouched for 30+ days — unearned structure is not inert,
a stale SPEC makes false claims to the next `/begin-dev` reconciliation.

### 6. Run Codebase Analysis

```
Analyzing codebase...
- Scanning for related files: models/, api/, services/
- Reading existing patterns
- Checking test structure
- Identifying dependencies
```

### 7. Draft the task list, then grill

Draft task **titles and impacted files only** — no details, no `Verify:` lines. This
draft is scratch: it exists to expose what you do not yet know, and is never written
to disk. Grilling after generation means paying for a plan and then rewriting it.

#### The grill

The test for asking a question at all: **would the answer change a task, a file, or a
`Verify:` line?** If not, do not ask it. Because every task must carry a runnable check
(see `Verify:` rules below), a task you cannot write a check for is the signal — that
is where the ambiguity is.

**Asking zero questions is a valid and common outcome.** A clear brief in a familiar
codebase should produce silence. Never manufacture a question to satisfy this step —
ceremony here is worse than nothing, because it teaches the user to skip the step.

| Rule | Why |
|------|-----|
| One question at a time | Batched questions get skimmed — the easy ones get answered and the hard one gets a shrug |
| Each carries a recommended answer + one-line reason | Enter-to-accept becomes the default path; the user reviews a proposal instead of authoring from blank |
| State the branch count before the first question | A visible end. Open-ended interrogation is what gets abandoned |
| Hard cap of 8 | Past 8 the feature is too big — split it rather than grinding through |
| Recommendations cite the step-6 analysis | "Extend ProgressService" is an opinion; "extend ProgressService — 400 lines, 3 callers" is a recommendation |

Question sources, in order. Skip any branch the feature does not touch:

1. **Data shape** — migration, backfill, retention
2. **Module ownership** — new module vs. extend an existing one
3. **Failure modes** — idempotency, partial failure, retries
4. **Auth / ownership boundary**
5. **Observability** — how will this be seen working? (this answer usually *is* the `Verify:` line)
6. **Non-goals** — what is explicitly cut

Worked example of one question:

```
6 branches. Answer, or press enter to take the recommendation.

[2/6] Idempotency: if the backfill runs twice, what stops a double award?
      → Recommend: partial unique index on (user_id, lesson_id) WHERE
        event_type IS NOT NULL. Protects the live path too, and keeps
        manual grants exempt — cheaper than a script-side guard.
```

Every answer becomes a `## Decisions` row **including the rejected option**. The
rejected option is the part that earns its keep: it stops the next session — or
`/review-dev` — re-proposing what you already ruled out, and it is what `/close-dev`
promotes into `architecture/{feature}.md`.

What the grill *cannot* settle — needs the client, prod data, a third party — goes to
`## Open Questions` tagged with who unblocks it. That is the section's only legitimate
content once the grill has run.

### 8. Generate SPEC.md

```markdown
# Implementation Plan

**Generated:** {date}
**Status:** Draft | Approved | Stale

## Summary

{1-2 paragraph AI analysis}

## Decisions

| # | Decision | Rationale | Rejected |
|---|----------|-----------|----------|
| 1 | Backfill via one-off script, not a data migration | 40k rows; a failed data migration blocks every later deploy | Alembic data migration |

## Impacted Files

| File | Action | Reason |
|------|--------|--------|
| src/models/user.py | modify | Add preferences field |

## Task Breakdown

- [ ] **Task 1:** Add preferences JSON field
  - File: `src/models/user.py:45`
  - Details: Add `preferences = Column(JSON, default={})`
  - Verify: `pytest tests/unit/test_user_model.py::test_preferences_default -x` (new test, write it first)
  - Route: sonnet · medium

Commit after each task passes its Verify.

## Dependencies & Risks

| Type | Description | Mitigation |
|------|-------------|------------|
| risk | Large table migration | Use batched migration |

## Acceptance Criteria

- [ ] User can read/write preferences via API

## End-to-end check

`{one command that proves the feature works as a whole}`

## Out of scope

| Cut | Reason |
|-----|--------|

## Open Questions

- [ ] Retention window for point_events rows? — **blocked on: client**
```

**`## Decisions` rules.** One row per grill answer, written at plan time, never
back-filled from the code. The `Rejected` column is not optional — a decision without
its discarded alternative gets re-proposed by the next session. `/review-dev` treats a
Decision with no implementing task or `Verify:` as a coverage gap. It is also the
natural source for `architecture/{feature}.md` when that is listed as a deliverable —
`/close-dev` promotes it like any other design content, not by special case. Empty
table = the grill asked
nothing, which is a normal outcome, not a skipped step.

**`## Open Questions` rules.** After the grill this holds only what could not be
settled in the room — needs the client, prod data, or a third party. Each carries a
**blocked on:** tag. Anything answerable by the two people in the session should have
been a Decision.

**`Verify:` rules.** It is a command or a named test path. The planner writes it; the implementing session runs it — it does not invent its own check. Prose is not a Verify ("runs twice with zero diff" → `scripts/x.py && git diff --exit-code kb/refs`). Every `Verify:` is copied into COMMANDS.md, inside the `<!-- MERGE_START(VERIFY) -->` / `<!-- MERGE_END(VERIFY) -->` markers — that block is machine-owned (see Refresh mode); anything outside the markers is hand-written and never rewritten. Evidence: supplied, correct checks move agent success rates by ~25pp on SWE-bench; agent-written tests move nothing (`~/.claude/claude-dev-loop/docs/why.md`).

**`Route:` rules.** `{tier} · {effort}` — write both; tier-only routes are why `/begin-dev` handoffs had to fall back to a tier default for the effort half of their model/effort line. Derive the tier from the Verify line per `context-agentic.md` → Model Routing and the effort from the same file's Effort = thinking mode table, raising it off the default only where the task's reasoning (not its typing) warrants it. A task whose Verify is prose-only cannot route below the workhorse tier.

**Keystones and Fable.** A keystone is a large task whose interfaces at least three later tasks build on, where the SPEC fixes *what* but leaves *how* to the implementer — the engine of a feature, not its removals or wiring. Tag it by appending `· keystone` to the task title (at most two per plan) and route it `opus · xhigh`, not Fable: with a runnable check to iterate against, Opus 5.5 matches or beats Fable 5.1 at ~⅓ the cost per task (recheck 2026-10-11, `context-agentic.md` → Model Routing). Fable is for the task whose Verify can only check shape — a mapping table's row count, a prompt's length cap — not whether the judgment is right; route that `fable · high`. Never write `fable · max`. Before this rule the table had no row that reached Fable for implementation, and Fable was routed to one task across 99 SPECs.

**`Sessions:` is gone.** The session split is computed by `/begin-dev` at resume time from the `Route:` lines, when it is actionable.

### 9. Update INDEX Files

**If `--from-research`:**

Update both tracking indexes:

**research/INDEX.md:** Mark as promoted
```markdown
| 🟢 promoted | {topic} | {created} | {today} |
```

**development/INDEX.md:** Add new entry
```markdown
| 🔴 Not Started | {feature} | {today} | Planning |
```

Archive research file:
```bash
ARCHIVE_DIR="docs/.archive/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$ARCHIVE_DIR"
mv docs/research/{file}.md "$ARCHIVE_DIR/"
```

**If from context:**

**development/INDEX.md:** Add new entry
```markdown
| 🔴 Not Started | {feature} | {today} | Planning |
```

### 10. Report Summary

```
Created: development/{feature}/

Files:
  - INDEX.md (populated from {source})
  - SPEC.md (implementation plan)
  - PROGRESS.md
  - COMMANDS.md

Deliverables configured:
  - SPEC.md (design section) -> architecture/{feature}.md (create)
  - SPEC.md (api section) -> api/{resource}.md (merge)

{If --from-research:}
Archived: research/{file}.md -> .archive/{timestamp}/

Next steps:
  1. Review/edit INDEX.md deliverables table
  2. Review SPEC.md implementation plan
  3. Run /review-dev {feature} for security check
  4. Track progress in PROGRESS.md
  5. Run /close-dev {feature} when ready
```

---

## Example Usage

### From Context (Default)

```
> /init-dev user-preferences

Analyzing conversation context...

Found:
  - Feature: User preferences system
  - Decisions: Use JSON column, not separate table
  - Files: models/user.py, api/preferences.py
  - Open: Migration strategy for existing users

Suggested deliverables:
  1. SPEC.md (design) -> architecture/user-preferences.md
  2. SPEC.md (schema) -> schema/user.md (merge)

Confirm? [Y/n]: y

Analyzing codebase...
  - Found: src/api/users.py, src/models/user.py
  - Tests: 12 user-related tests

Creating development/user-preferences/...

Generated:
  - INDEX.md (populated from context)
  - SPEC.md (6 tasks, 4 files)
  - PROGRESS.md
  - COMMANDS.md

Updated: development/INDEX.md

Next: /review-dev user-preferences
```

### From Research

```
> /init-dev auth-system --from-research

Found: docs/research/auth-strategy.md
Status: decided

Suggested deliverables:
  1. SPEC.md (design) -> architecture/auth-system.md
  2. SPEC.md (api) -> api/auth.md

Confirm? [Y/n]: y

Analyzing codebase...
  - Found: src/api/users.py, src/models/user.py
  - Tests: 12 auth-related tests

Creating development/auth-system/...

Generated:
  - INDEX.md (populated from research)
  - SPEC.md (8 tasks, 5 files)
  - PROGRESS.md
  - COMMANDS.md

Updated:
  - research/INDEX.md (marked promoted)
  - development/INDEX.md (added auth-system)

Archived: research/auth-strategy.md -> .archive/20260115_143022/

Next: /review-dev auth-system
```

### Light

```
> /init-dev fix-retry-backoff --light

Analyzing codebase...
  - Found: src/clients/base.py:88 (retry loop), tests/unit/test_retry.py

Created: development/fix-retry-backoff/SPEC.md (3 tasks, each with Verify: + Route:)
No INDEX/COMMANDS — the SPEC is the artifact.

Next: /review-dev fix-retry-backoff
```

---

## Refresh mode (`--refresh`)

Rewrites SPEC.md for an existing dev doc when scope shifted. PROGRESS.md, completed checkmarks, and every surviving task's `Route:`/`Verify:` lines are preserved; the grill covers only the delta.

### Archive before rewriting
`--refresh` overwrites a file that may be the only record of a plan, and `docs/development/` is gitignored — an overwrite is unrecoverable. Before writing, archive what will change:

```bash
ARCHIVE_DIR="docs/.archive/$(date +%Y%m%d_%H%M%S)" && mkdir -p "$ARCHIVE_DIR" && cp docs/development/{feature}/SPEC.md docs/development/{feature}/COMMANDS.md "$ARCHIVE_DIR/" 2>/dev/null
```

### COMMANDS.md reconciliation
COMMANDS.md is not regenerated, but its `VERIFY` block must not drift from the rewritten SPEC. `/close-dev` executes the `Verify:` lines in SPEC.md and treats COMMANDS.md as the collection of them (`~/.claude/claude-dev-loop/specs/close-dev.md` → 2b. Verify), so drift is not usually a false green — with two exceptions that make it matter:

1. **The fallback path.** A dev doc whose SPEC carries no per-task `Verify:` lines — 134 of 168 in the field — has close-out fall back to COMMANDS.md's pytest line. There the file *is* the gate, and a stale block is a green close-out that checked the wrong thing.
2. **Human and session use.** COMMANDS.md is what `/begin-dev`'s Commands block, `--run-tests`, and the user copy from. Dead commands for dropped tasks and missing commands for new ones waste exactly the session the handoff was meant to speed up.

**With markers present** (`<!-- MERGE_START(VERIFY) -->` … `<!-- MERGE_END(VERIFY) -->`): replace the block's contents with every `Verify:` line from the rewritten SPEC plus the end-to-end check, in task order. Everything outside the markers — setup, debug, rollback, hand-written test invocations — is untouched. Report the delta (`+2 added, −1 dropped`).

**Without markers** (an older COMMANDS.md with no VERIFY markers): do **not** restructure the file. Reconcile and report only — list verify lines in SPEC with no counterpart in COMMANDS.md, and commands under `## Validation` matching no surviving task — then offer to insert the markers around the existing Validation block as a separate confirmed edit. A file whose layout the user chose is not silently rewritten to suit the tool.

**`--light` features** have no COMMANDS.md; there is nothing to reconcile and none is created.

Tasks appended by `/begin-dev --next` are ordinary tasks and are indistinguishable here — deliberately. They are re-planned, preserved, or dropped on their merits like any other, and the COMMANDS reconciliation keeps the verify sweep honest either way.

## Flags

| Flag | Effect |
|------|--------|
| `--from-research` | Source from research doc instead of context |
| `--light` | SPEC.md only; no INDEX/COMMANDS |
| `--refresh` | Rewrite SPEC.md in place (archived first), preserving progress and per-task lines; reconcile COMMANDS.md `VERIFY` block |

---

## Templates Used

- Feature INDEX: `~/.claude/claude-dev-loop/templates/development-feature.md`
- Plan: `~/.claude/claude-dev-loop/templates/development-plan.md`
- Progress log: `~/.claude/claude-dev-loop/templates/development-progress.md`
- Commands: `~/.claude/claude-dev-loop/templates/development-commands.md`

---

## Relationship to Other Commands

```
[research notes]     -> research/{topic}.md (exploration)
        |
        v
/init-dev --from-research -> development/{feature}/ (promotion + planning)

[context] -> /init-dev -> development/{feature}/ (direct, skip research)
        |
        v
     /init-dev --refresh (updates existing plan)
        |
        v
     /review-dev (security review)
        |
        v
     /close-dev -> docs/ (permanent)
```

---

## Notes

- The grill (step 7) is unconditional — there is no flag to skip it, because it is
  self-limiting: on an unambiguous plan in a familiar codebase it asks nothing and you
  never notice it ran. A flag would get passed reflexively and the step would rot. If
  it starts asking questions that change nothing, the stop test is being ignored — fix
  the test, don't add the flag
- Development docs are gitignored (local only)
- Research files are archived after promotion (recoverable from `.archive/`)
- Always creates directory structure (no single-file option)
- Deliverables table is the key artifact - defines what gets promoted
- PROGRESS.md and COMMANDS.md are operational, never promoted
- Use `/init-dev --refresh` to regenerate SPEC.md on existing development docs
- Run `/review-dev` before implementation for security checks
- Task `Verify:` lines are the load-bearing part of the plan — a runnable check per task, written by the planner. `/review-dev` treats a prose-only Verify as a Warning; `/close-dev` runs them.
- Task `Route:` lines (`{tier} · {effort}`, both written) follow `~/.claude/claude-dev-loop/context/context-agentic.md` → Model Routing and are derived from the Verify line. Defaults only — confirmed at `/review-dev`, turned into a session plan by `/begin-dev` at resume time. They never switch models themselves; the model is chosen at session launch (`claude --model`, `/model`).
- Commit after each task passes its Verify. One task per commit keeps a bad step recoverable.
