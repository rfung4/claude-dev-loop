---
description: Create a docs/development/{feature}/ structure with an AI-generated implementation plan. Use when the user says to plan work, make a dev doc, start structured work on a decided feature, or "let's plan this" / "make a fresh plan here"; --light (SPEC.md only) is the normal case — full INDEX/PROGRESS structure is earned by multi-session work or a deliverable to promote; --refresh re-plans an existing dev doc when scope shifted. If the diff fits in one sentence, don't plan — just do it.
argument-hint: <name> [--from-research] [--light] [--refresh]
effort: high
---

# Initialize Development

Create a development structure in `docs/development/` with AI-powered planning.

**Workflow:** `docs/research/{topic}.md` -> `/init-dev` -> `/review-dev` -> [implement] -> `/close-dev`

## Arguments

| Arg | Effect |
|-----|--------|
| `$1` | Feature name in kebab-case (required) |
| `--from-research` | Source from `docs/research/{name}.md` |
| `--light` | SPEC.md only (+ PROGRESS.md if multi-session). No INDEX |
| `--refresh` | Regenerate SPEC.md for an existing dev doc (scope shifted mid-flight) |

## Modes

Pick by what will **outlive** the work, not by how important it feels. `--light` is the
normal choice; full structure has to be earned by *at least one* of: the work spans more
than one session, or it produces a deliverable to promote into `docs/`. One ticket, one
sitting, nothing to promote → `--light`. Unearned structure becomes a stale SPEC that
lies to the next session.

| Mode | When to Use |
|------|-------------|
| _(don't invoke)_ | Diff fits in one sentence — planning is overhead, just do it |
| `--light` | **Normal case.** Multi-step, one sitting, nothing to promote — the SPEC is the whole artifact |
| Full | Earned: multi-session **or** has deliverables to promote into `docs/` |
| `--from-research` | Research complete, ready to promote |
| `--refresh` | Dev doc exists, plan is stale — re-plan without losing progress |

**Size is decided after the codebase look (step 5), not before.** A SPEC is ≤10 tasks and
≤10 KB. If the draft task list exceeds either, stop: split the feature, or write one line
under `## Summary` saying why this one earns more. A draft of ≤2 tasks is the "don't invoke"
row arriving late — say so and offer to just do the work instead of writing a SPEC.

## Process

1. Check prerequisites (development/ exists). On name collision: stop and
   suggest `--refresh` — never silently overwrite an existing dev doc.
2. Source content (context or research file)
3. Determine deliverables (-> architecture/, api/, schema/, notes/)
4. Create structure: INDEX.md, SPEC.md, PROGRESS.md (`--light`: SPEC.md only). INDEX.md links to SPEC's task list — never duplicates it. COMMANDS.md is not generated; the SPEC's `Verify:` lines are the collection
5. Run codebase analysis
6. **Draft the task list** — titles and impacted files only, no details, no Verify lines yet. This is the input to the grill, not an artifact; it is never written to disk
7. **Grill.** Ask about anything whose answer would change a task, a file, or a `Verify:` line — nothing else. One question at a time, each carrying a recommended answer and a one-line reason. **Asking zero questions is a valid and common outcome; never manufacture one.** Answers land in `## Decisions`. Full contract: `~/.claude/claude-dev-loop/specs/init-dev.md` → The grill
8. Generate SPEC.md. **Every task carries a `Verify:` line — a command or a named test file, written by the planner, never prose** ("run twice → zero-line diff" is prose; `python scripts/x.py --check` is a check). The plan ends with one `## End-to-end check`. A task runs on the session's model and carries **no `Route:`** unless it is an exception (`~/.claude/claude-dev-loop/context/context-agentic.md` → Model Routing): its Verify can check shape but not correctness → `Route: fable · high`; it is the **keystone** (large, ≥3 later tasks build on its interfaces; at most 2 per plan) → append `· keystone` to the task title so the session runs it at `/effort xhigh`. Never `fable · max`. No `Sessions:` header
9. Unchecked Open Questions that a task depends on must be resolved or turned into a task before the plan is done. After the grill, what remains here is only what could not be settled in this room — tag each with who unblocks it (client, prod data, a third party)
10. Update INDEX files (archive research if `--from-research`)

**`--refresh` differs at steps 4, 7 and 8:** it rewrites SPEC.md only. PROGRESS.md and
completed task checkmarks are preserved, and every surviving task keeps its existing
`Route:` and `Verify:` lines (re-derive only for genuinely new tasks). The grill covers
only the delta — existing `## Decisions` rows are inputs, not re-litigated.

**Archive first** (`docs/development/` is gitignored — an overwrite is unrecoverable):

```bash
ARCHIVE_DIR="docs/.archive/$(date +%Y%m%d_%H%M%S)" && mkdir -p "$ARCHIVE_DIR" && cp docs/development/{feature}/SPEC.md docs/development/{feature}/COMMANDS.md "$ARCHIVE_DIR/" 2>/dev/null
```

**COMMANDS.md is legacy** (no longer generated). If the doc has one with
`<!-- MERGE_START(VERIFY) -->` markers, replace the block from the new SPEC and report
`+N / −N`; without markers, reconcile and report only. Never create the file.

## Example

```
> /init-dev user-preferences

Analyzing context...
Found: JSON column decision, models/user.py, api/preferences.py

Deliverables:
  1. SPEC.md (design) -> architecture/user-preferences.md

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
  - INDEX.md (populated)
  - SPEC.md (6 tasks, each with Verify:; task 3 · keystone; 2 Decisions)
  - PROGRESS.md

Next: /review-dev user-preferences
```

```
> /init-dev fix-retry-backoff --light

Created: development/fix-retry-backoff/SPEC.md (3 tasks)
No INDEX — the SPEC is the artifact.

Next: /review-dev fix-retry-backoff
```

```
> /init-dev user-preferences --refresh

Archived: docs/.archive/20260912_170430/ (SPEC.md)

Re-planned: 6 tasks → 7 (2 new, 1 dropped, 4 preserved with their Verify:)

Next: /review-dev user-preferences
```

```
> /init-dev auth-system --from-research

Found: docs/research/auth-strategy.md (decided)

Created: development/auth-system/
Archived: research/auth-strategy.md

Next: /review-dev auth-system
```

## See Also

- `/review-dev` - Security review before implementation
- `/close-dev` - Complete development work

*Full spec: `~/.claude/claude-dev-loop/specs/init-dev.md`*
