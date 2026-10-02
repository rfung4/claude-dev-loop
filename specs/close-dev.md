# Close Development

Complete a development effort by promoting documentation to permanent locations, generating a completion report, and archiving the development files. This is the final step in the dev loop.

**Workflow:**
```
[research notes] → /init-dev --from-research → /review-dev → [implement] → /close-dev
                   /init-dev                  → /review-dev → [implement] → /close-dev
                                                                             ↓
                                                               docs/ (permanent)
                                                               report/ (tracking)
                                                               .archive/ (backup)
```

## What This Command Does

1. **Promote** - Move deliverables to permanent docs (architecture/, api/, etc.)
2. **Report** - Generate completion summary in `report/`
3. **Archive** - Move development files to `.archive/`

## Arguments

- `$1` - Feature name (optional, will prompt if not provided)
- `--skip-report` - Skip report generation
- `--skip-tests` - Skip test verification
- `--partial` - Allow closing with unpromoted deliverables (generates report noting incomplete items)
- `--force` - Continue even if tests fail (failure noted in report)
- `--dry-run` - Show what would happen without executing

## Prerequisites

- Development item must exist
- No deliverable still 🔴 (not started) unless `--partial` used
- `docs/report/` directory exists (created if missing)

## Process

### 1. Locate Development Item

```bash
docs/development/{arg}/INDEX.md  # Development feature (directory)
docs/development/{arg}/SPEC.md   # --light feature: no INDEX, no deliverables table — verify, report, archive only
```

### 2. Pre-flight Validation

Validate all deliverables before any operations:

```
Pre-flight validation...

[1] design.md → architecture/user-prefs.md (create)
    ✓ Source exists
    ✓ Target directory exists
    ✓ No conflicts

[2] api-changes.md → api/users.md (merge)
    ✓ Source exists
    ✓ Target exists

All validations passed.
```

### 2b. Verify

Run every task `Verify:` line from SPEC.md (COMMANDS.md collects them) and the
`## End-to-end check`. These were written by the plan, so they are the contract:
a task whose Verify fails is not done, whatever the checkbox says. Legacy dev
docs without `Verify:` lines fall back to the COMMANDS.md pytest line:

```
Test verification...

Found: COMMANDS.md with pytest commands

Running: pytest tests/unit/test_preferences.py -v
======================== test session starts =========================
tests/unit/test_preferences.py::test_create_preference ✓
tests/unit/test_preferences.py::test_update_preference ✓
tests/unit/test_preferences.py::test_delete_preference ✓
======================== 3 passed in 0.45s ===========================

Test Status: ✓ All tests passing (3/3)
```

**Test verification behavior:**

| Scenario | Action |
|----------|--------|
| No COMMANDS.md | Skip test verification |
| COMMANDS.md without pytest | Skip test verification |
| Tests pass | Report in completion summary |
| Tests fail | Report failure, prompt to continue |
| `--skip-tests` flag | Skip test verification |
| `--force` flag | Continue even if tests fail |

**If tests fail:**

```
Test verification...

Running: pytest tests/unit/test_preferences.py -v
======================== test session starts =========================
tests/unit/test_preferences.py::test_create_preference ✓
tests/unit/test_preferences.py::test_validation FAILED

FAILED tests/unit/test_preferences.py::test_validation - AssertionError
======================== 1 failed, 1 passed =========================

Test Status: ✗ 1 of 2 tests failing

⚠ Tests are failing. Options:
  - Fix tests and rerun /close-dev
  - Use --force to close anyway (failure noted in report)
  - Use --skip-tests to skip verification

Continue? [y/N]:
```

### 2c. Compliance pass

The mirror of `/review-dev`: that gate checks the plan against the repo before
code; this checks the code against the plan after. Nothing else in the loop
catches scope creep or a quietly-skipped criterion — tests passing says the code
works, not that it is the code the plan asked for.

**Run it in a fresh subagent, never inline.** The session that implemented the
feature grades its own work otherwise, and a model favours its own output.
Hand the subagent only:

- SPEC.md `## Acceptance Criteria` and `## Task Breakdown` (file lists)
- `git diff <base>..HEAD` where base is the branch point, or the first commit
  after the PROGRESS.md "Planned" entry; uncommitted changes included

It returns:

| Criterion | Status | Evidence |
|-----------|--------|----------|
| {AC 1} | implemented / partial / missing | `file:line` or test name |

plus "Changed outside the plan: {files no task names}".

Bounds: correctness and scope only. A reviewer prompted to find gaps will find
some — style, naming, and "could be cleaner" are not findings. `missing` → stop
unless `--partial`; out-of-plan files → reported, not blocked (they may be
legitimate — the report is where the human decides).

Evidence grade: this is vendor-recommended practice (Anthropic: "review the diff
against PLAN.md… report gaps, not style") with no measured effect size. It is kept
because it is cheap and is the only scope check in the loop.
See `~/.claude/claude-dev-loop/docs/why.md`.

### 3. Promote Deliverables

Execute promotions per the deliverables table:

| Action | Behavior |
|--------|----------|
| `create` | Copy source to target |
| `merge` | Append with separator |
| `merge-at-marker(X)` | Replace between markers |

Update each deliverable status to 🟢 with date.

### 4. Update Target INDEX Files

Add entries to INDEX.md files in affected directories (best-effort).

### 5. Generate Completion Report

Create `docs/report/{feature}.md`:

```markdown
# Report: {Feature Name}

**Completed:** {date}
**Duration:** {created_date} → {completed_date}
**Status:** Complete | Partial

---

## Summary

{AI-generated summary of what was built, key decisions, approach taken}

---

## What Was Done

- Created user preferences system with JSON storage
- Added API endpoints for CRUD operations
- Implemented validation with Pydantic schemas
- Added migration for existing users

---

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| JSON column vs separate table | Simpler, sufficient for unstructured prefs |
| No caching | Low traffic, premature optimization |

---

## Files Changed

| File | Change |
|------|--------|
| src/models/user.py | Added preferences field |
| src/api/preferences.py | New endpoint (created) |
| src/schemas/preferences.py | New schema (created) |
| migrations/20260106_user_prefs.py | New migration |

---

## Deliverables Promoted

| Source | Target | Status |
|--------|--------|--------|
| design.md | → architecture/user-prefs.md | ✓ Promoted |
| api-changes.md | → api/users.md | ✓ Merged |

---

## Lessons Learned

{Extracted from development notes, gotchas encountered}

- JSON field requires explicit `default={}` to avoid None issues
- Pydantic's `model_dump()` replaced deprecated `dict()` in v2

---

## Compliance

| Criterion | Status | Evidence |
|-----------|--------|----------|
| User can read/write preferences via API | implemented | tests/api/test_preferences.py::test_roundtrip |

Changed outside the plan: none

## Test Results

**Status:** ✓ Passed (12/12)

```bash
$ pytest tests/unit/test_preferences.py -v
======================== test session starts =========================
tests/unit/test_preferences.py::test_create_preference ✓
tests/unit/test_preferences.py::test_update_preference ✓
tests/unit/test_preferences.py::test_delete_preference ✓
tests/unit/test_preferences.py::test_validation ✓
======================== 12 passed in 0.45s ==========================
```

| Test File | Tests | Status |
|-----------|-------|--------|
| test_preferences_crud | 8 | ✓ Passed |
| test_preferences_validation | 4 | ✓ Passed |

---

## Time Tracking (Optional)

{If PROGRESS.md had time entries}

| Date | Hours | Notes |
|------|-------|-------|
| 2026-01-04 | 2.0 | Initial implementation |
| 2026-01-05 | 1.5 | API endpoints |
| 2026-01-06 | 1.0 | Tests and cleanup |
| **Total** | **4.5** | |

---

## References

- Development: .archive/{timestamp}/user-preferences/
- Plan: .archive/{timestamp}/user-preferences/SPEC.md
- Research: .archive/{earlier}/user-preferences-research.md (if applicable)
```

### 6. Archive Development Files

```bash
ARCHIVE_DIR="docs/.archive/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$ARCHIVE_DIR"
mv docs/development/{feature}/ "$ARCHIVE_DIR/"
```

### 7. Update development/INDEX.md

Remove the entry from the tracking table:
```markdown
# Before:
| 🟡 In Progress | {feature} | 2026-01-15 | Implementation |

# After: (row removed)
```

### 8. Run Validation

Check that the docs/ INDEX files are current — no row or link still points at the archived feature.

### 9. Report Summary

```
Closed: user-preferences

Promoted:
  ✓ design.md → docs/architecture/user-prefs.md
  ✓ api-changes.md → docs/api/users.md (merged)

Report generated:
  → docs/report/user-preferences.md

Archived:
  → docs/.archive/20260106_143022/user-preferences/

Updated INDEX files:
  - docs/architecture/INDEX.md
  - docs/api/INDEX.md
  - docs/development/INDEX.md (removed entry)

Feature complete!
```

## Partial Closure

With `--partial`, close even if some deliverables aren't ready:

```
> /close-dev user-preferences --partial

Warning: 1 deliverable not ready:
  - schema-changes.md (pending)

Continue with partial close? [y/N]: y

Promoted: 2/3 deliverables
Skipped: schema-changes.md (noted in report)

Report generated with partial status.
Archived development files.
```

Report will note:
```markdown
**Status:** Partial

## Not Completed
- schema-changes.md → schema/user.md (deferred)
```

## Report Generation Details

The report is AI-generated from:

| Source | Extracts |
|--------|----------|
| INDEX.md | Background, deliverables, status |
| SPEC.md | Tasks completed, decisions |
| PROGRESS.md | Time entries, daily notes |
| COMMANDS.md | Test commands run |
| Deliverable files | Content summaries |
| Git log | Files changed (if available) |

**Report includes:**
- What was built (summary)
- Key decisions with rationale
- Files changed
- Deliverables promoted
- Lessons learned (from notes/gotchas)
- Tests added (if any)
- Time tracking (if PROGRESS.md has entries)

## Flags

See [Arguments](#arguments) — the same five flags as the command.

## Example Usage

### Standard Close

```
> /close-dev user-preferences

Found: development/user-preferences/ (2 deliverables, all ready)

Pre-flight validation... ✓

Test verification...
  Running: pytest tests/unit/test_preferences.py -v
  ✓ All tests passing (12/12)

Promoting deliverables...
  ✓ design.md → architecture/user-prefs.md
  ✓ api-changes.md → api/users.md

Generating report...
  ✓ Created: docs/report/user-preferences.md

Archiving...
  ✓ Moved to: docs/.archive/20260106_143022/

Validation check... ✓

Feature closed!
```

### Skip Report

```
> /close-dev quick-fix --skip-report

Promoting 1 deliverable...
  ✓ fix.md → notes/redis-gotcha.md

Archiving...
  ✓ docs/.archive/20260106_150000/quick-fix.md

Done. (No report generated)
```

### Dry Run

```
> /close-dev user-preferences --dry-run

Would promote:
  - design.md → architecture/user-prefs.md (create)
  - api-changes.md → api/users.md (merge)

Would generate:
  - docs/report/user-preferences.md

Would archive:
  - development/user-preferences/ → .archive/20260106.../

No changes made.
```

## Directory Structure

After `/close-dev`:

```
docs/
├── architecture/
│   └── user-prefs.md      ← promoted
├── api/
│   └── users.md           ← merged
├── report/                 ← NEW (gitignored)
│   └── user-preferences.md ← completion report
├── development/
│   └── INDEX.md           ← entry removed
└── .archive/               ← backup
    └── 20260106_143022/
        └── user-preferences/
            ├── INDEX.md
            ├── PROGRESS.md
            └── SPEC.md
```

## Notes

- `/close-dev` is the standard end-of-feature command
- Reports are gitignored (local tracking only)
- Archive preserves full development history
- Use `--partial` for abandoned or deferred features
- Reports can be used for billing, retrospectives, weekly summaries
- Time tracking is optional - only included if PROGRESS.md has entries
