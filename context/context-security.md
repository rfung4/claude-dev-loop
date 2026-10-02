# Security — review triggers and house rules

Library, not a command. `/review-dev` reads this when a plan touches auth, ACL, user data, input handling, migrations, or external I/O (or under `--focus=security`). It holds **what to check and our own rules** — not a security primer; the model knows OWASP. Read a section, not the file.

---

## What the plan must show, by surface

| Surface in the plan | Check for | Missing → |
|---|---|---|
| Authentication | token/session handling, re-auth on privilege change, rate limits on auth endpoints, lockout | Blocker if absent on a new auth path |
| Authorization / ACL | per-object check (not role-only), IDOR (queries scoped to the caller's tenant/org), deny by default, **deny-case tests first** (below) | Blocker |
| Input | validation spec per input (type, size, shape), injection vectors named, parameterised queries | Warning → Blocker if raw SQL / shell / XML |
| Output / errors | no internals in error messages, explicit response schemas (no model-dump of internal fields), opaque public IDs | Warning |
| Data | sensitive fields named, PII minimised, retention stated | Warning |
| Secrets | from env/secrets manager, never in code or logs, `.env*` gitignored | Blocker |
| Migrations | lock behaviour on large tables (`ADD COLUMN … DEFAULT now()` takes a full-table lock on old PG), backfill strategy, reversibility | Blocker on prod tables |
| External I/O | timeouts, retry bounds, failure never stored as success | Warning |

Risk level for findings: Critical (auth bypass, data exposure, injection) · High (missing input validation, IDOR) · Medium (no rate limiting, verbose errors) · Low (hardening).

---

## ACL features: deny cases first

Write and red-green the **deny** tests before implementing the gate — the value of an ACL is what it keeps out. Cover fail-closed paths, flag-off parity, and not-a-member probes before the happy path; the happy path is the easy half. A plan for an ACL feature whose `Verify:` lines are all happy-path is a Warning.

---

## Credential guard (when reading config for review)

Skip the content of `.env`, `.env.*`, `*.pem`, `*.key`, `*secret*`, `*credential*`. Redact values of `*_KEY`, `*_SECRET`, `*_TOKEN`, `*_PASSWORD`, `DATABASE_URL`, `REDIS_URL`, `*_DSN`, `OPENAI_*`, `AWS_*`, `STRIPE_*`, `ANTHROPIC_*`. Report as `DATABASE_URL=[REDACTED]` and count what was redacted. Never echo a credential into a transcript.

---

## Non-obvious anti-patterns (the obvious ones are not listed)

| Don't | Why |
|-------|-----|
| Trust `X-Forwarded-For` blindly | Spoofable; validate against known proxies |
| Sequential IDs in URLs | IDOR; use UUID / opaque public_id |
| `PermissionDenied` as 404 for authenticated users | Hides the check from your own tests; 403 for authed, 404 only for unauthenticated probing |
| Disable HTTPS "for development" | Muscle memory leaks to prod |
| Rate limit only the API, not login/reset/register | Brute force and spam land on the unlimited paths |

---

## Sources

OWASP Top 10 + Cheat Sheet Series · NIST 800-63B · FastAPI / Django security docs. `/review-dev` spec §D for how findings are reported.
