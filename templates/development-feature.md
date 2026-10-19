# Feature: {FEATURE_NAME}

**Created:** {DATE}
**Status:** 🔴 Not Started
**Source:** research/{source}.md (archived)

---

## Current Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1 | 🔴 Not Started | {description} |
| Phase 2 | 🔴 Not Started | {description} |

**See also:** [Progress Log](PROGRESS.md)

---

## Background

{Key findings and context from research phase. This section is auto-populated by /init-dev from the research file's "Key Findings" or "Decision" sections (when using --from-research) or from conversation context (default).}

---

## Blockers & Decisions

| Date | Type | Description | Resolution |
|------|------|-------------|------------|
| | blocker | | |
| | decision | | |

---

## Deliverables

Map each piece of documentation to its target location in docs/.

| Status | Source | Target | Action |
|--------|--------|--------|--------|
| 🔴 | design.md | → architecture/{feature}.md | create |
| 🔴 | api-changes.md | → api/{resource}.md | merge |
| 🔴 | schema-changes.md | → schema/{entity}.md | create |
| 🔴 | gotchas.md | → notes/{topic}.md | create |

**Actions:**
- `create` - Create new file at target (fails if exists)
- `merge` - Append to existing file with separator
- `merge-at-marker(NAME)` - Replace content between `<!-- MERGE_START(NAME) -->` and `<!-- MERGE_END(NAME) -->` markers

**Status:**
- 🔴 Not started
- 🟡 In progress - being written, not yet promoted
- 🟢 Done - promoted to docs/ by `/close-dev`

---

## Implementation Plan

Tasks, per-task `Verify:` checks, routing, acceptance criteria and the end-to-end
check live in [SPEC.md](SPEC.md). **Do not copy the task list here** — one source
of truth; this file links to it. Current task is the **Current task** line near the top of
[PROGRESS.md](PROGRESS.md) (under the title), not line 1.

### Open Questions

- [ ] Question that needs resolution

---

## Working Notes

{Scratch space for notes during implementation. Not promoted.}

---

## Files

**Preferred (3-4 files max for LLM efficiency):**

```
development/{feature}/
├── INDEX.md       # This file - status, decisions, deliverables (READ FIRST; tasks live in SPEC.md)
├── SPEC.md        # Single technical spec (architecture, API, schema combined)
└── PROGRESS.md    # Daily log (optional, for multi-day work)

COMMANDS.md is legacy: no longer generated. Verify: lines live in SPEC.md.
```

**Avoid:**
- Separate design.md, api-changes.md, schema-changes.md → consolidate into SPEC.md
- source/ subdirectory with multiple specs → single SPEC.md
- Duplicating architecture diagrams or task lists across files
- Embedding full code implementations → reference by path

**Why:** A 5+ file structure costs ~8K tokens before any code is read. Keep INDEX.md self-contained (~2-3KB) so LLM can understand feature without reading everything.

Create only the files you need. Delete unused entries from Deliverables table.
PROGRESS.md is scaffolded but not promoted to docs/.
