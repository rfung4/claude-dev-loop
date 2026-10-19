---
description: Close out finished development work — promote deliverables to permanent docs/, write a completion report, archive the dev doc. Use when a feature is done and tests pass — on the feature branch, before the PR — or the user says they're finished with a dev doc. Confirm the feature name before running.
argument-hint: <feature> [--skip-report] [--skip-tests] [--partial] [--force] [--dry-run]
effort: medium
---

# Close Development

Complete a development effort: promote documentation, generate completion report, archive files.

**Workflow:** `/init-dev` → `/review-dev` → [implement] → `/close-dev` → commit → PR

Run it on the feature branch **before** the PR: promotions stay uncommitted so they go in the feature's PR, and a `missing` criterion can still block the merge. Closing after the merge is what spawns docs-only follow-up PRs.

## What It Does

1. **Verify** - Run the SPEC's `Verify:` lines + end-to-end check; then review the branch diff with the `code-review` skill and list every changed file no task names
2. **Promote** - Move deliverables to permanent docs/
3. **Report** - Generate completion summary in `docs/report/`
4. **Archive** - Move development files to `.archive/`

## Arguments

| Arg | Effect |
|-----|--------|
| `$1` | Feature name |
| `--skip-report` | Skip report generation |
| `--skip-tests` | Skip test verification |
| `--partial` | Allow unpromoted deliverables |
| `--force` | Continue even if tests fail |
| `--dry-run` | Show what would happen |

## Process

1. Locate development item (`{arg}/INDEX.md`; fall back to `{arg}/SPEC.md` for `--light` features)
2. Pre-flight validation (sources exist, targets valid). If the feature already merged — HEAD is
   in the remote default branch and nothing outside `docs/` is uncommitted — say so in one line
   (promotions will need their own commit) and continue
3. Run every `Verify:` in SPEC.md and the `## End-to-end check` (COMMANDS.md's pytest line only on a legacy doc whose SPEC carries no per-task `Verify:`). Any failure → stop unless `--force`
4. **Diff review.** Invoke the `code-review` skill (Skill tool, level `high`) on
   `git diff <base>..HEAD` (base = branch point or the first commit after PROGRESS
   "Planned"; uncommitted changes included). It is a fresh context by construction.
   Take its correctness findings; then list every changed file no task names.
   A Blocker-grade finding → stop unless `--force`. Out-of-plan files → listed in the
   report, not blocked. Replaces a compliance subagent that stopped
   nothing in 31 runs; the review that caught a real break was a diff review
5. Promote deliverables (`create` or `merge`) — leave them uncommitted for the feature's commit
6. Update status to 🟢
7. Generate completion report (includes verify results + review findings)
8. Archive to `.archive/`

## Report Contents

Generated in `docs/report/{feature}.md`:
- Summary of what was built
- Key decisions with rationale
- Files changed
- Deliverables promoted
- Verify results (per task + e2e), the code-review findings and how each was resolved, and files changed outside the plan
- Lessons learned
- Time tracking (if PROGRESS.md has entries)

## Example

```
> /close-dev user-preferences

Found: development/user-preferences/ (2 deliverables)

Pre-flight... ✓
Verify (6 tasks + e2e)... ✓
Code review (high)... 0 findings; 1 file outside plan: src/utils/fmt.py (noted)

Promoting:
  ✓ design.md → architecture/user-prefs.md
  ✓ api-changes.md → api/users.md

Report: docs/report/user-preferences.md
Archived: docs/.archive/20260106_143022/

Feature complete!
```

```
> /close-dev user-preferences --partial

Warning: 1 deliverable not ready
Continue? [y/N]: y

Promoted: 2/3 deliverables
Report notes partial status.
```

## See Also

- `/init-dev --refresh` - Regenerate implementation plan

*Full spec: `~/.claude/claude-dev-loop/specs/close-dev.md`*
