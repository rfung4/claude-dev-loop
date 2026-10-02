# Why the loop looks like this

**In short:** the loop keeps the plan on disk with a runnable check per task, reviews it against
the codebase in a fresh context, and checks the diff against it at the end. Of the mechanics
it relies on, only planner-supplied per-task checks are well supported by research; the others
rely on vendor guidance and field use, and are labelled that way below.

This is the evidence review behind `/init-dev` → `/review-dev` → `/begin-dev` → `/close-dev`,
run in August 2026 once the loop had been in daily use long enough to have habits worth
questioning. It is kept here because it explains the parts that look odd at first sight — why
every task carries a `Verify:` line, why the review insists on a fresh context, why `--light`
is the default — and because it records what was cut, not just what was kept.

**Method:** four parallel research passes (Anthropic's own guidance · spec-driven tooling ·
practitioner workflows · research literature), about 60 sources, compared against the four
command files, their specs, and a real dev doc produced by the loop. A second pass then
fact-checked the five mechanics the recommendations depend on (below).

## The question

Is this planning loop in line with what Anthropic and the strongest practitioners do in 2026,
and where does it lag?

## The 2026 consensus

1. **Plan in a file, on disk, in the repo.** Spec Kit, Kiro, OpenSpec, BMAD and Superpowers all commit it; Claude plan mode and Cursor default to home-dir scratch. Everyone keeps state outside the context window because context gets compacted or truncated.
2. **Having a plan helps, and a check before code is cheap.** The verified finding is that *no* plan hurts ([2604.12147](https://arxiv.org/abs/2604.12147)); the stronger form, that a subpar plan hurts more than none, did not survive verification.
3. **Verify the plan against the repo with a fresh context, using evidence.** Self-review without new evidence is near-worthless (Huang et al. [2310.01798](https://arxiv.org/abs/2310.01798)); judges favour their own output ([2404.13076](https://arxiv.org/abs/2404.13076)). Anthropic (paraphrased): a fresh context improves review because the reviewer isn't biased toward code it just wrote — and gap-finding reviewers always find gaps, so restrict them to correctness.
4. **Each task carries its own pass/fail check.** Correct supplied tests lift resolution sharply (TDFlow: 94.3% on SWE-bench Verified, an oracle upper bound, since the tests are known-correct); agent-written tests showed no measurable effect ([2602.07900](https://arxiv.org/abs/2602.07900)). Anthropic (paraphrased): a spec should end with an end-to-end verification step.
5. **Small steps, one per context, commit each.** In a coherence-collapse study, 60–69% of failures had the right edit mid-trajectory and then destroyed it; checkpoints recovered them.
6. **Plan influence decays as context fills** — periodic recitation (Manus `todo.md`, plan reminders) was associated with higher success in one study. *(Directional only; see below.)*
7. **A progress file plus git log is the handoff; a fresh context reading the filesystem beats compaction.** Anthropic's long-running-agent harness: read git log and the progress file, run a smoke test, pick one feature.
8. **One decision-maker; subagents for read-only research and fresh-context review only.** Cognition and Anthropic agree coding parallelises poorly.
9. **Proportional ceremony.** Anthropic (paraphrased): if you could describe the diff in one sentence, skip the plan. Boris Cherny (paraphrased): plan mode is unnecessary for synchronous work. Böckeler watched Kiro turn a bug fix into 4 stories and 16 acceptance criteria.
10. **Model-routing evidence is weak.** Most learned routers perform about as well as always using the mid tier; a cheap executor produces plausible-wrong output and the retry loop costs ~4× a clean run (SWE-Effi). Defensible only with per-step verification.
11. **Post-implementation plan-compliance review.** Anthropic's suggested prompt (paraphrased): review the diff against the plan — every requirement implemented, edge cases tested, nothing outside scope changed; report gaps, not style.
12. **The minimal viable plan:** goal, in/out scope, open questions resolved, numbered testable acceptance criteria, affected files by path, small dependency-ordered tasks each naming its files and check, a progress block, human approval before code.

## Scorecard (the loop as it stood, August 2026)

| # | Consensus item | The loop then | Verdict |
|---|---|---|---|
| 1 | Plan file on disk, in repo | `docs/development/{feature}/`, in-repo but **gitignored** | ✓ with a known cost: untracked files are unrecoverable, hence archive-before-delete. Right for repos you don't own |
| 2 | Plan quality gate | `/review-dev` is the mandatory next step | ✓ |
| 3 | Fresh-context, evidence-based review | `/review-dev` verifies the plan's claims against the code before judging; subagent if the same session wrote the plan; correctness-only findings | ✓✓ — Spec Kit `/analyze` and Jules' Planning Critic compare artifact to artifact; this compares plan to codebase |
| 4 | Per-task pass/fail check | Prose acceptance per task ("run twice → zero diff"); the runnable checks sat in COMMANDS.md, unlinked | ◐ stated, mostly not runnable |
| 5 | Small steps, commit each | Tasks grounded in `file:line`; nothing said commit per task | ◐ |
| 6 | Plan recitation mid-session | Nothing between `/begin-dev` and `/close-dev` | ✗ |
| 7 | Progress file + startup ritual | PROGRESS.md + COMMANDS.md + `/begin-dev` reconcile | ✓✓ close to Anthropic's long-running-agent harness |
| 8 | Single decision-maker | Yes | ✓ |
| 9 | Proportional ceremony | Always four files; `--no-plan` gave the scaffolding *without* the plan (backwards); INDEX duplicated SPEC's task list | ✗ — and dev docs were opened more than 5× as often as they were closed |
| 10 | Model routing | `Route:` per task, plus a `Sessions:` paragraph, plus the rubric restated in three commands | ✗ over-invested relative to the evidence |
| 11 | Post-implementation plan-vs-diff review | `/close-dev` checked tests passed; nothing checked scope or criteria against the diff | ✗ highest-value gap |
| 12 | Open questions resolved before code | Listed in INDEX; nothing forced resolution | ◐ |

Net: **the overall shape held up**, and two parts (the claim-verification gate, reconcile-on-resume)
do something the compared tools don't. The lag was in four specific mechanics.

## What survived verification

A second pass fetched 22 sources, extracted 103 claims, put 25 through three-vote adversarial
refutation, and killed 5.

| Mechanic | Verdict | What actually holds |
|---|---|---|
| Runnable per-task checks | **Well-supported** — the only one | TDFlow: 94.3% vs 69.8% on SWE-bench Verified with *correct* supplied tests (an oracle upper bound). [2602.07900](https://arxiv.org/abs/2602.07900): agent-written tests have **no** measurable effect across six frontier models — flipping test-writing by 64–68pp changed nothing. Correlational support: validation share ↔ resolution ρ = +0.50 over 19 agents; each failed CI check cuts PR merge odds ~15% (33.6K PRs). **The lesson is "a correct check must exist", not "the agent should write tests".** |
| Post-implementation plan-vs-diff review | Plausible but thin | Vendor guidance only. The nearest number, Jules' changelog claim that its Planning Critic cut task failures by 9.5%, is a vendor figure, unreplicated, and measures a *pre*-implementation plan critique, not a diff review. Anthropic's own warning stands: a gap-finding reviewer always finds gaps. |
| Proportional ceremony | Plausible but thin | Vendor guidance plus anecdote. No data on how often agents ignore plan files for small tasks. |
| Per-task model routing | Plausible but thin | The economics are real (SWE-Router: a 17–24× cost gap for an 8–15pp resolve gap); failed runs cost ~4× successes (SWE-Effi: n = 50, 2024-era models). No end-to-end study shows routing saves money on multi-step coding without lowering success, and the headline learned-router result itself failed verification 0–3. |
| Mid-session plan recitation | Directional, one paper | arXiv [2604.12147](https://arxiv.org/abs/2604.12147): a standard plan beats no plan for all four models on SWE-bench Verified; reminders every 5 steps improved success rates across all four models (paraphrased). Baseline plan compliance is already 0.75–0.92, so "agents ignore plans" is overstated. One scaffold, non-frontier models, single runs. |

## Recommendations, ranked by value ÷ cost

1. **Make acceptance runnable — supplied at plan time, not by the implementer.** Each task gets `Verify:` = a command or a named test file, written by the planner, copied into COMMANDS.md. `/review-dev` flags prose-only checks and opens named tests to confirm they assert the criterion. The plan ends with one end-to-end check.
2. **Add a post-implementation compliance pass** to `/close-dev`: fresh subagent, input = acceptance criteria + `git diff`, output = per-criterion implemented / partial / missing plus out-of-scope files. Correctness only.
3. **Invert `--no-plan` into `--light`:** SPEC.md only, the plan without the scaffolding. INDEX links to SPEC instead of copying it. If the diff fits one sentence, don't invoke.
4. **Shrink routing to one line per task**, keyed to its `Verify:` line, and point at one rubric instead of restating it in every command. Runnable checks are the precondition that makes routing down safe at all.
5. **Recitation, the cheap version:** PROGRESS.md carries a `Current task:` line; the implementer re-reads that task's block before starting it. No hook machinery on one paper's evidence.
6. **Open-questions gate:** an unchecked question that a task depends on is a Blocker in `/review-dev` unless it becomes a task.
7. **Commit per task**, written into the task template and the resume briefing.

Not recommended: committing dev docs to repos you don't own; multi-agent implementation;
switching to the Spec Kit / Kiro / BMAD formats (heavier, and the review gate here is stronger).

## What changed because of this

Six of the seven recommendations shipped on 2026-08-23 with the context cut; the seventh,
`--light` as the default, landed on 2026-08-24. The cuts mattered as much as the additions:

- **The context library went from 1,650 lines to 310.** It had been restating what the model
  already knows, and `/review-dev` alone `@`-loaded about 1,000 lines (~8K tokens) of it on
  every run. What stayed is what was learned by being
  bitten, and it is read a section at a time, never `@`-included.
- **The `Sessions:` header was retired.** It pre-computed a session plan at planning time, when
  it was guesswork. `/begin-dev` now decides the split at resume time from the per-task routes.
- **Routing is keyed to `Verify:`.** A task with a runnable check and mechanical work can go to
  the value tier; a task with no runnable check goes to the strong model, because nothing
  downstream will catch a plausible-wrong answer.
- **`--light` became the normal case**, and full four-file structure has to be earned by
  multi-session work or a deliverable to promote.
- **A later field audit (October 2026) cut handoffs.** Splitting sessions at *every* route change
  produced eight handoffs in one day and whole sessions for 90-second tasks. `/begin-dev` now
  hands off only when there is a context worth escaping, and absorbs tiny lower-tier tasks.
- **The same audit found `Route:` lines were mostly not acted on.** In 4 of 5 cross-tier
  down-routes the user moved up to Opus rather than down to Sonnet. Routes are advice: the
  resume briefing states them and stops only at a real tier change, where the human decides.

## Sources

**Anthropic:** Claude Code best practices (code.claude.com/docs/en/best-practices) · Effective context engineering for AI agents (2025-09-29) · Effective harnesses for long-running agents (2025-11-26) · Harness design for long-running apps (2026-03-24) · How we built our multi-agent research system (2025-06-13) · platform prompting best practices (multi-context-window section).

**Tools:** github/spec-kit · kiro.dev/docs/specs · BMAD method v6 · Fission-AI/OpenSpec · obra/superpowers · get-shit-done · Cursor plan mode · Cline plan-and-act · Jules changelog 2026-01-26 (Planning Critic).

**Practitioners:** Boris Cherny (Pragmatic Engineer, 2026-03-04) · Birgitta Böckeler, SDD tools (martinfowler.com, 2025-10-15).

**Research:** Cognition, Don't build multi-agents (2025-06-12) · Manus, context engineering (2025-07-18) · Breunig, how long contexts fail (2025-06) · Chroma, context rot (2025-07-14) · Huang et al. [2310.01798](https://arxiv.org/abs/2310.01798) · Panickssery et al. [2404.13076](https://arxiv.org/abs/2404.13076) · Plan-to-Action [2604.12147](https://arxiv.org/abs/2604.12147) · failure study [2509.13941](https://arxiv.org/abs/2509.13941) · coherence collapse [2603.24631](https://arxiv.org/abs/2603.24631) · TDFlow [2510.23761](https://arxiv.org/abs/2510.23761) · agent-generated tests [2602.07900](https://arxiv.org/abs/2602.07900) · task-decoupled planning [2601.07577](https://arxiv.org/abs/2601.07577) · LLMRouterBench [2601.07206](https://arxiv.org/abs/2601.07206) · task/session routing [2608.14641](https://arxiv.org/abs/2608.14641) · SWE-Router · SWE-Effi [2509.09853](https://arxiv.org/abs/2509.09853) · AGENTS.md study [2601.20404](https://arxiv.org/abs/2601.20404) · self-compacting agents [2606.23525](https://arxiv.org/abs/2606.23525) · METR 2025-07-10 and 2026-02-24 update.
