# Review Development — Full Specification

Reference and rationale for `/review-dev`. The command file
(`~/.claude/claude-dev-loop/commands/review-dev.md`) is the contract the model executes; this document
explains why it is shaped that way and holds the detail that would bloat it.

## Purpose

Development plans carry issues that waste implementation time:

- claims about the codebase that are simply wrong
- vague task definitions ("update the API")
- acceptance criteria with no task behind them
- missing security consideration on ACL/data surfaces
- scope creep and over-engineering
- routing inherited from an older dev doc rather than derived

This is the gate that catches them **before** coding begins.

---

## Workflow Position

```
[research notes] → /init-dev → /review-dev → [implement] → /close-dev
                       ↑            ↑
              /init-dev --refresh ──┘  (re-plan in place after blockers)
```

Implementation should not start until the verdict is Ready or Ready with notes.

---

## Design rationale

Four choices in the command exist because the previous design measurably failed.
Measured 2026-07-28 over 130 recorded `/review-dev` invocations and ~200 dev-doc
folders across five repos.

### 1. Fresh context, not the planning session

`/review-dev` almost always ran in the same session that had just run `/init-dev`
(104 vs 130 lifetime invocations). A session grading a plan it just wrote evaluates
its own reasoning, not the artifact. Across all recorded reviews the verdict was
**"Ready/passed" 39 times and "Blocked" zero times**. The gate never once stopped
anything.

The fix is structural, not a stronger instruction: run the review in a subagent, so
a model that has not seen the planning reasoning judges the plan on its own terms.
This mirrors the Writer/Reviewer split — a fresh context reviews better because it
is not biased toward what it just produced.

The command pins `model: opus` (with `effort: high`). The subagent inherits the
session's model, and plans are mostly written on Fable, so reviews were mostly Fable
grading Fable: the same model wrote and reviewed 68 of 78 plans (2026-09-07 → 10-05).
A fixed Opus reviewer removes that for the common case, covers the inline path too,
and costs about half a Fable review ($1.59 vs $3.24 median). Opus-written plans are
still reviewed by Opus; fresh context carries that case, and a conditional
"different model" rule was not worth the branch.

### 2. Verification before judgement

Every high-value finding in the recorded history came from reading the repository,
not from reading the plan:

- an `ADD COLUMN … DEFAULT now()` migration that would take a table lock
- a task base class carrying the fleet's retry policy, so replacing it was not local
- a task scoped to "delete Telegram" that was load-bearing elsewhere
- a pre-condition the plan assumed which, once grepped, held — and became a
  regression test instead of an assumption

None of these were prompted by the old command, which only checked that a
`file:line` reference *existed*, never that it was *correct*. Verification is now
step 2 and mandatory.

### 3. No numeric score

The old command scored plans 0–100 with a deduction table. 56 recorded scores ran
58–100, but **73% landed between 70 and 90**, with the mode split between 84 (×9)
and 87 (×9). The scale resolved in practice to "84ish = ready with notes."

The deductions were never calibrated: −5 per vague task and −3 per missing file ref
put a ten-task plan at −80 before security was considered, so the number was chosen
first and justified afterwards. LLM judges shift scores on prompt phrasing alone and
drift over time without a human-labelled gold set — there is no gold set here, and
84s were being compared across five months.

Severity levels carry the same information honestly. Blocker/Warning/Observation
already existed in the output; only the arithmetic was removed.

### 4. Bounded findings

A reviewer asked to find gaps will report some even when the work is sound. The old
command ran five mandatory checklists against every plan, so a five-line filter
change still produced a security table of Pass/Pass/Pass. Sections are now
conditional with an explicit "N/A — why", and findings are bounded to correctness
and stated requirements.

---

## Input detection

```
docs/development/{arg}/INDEX.md   → folder feature (read INDEX + SPEC)
docs/development/{arg}/SPEC.md    → --light feature (no INDEX — normal) or direct spec review
docs/development/{arg}.md         → single-file feature
```

Not found → `Development artifact not found. Run /init-dev {arg} first.`

---

## Context loading

Read the dev doc first; load context only where its contents trigger it. Never
`@`-include — `@` mentions are extracted by a lexical scan and attached before the
model reads the body, so a parenthetical condition beside one has no effect, and a
surrounding code fence does not suppress expansion either.

| Path | Trigger |
|------|---------|
| `~/.claude/claude-dev-loop/context/context-docs.md` | doc structure / promotion in scope |
| `~/.claude/claude-dev-loop/context/context-security.md` | auth, ACL, input validation, DB changes; forced by `--focus=security` |
| `~/.claude/claude-dev-loop/context/context-agentic.md` | agent/subagent design, or `Route:` checking |

Paths are absolute deliberately. This command runs in project repos, where a
toolkit-relative path resolves to nothing; `install.sh` links the clone to
`~/.claude/claude-dev-loop` so one fixed prefix resolves from any repo, wherever the
toolkit was cloned.

---

## Review dimensions

### A. Claim verification (always)

| Claim | Verification |
|-------|--------------|
| `file.py:NNN` reference | Read the line; confirm it does what the task says |
| "X already does Y", any pre-condition | grep; a failing pre-condition invalidates the task |
| "no other caller", "only used here" | grep the symbol repo-wide |
| Branch / migration state | `git log`, migration directory listing |
| An existing test named as a guard | Open it; confirm the assertion exists |

Each claim resolves to **verified**, **wrong**, or **unverifiable**, with evidence
quoted inline. Wrong → Blocker. Unverifiable → Blocked verdict, because the plan
rests on something nobody can check.

A verified pre-condition is worth converting into a regression test in the plan —
that is the difference between a plan that assumes a property and one that pins it.

### B. Coverage

Bidirectional mapping, reported as gaps only:

| Direction | A gap means |
|-----------|-------------|
| acceptance criterion → task | Nothing implements it — **Blocker** |
| task → criterion / deliverable | Nothing asked for it — **Warning** (scope creep) |
| unchecked Open Question → dependent task | Implementation will answer it by assumption — **Blocker** unless converted into a task |
| unchecked Open Question, no `blocked on:` tag | The grill should have settled it or tagged its owner — **Warning** |
| `## Decisions` row → task / `Verify:` | Recorded, then dropped — **Warning** |
| task → contradicts a `## Decisions` row | The plan is arguing with itself; the `Rejected` column is what makes this checkable — **Blocker** |

### C. Plan quality

| Criterion | Pass | Fail |
|-----------|------|------|
| Task concreteness | `src/auth.py:45` + what changes | "Update auth" |
| Acceptance criteria | "p95 < 200ms" | "Should be fast" |
| Risks | Risk + mitigation | No risks section |
| Dependencies | "Requires X first" | Implicit assumption |
| `Verify:` per task | a command or named test path | prose ("works when run twice"), or absent |
| End-to-end check | one command in SPEC | absent |
| Scope vs size | 3–5 tasks for a small feature | 50 tasks for "small" |

Why `Verify:` is the load-bearing row: supplied, correct checks
raise agent task success ~25pp on SWE-bench Verified; agent-written tests change
nothing measurable. The plan supplies the check; the implementer runs it. A named
test file is a claim — open it under A and confirm the assertion. Research and
sources: `~/.claude/claude-dev-loop/docs/why.md`.

Test approach by feature type: bug fix → test-first (reproduce first); complex
logic → test-first; API endpoint → test-along (unit + integration); quick fix →
test-after, but before merge.

### D. Security — only when triggered

Trigger: auth, ACL, user data, input handling, migrations, external I/O.

- **Authentication** — token/session handling, re-auth on privilege change, session fixation, rate limits on auth endpoints
- **Authorization** — per-object checks, IDOR, cross-tenant reads
- **Input** — validation spec per input, type/size constraints, injection vectors
- **Output** — error messages not leaking internals, response filtering, XSS
- **Data** — sensitive fields identified, PII minimisation, retention
- **ACL features** — red-green the **deny** cases before the gate exists; the value of an ACL is what it keeps out

Risk level: Critical (auth bypass, data exposure, injection) · High (missing input
validation, IDOR) · Medium (no rate limiting, verbose errors) · Low (hardening).

### E. Scope

| Signal | Example |
|--------|---------|
| Future-proofing | "in case we need X later" |
| Unnecessary abstraction | interface with one implementation |
| Gold-plating | features not in the requirements |
| Premature optimisation | "for performance", no metric |
| Scope creep | adjacent features included |

Under-specification is the mirror: no failure modes, no test plan, implicit
dependencies, "and related changes".

### F. docs-structure compliance

| Criterion | Threshold |
|-----------|-----------|
| File count | ≤ 4 |
| INDEX.md | < 3KB, self-contained |
| Total folder | < 10KB |
| Deliverables | every one mapped to a promotion target |

Content quality: INDEX.md understandable without SPEC.md; SPEC.md consolidated
rather than scattered across design/api-changes files; no duplication between them.

### G. Routing

`Route:` lines (`tier · effort`, e.g. `sonnet · medium`; effort optional) are emitted by `/init-dev` per
`context-agentic.md` → Model Routing and are **derived from each task's `Verify:`**.
They are defaults confirmed by the human at this gate and turned into a session
plan by `/begin-dev` at resume time. They never switch models — the model is chosen
at session launch.

The `Sessions:` header was retired: it pre-computed at plan time a
decision that is only actionable at a session boundary, and the evidence for
cost-routing on multi-step coding is thin (no end-to-end study; cheap-executor
failures cost ~4×). What makes routing down safe is a runnable check on the task,
so that is now the routing key.

Flag:

- a task routed below the workhorse tier whose `Verify:` is prose-only
- security/auth/ACL/migration-surface tasks on the value tier
- high/xhigh effort on mechanical work (effort is for reasoning, not typing)
- Fable on auth-adjacent tasks — the safeguard classifier reroutes them anyway
- a legacy `Sessions:` header — Observation; `/begin-dev` computes the split now
- **routing inherited from an earlier dev doc** rather than derived from these tasks

That last one is not hypothetical: a one-off routing instruction propagated verbatim through three
consecutive dev docs, each citing the previous, because nothing re-derived it. Treat a routing block that cites
another dev doc as unreviewed.

Missing `Route:` lines are an Observation, not a blocker.

---

## Output

No score. No standalone report file. Findings, then verdict.

```markdown
# Development Review: {feature}

**Verdict:** Ready | Ready with notes | Blocked
**Focus:** {all|security|quality|scope}
**Context read:** {files, or "none"}

## Claim verification
{claim → verified / wrong / unverifiable, with evidence}

## Coverage
{uncovered criteria; unmotivated tasks. "Complete" if neither}

## Blockers
### 1. {title}
- **Location:** `{file}:{section}`
- **Issue / Impact / Required:** …

## Warnings
### 1. {title}
- **Location / Issue / Suggestion:** …

## Observations
1. …

## {Security | Scope | Docs | Routing}
{findings, or "N/A — <why>" on one line}

## Recommendation
{next step: proceed, fold warnings, or what must change}
```

Verdict rules: **Blocked** if any Blocker or any unverifiable claim; **Ready with
notes** if only Warnings; **Ready** otherwise.

---

## Landing the findings

Reviews leave no report artifact — none of the 130 recorded runs produced one, and
the convention that emerged instead works better:

1. **Warnings fold into SPEC.md inline**, at the point they apply, tagged with the
   review: `**Deny-first (review W2):** red-green the deny cells BEFORE …`.
   Implementation meets the finding where it is relevant, instead of in a document
   it will not reopen.
2. **One PROGRESS.md line** records date, verdict, and what was fixed.
3. **Blockers that change the plan's shape** go through `/init-dev --refresh`, which
   re-plans in place and preserves `Route:` lines and PROGRESS.md.

Offer these; apply on the user's go-ahead. Never edit the plan silently as part of
a review.

---

## Focus modes

| Mode | Effect |
|------|--------|
| `all` | Default. Verification + coverage always; other sections as triggered |
| `security` | Force section D regardless of contents; read `context-security.md` first; require an explicit security section in the plan; add OWASP alignment and credential handling |
| `quality` | Deep-dive C: task-by-task assessment, suggested rewrites, missing test scenarios |
| `scope` | Section E only: complexity vs feature description, simplification suggestions |

Verification (A) and coverage (B) run under every mode. They are what the review is.

---

## Iteration

```
/init-dev feature
  ↓
/review-dev feature            → Blocked
  ↓
fold warnings / /init-dev --refresh feature
  ↓
/review-dev feature            → Ready with notes
  ↓
implement → /close-dev feature
```

---

## See Also

- `/init-dev --refresh` — regenerate an implementation plan in place
- `/begin-dev` — fresh-session resume; the same fresh-context principle
- `~/.claude/claude-dev-loop/context/context-security.md` — security principles (library, not a command)
- `~/.claude/claude-dev-loop/context/context-docs.md` — structure and efficiency principles
