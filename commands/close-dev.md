---
description: Close out finished development work — promote deliverables to permanent docs/, write a completion report, archive the dev doc. Use when a feature is done and tests pass, or the user says they're finished with a dev doc. Confirm the feature name before running.
argument-hint: <feature> [--skip-report] [--skip-tests] [--partial] [--force] [--dry-run]
effort: medium
---

# Close Development

Complete a development effort: promote documentation, generate completion report, archive files.

**Final step:** `/init-dev` → `/review-dev` → [implement] → `/close-dev`

## What It Does

1. **Verify** - Run the SPEC's `Verify:` lines + end-to-end check; then a fresh-context compliance pass of the diff against the acceptance criteria
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
2. Pre-flight validation (sources exist, targets valid)
3. Run every `Verify:` in SPEC.md (via COMMANDS.md) and the `## End-to-end check`. Any failure → stop unless `--force`
4. **Compliance pass — fresh subagent, never inline.** Input: SPEC.md acceptance
   criteria + task list, and `git diff <base>..HEAD` (base = branch point or the
   first commit after PROGRESS "Planned"). Output, per criterion: implemented /
   partial / missing, with the evidence line; plus every changed file no task
   names. Correctness and scope only — *a reviewer asked for gaps will find some;
   style is not a finding.* Missing criterion → stop unless `--partial`.
   Out-of-scope changes → listed in the report, not blocked
5. Promote deliverables (`create` or `merge`)
6. Update status to 🟢
7. Generate completion report (includes verify results + compliance table)
8. Archive to `.archive/`
9. Check that docs/ INDEX files are current

## Report Contents

Generated in `docs/report/{feature}.md`:
- Summary of what was built
- Key decisions with rationale
- Files changed
- Deliverables promoted
- Verify results (per task + e2e) and the compliance table (criterion → implemented / partial / missing; out-of-scope changes)
- Lessons learned
- Time tracking (if PROGRESS.md has entries)

## Example

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
