# Workflows — {{PRODUCT_NAME}}

Agent-agnostic playbooks: markdown checklists any coding agent can follow (Claude Code, Codex, Cursor, or a human). Tier-3 also ships `.claude/agents/` — a Claude-specific crew that happens to be well suited to running these checklists — but nothing here requires that crew to exist. Where a step names a role, treat it as "whichever agent/session is doing this kind of work," with the Claude crew mapping noted in parens.

## Routing table

Match the PRD area you're implementing to its `feature_list.json` id prefix and playbook.

| PRD area | id prefix | Playbook | Primary role (Claude crew mapping) |
|---|---|---|---|
| Manual-payment lifecycle (activation, trial, dunning, grace, expiry, refund, dispute, receipts) | `payments-` | `payment-lifecycle.md` | backend-engineer + surface-builder |
| Tenant state machine, RLS enforcement, Mission Control admin actions | `tenant-` | `tenant-lifecycle.md` | backend-engineer + surface-builder |
| Landing page | `landing-` | `surface-build.md` | surface-builder |
| PWA customer app | `pwa-` | `surface-build.md` | surface-builder |
| Mission Control admin console | `mission-control-` | `surface-build.md` | surface-builder |
| Any additional surface the PRD's distribution interview locked in | (surface's own PRD prefix) | `surface-build.md` | surface-builder |
| Shared/cross-cutting work not owned by one surface — zod schemas, locale files, Sentry/analytics wiring, CI config | `platform-` | none — follow AGENTS.md's non-negotiables directly, no dedicated playbook | backend-engineer |
| Repo creation, CI, Vercel deploy, Lighthouse, issue conversion, Launch Dossier inputs | `release-` | `release.md` | whoever holds repo/deploy access |

If a PRD area doesn't map cleanly to a row above, don't invent a new playbook file — extend the closest existing one in place (e.g. a new surface still uses `surface-build.md`) or route it through `platform-` and AGENTS.md directly.

## Convention: playbooks map runs to `feature_list.json` entries

- A playbook run is scoped to exactly one `feature_list.json` entry at a time — the single-WIP rule from AGENTS.md applies here too. Mark the entry `in_progress` before starting the playbook's steps, not after.
- Every playbook in this directory ends its steps the same way: verify against AGENTS.md's **Definition of Done** (the last, most-important section — read it, don't assume), then write the result into `feature_list.json` (`verification`, `evidence`, `status`). A playbook run that doesn't end in a `feature_list.json` update didn't happen as far as the harness is concerned.
- `status: passing` requires real evidence (a Playwright run, Vitest output, a Lighthouse score, a live URL) attached to the entry — never flip status without it. At tier-3+, only the `qa-verifier` role is expected to make the final `passing` call; other roles hand off with evidence attached and status left at whatever the crew roster in AGENTS.md specifies.
- If a step can't be completed (missing key, undecided PRD detail, external dependency), mark the entry `blocked` with notes naming exactly what's missing — never leave it `in_progress` across a session boundary, and never fudge `passing` to avoid a blocker.
- `id` is PRD-keyed and prefixed per the routing table above (e.g. `payments-03`, `tenant-01`, `landing-02`, `release-04`) — pick the granularity from the PRD's own feature breakdown, one id per shippable unit of behavior.
