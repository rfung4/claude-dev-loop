---
description: Pre-implementation gate review of a development plan/spec — verifies the plan's claims against the codebase, then checks quality, security, scope creep, docs-structure compliance, and task routing. Use after /init-dev and before any code is written, or when the user asks whether a plan is ready, sound, or over-engineered.
argument-hint: <feature> [--focus=all|security|quality|scope]
effort: high
---

# Review Development

Gate review of a development plan before coding begins. A plan is a set of claims
about the codebase — this command verifies them first, then judges what's left.

**When to use:** after `/init-dev`, before implementation.

## Where to run it

Review in a **fresh context**. If this session wrote or edited the plan, delegate
the review to a subagent: the session that produced a plan grades its own reasoning
rather than the artifact, and a model favours its own output. Give the subagent the
dev-doc path and this contract, and take back its findings. Run inline only when
this session did not touch the plan. What makes the review worth anything is
*evidence from the repo* (§2), not a second reading of the prose.

## Context

Read the dev doc FIRST, then `Read` only what its contents trigger. Default is none.

**Never `@`-include these.** `@` expands eagerly and unconditionally, so a
parenthetical condition beside one does nothing — every file would load on
every invocation regardless of `--focus`. Paths are absolute because this
command runs in project repos, not in the toolkit clone:

| Path | Read when |
|------|-----------|
| `~/.claude/claude-dev-loop/context/context-docs.md` | doc structure or promotion is in scope |
| `~/.claude/claude-dev-loop/context/context-security.md` | auth, ACL, input validation, DB changes — forced by `--focus=security` |
| `~/.claude/claude-dev-loop/context/context-agentic.md` | agent/subagent design, or `Route:` lines need checking |

## Arguments

| Arg | Effect |
|-----|--------|
| `$1` | Feature name or development path |
| `--focus=all` | Full review (default) |
| `--focus=security` | Force the security pass regardless of plan contents |
| `--focus=quality` | Task concreteness, acceptance criteria, test strategy |
| `--focus=scope` | Over-engineering and scope creep only |

## Process

### 1. Locate

```
docs/development/{arg}/INDEX.md   → folder feature (read INDEX + SPEC)
docs/development/{arg}/SPEC.md    → --light feature or direct spec review (no INDEX is normal)
docs/development/{arg}.md         → single-file feature
```

Not found → `Development artifact not found. Run /init-dev {arg} first.`

### 2. Verify the plan's claims — before judging anything

Check the plan's assertions against the repo, not against its own prose:

| Claim | How to verify |
|-------|---------------|
| A `file.py:NNN` reference | Read it. Does that line do what the task says? |
| "X already does Y" / any pre-condition | grep it. Pass or fail changes the plan |
| "no other caller" / "only used here" | grep the symbol repo-wide |
| Branch / migration state | `git log`, migration dir — is the stated base real? |
| An existing test named as a guard | Open it. Does it assert what's claimed? |

Report each as **verified / wrong / unverifiable** with the evidence inline
(`orders_repo.py:237 — confirms is_archived = False`). A wrong claim
is a Blocker no matter how good the rest of the plan is; a verified pre-condition
should become a regression test rather than staying an assumption.

This pass is where the review earns its keep. Do not skip it to save tokens.

### 3. Coverage

Map both directions, report the gaps:

- every acceptance criterion → the task(s) satisfying it — uncovered is a **Blocker**
- every task → the criterion or deliverable it serves — unmotivated is a **Warning** (usually scope creep)
- every unchecked Open Question → is any task depending on its answer? If so it is a
  **Blocker** unless the plan converts it into a task ("settle X against the real data
  before task N"). Questions carried silently into implementation get answered by
  whatever the implementer assumes. Post-grill, an untagged question is itself a
  **Warning** — it should carry `blocked on: <who>` or have become a Decision
- every `## Decisions` row → the task or `Verify:` implementing it — a decision nothing
  acts on is a **Warning** (it was recorded and then dropped). A task contradicting a
  Decision is a **Blocker**; the Rejected column is what makes that checkable

### 4. Judge what's left

Run only the sections the plan triggers. For each one skipped, state
**"N/A — <why>"** in a single line. Never emit an all-Pass table for a dimension
the plan doesn't touch.

**Plan quality** — vague tasks ("update the API"), unmeasurable acceptance criteria
("should be fast"), risks without mitigations, implicit dependencies. **Every task
must carry a runnable `Verify:`** (a command or a named test file). Prose-only Verify
→ Warning with the runnable form suggested. A named test → open it (§2) and confirm
it asserts the task's criterion. Missing `## End-to-end check` → Warning. The check
is written here, by the plan, so the implementing session runs it rather than
inventing its own — supplied checks move outcomes; self-written ones don't.

**Security** — only when the plan touches auth, ACL, user data, input handling,
migrations, or external I/O. Then: authorization checks, input validation, error
messages leaking internals, secrets, rate limiting, IDOR. For ACL work, red-green
the deny cases first (`context-security.md`).

**Scope** — future-proofing, an abstraction with one implementation, gold-plating,
premature optimization, adjacent features that arrived uninvited.

**Docs structure** — ≤4 files, INDEX.md under 3KB and self-contained, under 10KB total,
deliverables mapped to promotion targets.

**Routing** — `Route:` lines follow `context-agentic.md` → Model Routing and are
derived from each task's `Verify:`. Flag: a task routed below the workhorse tier
with a prose-only Verify (nothing downstream will catch a cheap model's plausible-wrong
output); security/migration tasks on the value tier; Fable on auth-adjacent work;
routing **inherited from an earlier dev doc** instead of derived here. A `Sessions:`
header is legacy — note it as an Observation; `/begin-dev` computes the split now.
Missing `Route:` lines are an Observation. Routing in spec text switches nothing.

**Report only what affects correctness or a stated requirement.** A reviewer asked
for gaps will always produce some; unbounded findings turn into defensive
over-engineering downstream. Style preferences are not findings.

### 5. Report

Three severities, no numeric score.

| Severity | Means |
|----------|-------|
| **Blocker** | Wrong claim, uncovered acceptance criterion, or a correctness/security defect — implementation would build the wrong thing |
| **Warning** | Real but survivable; fold into SPEC and proceed |
| **Observation** | Worth knowing; no action required |

Each finding carries: location (`file:section`), what is wrong, why it matters, the
specific fix.

**Verdict** follows from the findings, not from feel:

| Verdict | Condition |
|---------|-----------|
| **Blocked** | ≥1 Blocker, or any claim that could not be verified |
| **Ready with notes** | Warnings only |
| **Ready** | Neither |

### 6. Land the findings

The review is not a document. Offer, then on the user's go-ahead:

- fold Warnings into SPEC.md as inline notes **at the point they apply**
  (`**Deny-first (review W2):** …`), so implementation meets them in place
- add one line to PROGRESS.md: date, verdict, what was fixed
- for Blockers that change the plan's shape, `/init-dev --refresh` re-plans in place
  and preserves `Route:` lines and PROGRESS.md

Do not write a standalone review-report file.

## See Also

- `/init-dev --refresh` — re-plan in place after blockers
- `/begin-dev` — resume in a fresh session; the natural sibling of this gate
- `/close-dev` — after implementation; its compliance pass is this review's mirror (diff vs acceptance criteria)
- `~/.claude/claude-dev-loop/context/context-security.md` — security principles (library, not a command)

*Full spec: `~/.claude/claude-dev-loop/specs/review-dev.md`*
