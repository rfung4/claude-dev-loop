# Docs — where documentation goes

Library, not a command. Read when deciding where a piece of documentation belongs or how a `docs/development/` folder should be shaped.

---

## Principles (the ones that change decisions)

1. **Document when it hurts, not on a schedule** — after 30 min of debugging, after explaining something twice. Capture the *decision and why*; facts age faster.
2. **Promotion workflow:** `research/` (messy, gitignored) → `development/` (structured WIP, gitignored) → `docs/` (permanent). research note → `/init-dev` → `/review-dev` → implement → `/close-dev`. `/init-dev --refresh` re-plans in place.
3. **Four INDEX.md hubs only:** `docs/`, `schema/`, `api/`, `ops/`. No others.
4. **Archive before delete.** Untracked = unrecoverable. `docs/.archive/{timestamp}/` first, always.
5. **Status is a commitment:** 🔴 Open · 🟡 In progress · 🟢 Done · ⚫ Blocked.

---

## Where does this go?

| Situation | Goes to |
|-----------|---------|
| Got bitten by something | `notes/{topic}.md` (flat; `**Severity:**` header) |
| Evaluating options, no decision yet | `research/{topic}.md` (local) |
| Decision made, ready to build | `/init-dev {feature}` (or `--light` for small multi-step work) |
| Feature complete | `/close-dev` → promote + archive |
| Process / runbook | `ops/{process}.md` |
| API patterns | `api/conventions.md` |
| Schema change | `schema/{entity}.md` + update its INDEX |
| Reusable technical truth (not project-specific) | a personal knowledge base — not project docs |
| A correction to how Claude works | rule / skill / hook, not a doc |

---

## `docs/development/{feature}/` shape

```
INDEX.md      # status, decisions, deliverables → targets. LINKS to SPEC's tasks; never copies them
SPEC.md       # the plan: tasks with Verify: + Route:, acceptance criteria, e2e check, out-of-scope
PROGRESS.md   # **Current task:** line under the H1; dated log
COMMANDS.md   # every Verify: + the e2e check, runnable
```

- `--light` = SPEC.md only. One-sentence diffs get no dev doc at all.
- ≤4 files, <10KB total, INDEX.md <3KB and readable without SPEC.md. Agents read docs before code — a bloated dev doc steals tokens from the codebase.
- Reference code by `path:line`; never embed implementations. No duplicated diagrams or task lists across files.
- Deliverables table in INDEX.md is the promotion contract for `/close-dev`. PROGRESS.md and COMMANDS.md are operational, never promoted.

---

## Anti-patterns

| Don't | Do instead |
|-------|------------|
| Document everything upfront | Capture when you learn something hard |
| `@`-include doc directories from a command | Text pointer; `@` is eager and unconditional |
| Let `research/` accumulate | Promote decided items, archive abandoned |
| Create a fifth INDEX.md | Use the four hubs |
| Write "obvious" docs | Trust code clarity; document the non-obvious only |
| Two files describing one thing | Single source of truth per concern |

---

## See Also

- `~/.claude/claude-dev-loop/context/context-agentic.md` → Context Management — why dev docs are sized the way they are
