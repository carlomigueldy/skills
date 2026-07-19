# Tenant Lifecycle — {{PRODUCT_NAME}}

Task id prefix: `tenant-`. Covers the admin-discretionary tenant-status state machine (Mission Control's "Tenant lifecycle" power), its server-side RLS enforcement, and the audit trail — as distinct from the payment-driven subscription states (trial/grace/expired) owned by `payment-lifecycle.md`. If this product stores both in one status field, keep the two playbooks' transitions consistent whenever either touches it, and say so explicitly in the shared zod schema.

## State machine

| State | Meaning (default — confirm against the PRD if it defines these differently) |
|---|---|
| `active` | Normal access. |
| `suspended` | Full lockout, neutral/temporary framing (e.g. a billing or security hold) — no reason required, per the DEFAULT stack's "reason or no reason at all, at my sole discretion." |
| `soft_banned` | Reduced/read-only access; a visible banner citing the ToS reason; cannot transact. |
| `banned` | Full lockout, hard stop — the tenant sees a banned screen only. |
| `cancelled` | Tenant closed, by admin or customer request per the refund/cancellation policy; data retained per the PRD's Legal & compliance section. |

Every transition:
- Is instant and takes effect **server-side** (RLS/policy layer) — never a client-side-only flag. A banned/suspended/soft_banned tenant must be denied at the database policy layer, not merely hidden in the UI.
- Is reversible from any state back to `active` at the founder's sole discretion (Mission Control has no approval chain) unless the PRD marks a specific transition terminal.
- Produces exactly one immutable audit-log entry: actor, timestamp, from-state, to-state, reason (if given).

## Steps

1. Read the PRD's tenant-lifecycle section and the DEFAULT stack's Mission Control "Tenant lifecycle" bullet (`tech-design-video.md`) — confirm whether this product requires a mandatory reason on any transition (default: optional, per "reason or no reason at all").
2. Confirm or extend the tenant-status enum in the shared zod schema package (single source of truth): `active | suspended | soft_banned | banned | cancelled`, plus whatever payment-driven status `payment-lifecycle.md` owns.
3. Enforce server-side first: write the RLS policy (and the append-only migration adding the `tenant_status` column if not already scaffolded — **new migration file only, never edit a past one**) that denies non-public data access for `suspended` / `soft_banned` / `banned` tenants. Get this working and tested before building the admin UI on top of it.
4. Build the Mission Control admin actions: activate, suspend, soft-ban, hard-ban, cancel. Each destructive action gets a confirmation dialog (Safety Rails, no approval chain — the confirmation dialog IS the safety rail), an optional reason field, and writes the audit-log entry.
5. Build the per-tenant audit-log view in Mission Control: a timeline of every status change for that tenant.
6. Build the customer-facing side of each restricted state in the PWA: a clear, non-confrontational message with no ambiguity about why access is blocked, and a path back to support or payment where relevant. Never show a generic error for a deliberate admin action.
7. Verify RLS enforcement directly, not just through the UI: attempt an authenticated request as a `suspended`/`soft_banned`/`banned` tenant (Vitest hitting the Supabase policy directly, or a Playwright network assertion) and confirm the server denies it.
8. Verify every admin transition round-trips: Mission Control action → tenant-status change → audit-log entry appears → PWA reflects the new state on next load (Playwright).
9. Verify audit-log completeness: no transition is missing an entry, no entry is mutable after the fact.
10. Definition of Done (AGENTS.md) + `feature_list.json` update — `tenant-NN` entries split at whatever granularity the PRD's feature breakdown gives (e.g. `tenant-01` state machine + RLS, `tenant-02` Mission Control actions, `tenant-03` audit log, `tenant-04` customer-facing states), each `verification`/`evidence` filled in before `passing`.
