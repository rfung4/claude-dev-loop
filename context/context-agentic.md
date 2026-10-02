# Agentic Principles

Library, not a command. Read a **section** when a decision needs it; never pre-load the file. What is here was learned by being bitten or is a rubric of ours — generic agent theory (Anthropic's "Building effective agents", context-engineering posts) is linked at the bottom, not restated.

---

## When NOT to use agents / subagents

- A single LLM call with retrieval suffices, or the path is fixed → workflow, not agent
- You need deterministic, reproducible output
- The "subagents" would be **parallel** implementers — they make conflicting implicit decisions (Cognition); coding is poorly parallelisable (Anthropic)
- A **single** build-subagent has no conflict problem, but it starts with none of your context, cannot ask you anything mid-task (it guesses and commits), and its report is worthless until a reviewer reads the diff — so you pay the cheaper model to build *and* the stronger one to review. To run the build on a cheaper tier, `/model` in place (keeps the context, one cache miss; see Session plan). Delegate the build only when the parent's context must stay clean of it — a large build with other work after it. Subagents are otherwise for **read-only research** and **fresh-context review**
- Multi-agent ≈ 15× the tokens of a single turn; token use explains ~80% of performance variance — so it must buy something

Subagent mechanics worth knowing: `isolation: worktree` for separate git state; a subagent sees none of the parent's history — put paths, errors and decisions in its prompt; Explore/Plan built-ins skip CLAUDE.md and git status on purpose.

---

## Model Routing

Route by **what will catch a mistake**, not by task difficulty alone. Strong models on the bookends (plan / review), cheaper models in the middle (execution) — but routing down is only safe when the task carries a runnable check, because a cheap model's failure mode is plausible-wrong output and a failed run costs ~4× a successful one. The task's `Verify:` line is therefore the routing key:

| Task has… | Route to |
|-----------|----------|
| Runnable `Verify:` + mechanical / config / glue | Value tier (Sonnet) |
| Runnable `Verify:` + subtle correctness | Workhorse tier (Opus) |
| **No runnable check possible** (judgment, ambiguity, design) | Strong model — nothing downstream will catch it |
| Auth / ACL / data-handling / migration surface | Workhorse tier (Opus), regardless of Verify — and as of 2026-09 (Opus 5.5) expect the cyber classifier to hand the flagged turn to Opus 4.8 silently; see bullet below |
| Long-horizon, ambiguous, large-scope | Scalpel tier (Fable — lead vanishes on short, well-scoped tasks). Since Opus 5.5, Anthropic's own guidance is "start with Opus 5.5; Fable when your evals on Opus 5.5 at higher effort still fall short" — the scalpel now has to earn its 2.5× sticker against a workhorse that beats it on the launch table |

- A prose-only `Verify:` cannot route below the workhorse tier (`/review-dev` flags it)
- Reserve high/xhigh effort for **reasoning, not typing**
- **Security-adjacent work is rerouted on both upper tiers** (as of 2026-09). Fable's safeguard classifier reroutes cyber-flagged prompts to Opus 4.8; so does Opus 5.5's (Claude Code shows "safeguards flagged this session … Opus 4.8 is answering instead"; `/model` cannot override it, and the fallback turn runs without the 5.5 thinking blocks). "Route auth work to Opus" therefore no longer escapes the reroute — it just means Opus 4.8 answers the flagged turns. Accept that, or pin `--model claude-opus-4-8` for an auth-heavy session so the model stays constant and the thinking history stays readable (the one place a versioned id beats the alias).
- **Reviewers: different context, ideally different model, grading against evidence.** Self-review without new evidence is near-worthless and a model favours its own output; the tier of the reviewer matters less than that it is not the author and that it reads the repo/diff, not the prose.
- **Route the review by what `Verify:` left uncovered.** A feature whose tasks all carry runnable checks needs no separate review — the checks are the review. Any prose-only `Verify:` task earns one **end-of-feature** review of the whole diff from a fresh context (new session or review subagent), at the highest tier any task in the feature was routed to, `high` effort. Review **per task** only when a later task builds on a weak-Verify earlier one — a plausible-wrong rewrite that downstream tasks consume costs three commits to unpick instead of one.
- Routing lives in the **session** (`--model`, `/model`) or **subagent frontmatter** — never in spec text; a "use Opus" line in SPEC.md switches nothing
- **Clean context is a quality lever, not just a token one.** For high-stakes tasks prefer a fresh session seeded from the dev doc (`/begin-dev` briefing) over mid-session `/model` flips. (`/model` mid-session doesn't re-ingest history — the only cost is a prompt-cache miss; the reason for fresh sessions is context noise.)
- Evidence grade (2026-08): the cost premise is real (17–24× for 8–15pp on SWE-bench); no study shows routing wins end-to-end on multi-step coding; learned routers ≈ "always-mid". Treat this rubric as a cost hedge made safe by `Verify:`, not as a measured gain. Sources: `~/.claude/claude-dev-loop/docs/why.md`.

### Effort = thinking mode

A `Route:` line is `{tier} · {effort}`, and effort means the reasoning-effort ladder — the thinking budget, not verbosity. Never set in spec text; a "use high effort" line in SPEC.md changes nothing.

**Where effort actually comes from** (verified against the CLI as of 2026-09, v2.1.269):

| Mechanism | Ladder it accepts | Scope |
|---|---|---|
| `claude --effort <level>` at launch | `low, medium, high, xhigh, max` | the session |
| `/effort <level>` in-session | `low, medium, high, xhigh, max, ultracode, auto` | the session, from that point |
| `effortLevel` in `settings.json` | `low, medium, high, xhigh` | default for every model |
| `modelSettings.<model>.effortLevel` | same four | default for that model, overrides the global one |
| `modelSettings.<model>.maxEffortLevel` | `…, max` | a cap; the lowest applicable across settings files wins, and a request above it is clamped with a warning |
| `effort:` in command/agent frontmatter | `low … xhigh` | that command or subagent's own run |

`max` and `ultracode` exist at launch/in-session but not in the settings schema, so a persisted default tops out at `xhigh`.

**Key `modelSettings` by alias, not by version.** Keys are canonicalized through the same alias resolution as `--model`, so `"fable"` behaves exactly like `"claude-fable-5-1"` — proven by the clamp warning naming the canonical model for both spellings. Write `"opus"`, `"sonnet"`, `"fable"` and a new minor version inherits the setting instead of needing a new key. (The canonical name also matches its dated, `[1m]`, Bedrock and Vertex spellings — so an `"opus"` key covers `claude-opus-5[1m]`.)

| Tier | Thinking behaviour | Default effort |
|------|--------------------|----------------|
| `sonnet` (value) | effort-capable | medium |
| `opus` (workhorse) | **always-on adaptive thinking since Opus 5.5 — `disabled`/`budget_tokens` are a 400**; API default effort dropped to `medium` (Opus 5 was `high`). Effort names don't transfer: 5.5 at `medium` ≈ Opus 5 at `high` per Anthropic, and 5.5 thinks more per level — the Claude Code picker shows `max` as ~6× usage (Opus 5 `max` was 1.5×) | medium (now also the API default); high for review/security; `xhigh`/`max` only with a measured gain |
| `fable` (strong) | **always-on adaptive thinking — effort is the only throttle.** Thinking tokens are why effective cost runs 3–5× Opus, not the 2.5× sticker | high for whole-doc runs; xhigh only for the genuinely ambiguous |

Rows are keyed by the CLI alias on purpose: an alias always means the latest model in that tier, so this table survives a 5.1 or a 5.2 without an edit. Version-pinned facts (pricing, context windows, what changed in a point release) live in Anthropic's model documentation, not here.

Alias-keying pays off: as of 2026-09, Claude Code 2.1.280+ stopped applying a top-level `effortLevel` (and any pre-per-model `/effort` choice) to newly released models — Opus 5.5 starts at its own default until you set `modelSettings.opus.effortLevel`. A mid-session `/effort` or `/model` change still invalidates the prompt cache (per-message effort is API-beta only). `/model` also **saves itself as the default for new sessions** ("saved as your default for new sessions") — routing down in place means routing back up before you leave, or the next session quietly starts on the lower tier.

### Session plan — decided at resume, not at plan time

**The actionable unit is the session, not the task** — you can only honor a route at a session boundary, and every restart repays orientation tokens. So the split is computed by `/begin-dev` when you resume, from the per-task `Route:` lines: one session by default; a new session only when there is a context worth escaping (large/post-compaction, hours idle) — a route change on its own is honored **in place**: effort-only is `/effort`, a **tier** change with more than one short task behind it is `/model` (one cache miss, no re-orientation, context kept — cheaper than a handoff and far cheaper than a build-subagent), tiny lower-tier tasks are absorbed into the current run, and prod/deploy tasks are an approval stop, not a model change; Fable only for large, interdependent or ambiguous runs that contain no auth/security task (safeguard reroute) and are not short/homogeneous-mechanical (3–5× Opus for no lead). The SPEC-header `Sessions:` line is retired — it pre-computed this at plan time, when it was guesswork, and was advisory prose anyway. In a field check, splitting at *every* route difference produced 8 handoffs in a day and sessions for 90-second tasks, and sonnet down-routes were taken in ~1 of 5 cases — the gate above is the correction.

Tier roles outlive model names — this file names tiers and CLI aliases; current model facts live in Anthropic's model documentation (as of 2026-09).

---

## Context Management

**Budget:** 1M-context models ≈ 985K usable; 200K models ≈ 185K. Degradation starts well before the ceiling (measurable on all 18 models tested by Chroma; Gemini >100K; Llama ~32K) and is driven by *irrelevant* material, not just length — so the lever is what you load, not how much room is left.

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Forgets earlier instruction | Long context / post-compaction loss | Put it in CLAUDE.md or the dev doc; `/clear` + `/begin-dev` |
| Hallucinates file contents | File never actually Read | Verify reads before reasoning |
| Wrong tool chosen | Overlapping tool descriptions | Reduce overlap; defer-load |
| Same fix attempted repeatedly | Doom loop | After two failed corrections, `/clear` and write a better prompt |
| Inconsistent behaviour | Conflicting instructions across CLAUDE.md / rules / skill | Find the conflict; keep one source per rule |

- **Start fresh** when the task changes kind, after two failed corrections, or when a `/begin-dev` briefing can carry the state. **Continue** mid-debugging when the investigation thread is the state.
- **Fresh context reading the filesystem beats compaction** for long work (Anthropic; Amp replaced compaction with Handoff). State lives in `docs/development/` + git, not in the conversation.
- `@path` in CLAUDE.md/commands loads **eagerly and unconditionally** — a condition beside it is inert. Use a text pointer and let the model `Read`.
- Dev docs for agents: ≤4 files, <10KB, INDEX.md links to SPEC.md rather than copying it. See `~/.claude/claude-dev-loop/context/context-docs.md`.

---

## Delegation clarity

When spawning a subagent, state: the objective; the output format; the effort budget (simple: 1 agent, 3–10 calls; complex: more); which tools to prefer; and every path/error/decision it needs — it has none of your context and cannot ask you mid-task, so any decision it would otherwise have to make, make in the prompt.

---

## LLM Product Engineering Principles

For platforms where the model reads config at runtime (prompt rows, tool descriptions, global instructions). **Every artefact the model reads is code — scope it, version it, test it, observe it.** Distilled from production work, where each was learned by being bitten.

| # | Principle | Rule | Defence |
|---|-----------|------|---------|
| 1 | **Instruction locality** | Put a behaviour at the *lowest* layer (global → agent → tool description → schema → code) that still reaches every caller that needs it. Every layer above pays context on every turn for every agent | Ask: how many agents, how many turns, will pay for this line? |
| 2 | **Instruction vs schema vs code** | Choose by determinism required. Unacceptable-if-ignored → schema/enum/allowlist/code. Style/preference → instruction. Judgement under uncertainty → instruction + eval | "What is the cost of the model ignoring this?" |
| 3 | **Tool descriptions are API contracts** for a stochastic caller | Capabilities in positive space, input contract, output contract incl. presentation, scale semantics ("higher = more human"). Uniform scale + direction across sibling tools | Negative-space only to close a substitution loophole the model will "helpfully" exploit |
| 4 | **Fail-open vs fail-closed** | Neither is right for aggregates. Silent-clean-on-error (open) lies; whole-call-throws-on-one-bad-part (closed) voids good work. Return partial result + typed degradation ("3/4 verified, 1 dropped") | Never store a failure as a success; never let one sub-failure void the aggregate |
| 5 | **Context is the whole payload** | Every turn resends everything unless proven otherwise. Symptoms of loss: "unverified" after a successful call, late-thread drift, tools "never called". Debug by reconstructing the turn's actual payload first | Count tokens per layer before reasoning about behaviour |
| 6 | **Affordance design** | A tool that exists but nothing prompts the agent to offer is dead. Specify trigger / offer / act / exclude (e.g. after >N chars content → offer check → chain to fix → never on streamed/scheduled runs) | "As built, would this ever be called?" |
| 7 | **Change identity** | You cannot A/B or roll back what you cannot name. Hash-per-artefact when config is many-to-many (N agents share tools); version-per-agent when it isn't. Baseline → change on staging → rerun → diff | "Tested against what?" needs a named baseline |
| 8 | **Evaluation levels** | Smoke (1 run) → sample (~20 real inputs) → regression (fixed dataset + judge) → simulation (scripted user vs agent). Match level to blast radius. Make n=20 cheap (thin client) rather than skip it | Judge rubric must be versioned and calibrated on human-labelled goldens |
| 9 | **Observability** | Trace ≠ session ≠ signal. LLM flaggers cost per trace → sample + env-scope them. Derive signals from user-visible failure, not from your own test scenarios. Upload human CS flags/scores as custom signals — highest-value data | Merged staging+prod projects get flagged together |
| 10 | **Minimal change, one variable** | Smallest edit at the narrowest scope, one at a time, so effect is attributable. Two edits in two layers within hours = contradictory and unattributable | One thing to production end-to-end beats five at 60% |
| 11 | **HITL gates and write authority** | Agents propose; humans decide anything irreversible or judgement-laden until calibration is measured. Prepare-only forks, read-only-except-gated-save, never-write-prod | Lift a gate only on a measured agreement rate |
| 12 | **Reversibility × observability** | Ship fast when reversible *and* observable; go deep when either is missing (edge-function throw, unversioned prod prompt row) | Resolves "fast vs proper" without appeal to authority |

---

## Sources (read these, don't restate them)

- Anthropic — Building effective agents · Effective context engineering for AI agents · Effective harnesses for long-running agents · How we built our multi-agent research system · Claude Code best practices (code.claude.com/docs/en/best-practices)
- Cognition — Don't build multi-agents (2025-06)
- Chroma — Context rot (2025-07)
- Evidence review for the dev loop: `~/.claude/claude-dev-loop/docs/why.md`

## See Also

- `./context-docs.md` — where documentation goes
- `./context-security.md` — review triggers, deny-first ACL, credential guard
