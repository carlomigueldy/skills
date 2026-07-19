# AGENTS.md — {{PRODUCT_NAME}}

The single rulebook for every agent working in this repo — human, Claude, or
any other coding agent. `CLAUDE.md` is a pointer to this file, not a
duplicate of it. If a rule here and a rule anywhere else disagree, this file
wins; fix the other file instead of routing around this one.

## What this repo is

{{PRODUCT_DESCRIPTION}} — a multi-tenant SaaS product ({{PRODUCT_SLUG}}),
built as a pnpm + Turborepo monorepo (`apps/` surfaces, `packages/` shared
code) on Supabase (auth, Postgres, RLS, storage). Primary locale is
{{PRIMARY_LOCALE}}. Payments are collected and verified manually by the
product owner ({{CONTACT_EMAIL}}) — there is no payment gateway integration
to trust; every access decision this repo makes is downstream of a human
verifying a receipt.

## Commands

Never hand-roll `pnpm`/`turbo` invocations from memory — delegate to
`./init.sh`, the single entry point every agent uses:

```bash
./init.sh install   # pnpm install
./init.sh verify    # pnpm turbo run lint typecheck build
./init.sh test      # pnpm turbo run test
./init.sh start     # pnpm dev
```

If a command needs to change, change it in `init.sh` — not in whatever you
happen to be running by hand.

## NON-NEGOTIABLES

- **Tailwind v4 + shadcn/ui on every production surface.** Never substitute
  another CSS framework or component library, never hand-roll a design-system
  primitive shadcn/ui already provides. The design system is derived FROM
  shadcn — stock components customized through its own layers (CSS
  variables/design tokens, Tailwind v4 `@theme`, component variants) — never
  built from scratch.
- **One token file.** `packages/ui/src/tokens.css` is the single source of
  design tokens (color, radius, type scale). Every app imports it after its
  own `@import "tailwindcss";` — never duplicate tokens into an app-local
  stylesheet.
- **RLS + tenant-status enforced server-side.** Every tenant-status effect
  (suspension, ban, cancellation) is enforced at the Postgres RLS/policy
  layer, not just gated in the UI. A client-side check is a convenience, not
  a security boundary — if RLS doesn't also enforce it, the rule doesn't
  exist yet.
- **Migrations are append-only.** An applied migration file is never edited
  or deleted. Schema changes are always a NEW migration file. This is
  enforced by a hook at tier 2+ — at tier 1 it is enforced by discipline
  only.
- **No secrets committed.** API keys, service-role keys, and provider
  credentials live in environment variables / Vercel project secrets, never
  in a committed file, never hardcoded in source.

## Domain rules

### Manual-payment lifecycle

Payments are collected manually (GCash, Maya, GoTyme, bank transfer, PayPal,
crypto) and verified by the owner in Mission Control — this is a core
product feature, not backstory, and it covers the revenue side as much as
the lockout side. Every build touching payments must account for the full
lifecycle, not just one stage of it:

1. **Activation** — access granted only after the owner verifies a
   submitted payment/receipt.
2. **Trial** — per the PRD's trial policy, time-boxed, converts to paid or
   expires.
3. **Renewal reminders & dunning** — nudges (in-app + Messenger/email) fire
   BEFORE expiry, on the PRD's cadence — never only after the customer is
   already locked out.
4. **Grace period** — a defined window after expiry where access continues
   but the customer is clearly warned.
5. **Expiry + lockout** — access is revoked server-side (RLS, not just UI)
   once grace lapses.
6. **Refund / cancellation / dispute** — per the PRD's policy, including the
   PayPal chargeback + personal-account-freeze mitigation where PayPal is a
   rail.
7. **Receipts** — every verified payment produces a customer-facing receipt
   and an owner-side manual receipt note.

### Tenant states

Tenant lifecycle is a state machine, owner-controlled from Mission Control,
with a reason or no reason at all at the owner's sole discretion, instant
effect, and reversible where applicable:

```
active ⇄ suspended
active ⇄ soft-banned
active → banned (hard-ban)
active → cancelled
```

Every state transition is enforced at the RLS/policy level (not just hidden
in the UI) and written to the admin audit log. A banned or cancelled tenant
must lose access immediately, server-side, on the next request — not on the
next client refresh.

## Orchestration roles

Roles below are agent-agnostic — any coding agent can fill them under
whatever name that agent's harness uses. Parenthetical Claude Code mapping
is the concrete assignment for this plugin's default execution model
(ultracode dynamic workflows):

- **Orchestrator** — decomposes work, orders dependencies, routes tasks,
  delegates, reviews integration. NEVER writes code itself. *(Claude: Fable,
  master orchestrator only.)*
- **Worker** — does most implementation and code review, one per surface
  workstream, in parallel where workstreams don't conflict. *(Claude:
  Sonnet.)*
- **Escalation** — architectural decisions and complex reasoning only, on
  escalation from a worker or the orchestrator — not a default assignee.
  *(Claude: Opus.)*
- **Mechanical** — trivial, mechanical, or lookup tasks, spawnable by a
  worker mid-task. Never edits product code unsupervised. *(Claude:
  Haiku/Explore.)*

Frontend work is never delegated to a worker without design direction
already settled and the `frontend-design` skill loaded first — that
precondition is the orchestrator's to enforce, not the worker's to skip.

## Verification

Every completed feature is verified before being marked done — not
implemented, verified:

- **Playwright MCP** — UI/E2E verification against the real running app,
  including offline-emulation scenarios for PWA work.
- **Vitest** — unit/integration coverage, run via `./init.sh test`.

A feature with no verification evidence attached is not done, regardless of
how confident the implementation looks.

## DEFINITION OF DONE

**This is the most important section in this file.** Every other section
exists to make this one achievable — when in doubt about whether something
is finished, this list is the tie-breaker, not your judgment call.

A feature (or the repo as a whole, at ship time) is DONE only when ALL of
the following hold:

- [ ] `./init.sh verify` exits 0 (lint, typecheck, build — all green).
- [ ] `./init.sh test` exits 0.
- [ ] Verified via Playwright MCP for any user-facing surface, with evidence
      recorded (not just "I checked it").
- [ ] Built FROM shadcn/ui per the NON-NEGOTIABLES — no hand-rolled UI
      primitives, no framework substitution.
- [ ] Loading, error, empty, offline, and pending-sync states are all
      present where applicable — not just the happy path.
- [ ] Forms use react-hook-form + zod validation.
- [ ] Responsive across mobile, tablet, and desktop.
- [ ] Accessibility basics covered: labels, focus order, contrast.
- [ ] RLS/tenant-status effects verified server-side, not assumed from the
      client behaving correctly.
- [ ] No secrets committed; no console.log/debugger left in.
- [ ] Sentry + the chosen analytics tool are wired for anything shipping to
      production.

If any box is unchecked, the work is not done — say so plainly instead of
reporting completion.
