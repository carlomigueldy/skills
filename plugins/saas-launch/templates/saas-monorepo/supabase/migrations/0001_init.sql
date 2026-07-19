-- 0001_init.sql
-- {{PRODUCT_NAME}} ({{PRODUCT_SLUG}}) — initial schema.
--
-- Multi-tenant SaaS core: tenants, subscriptions, manual_payments, audit_log.
-- Enums and nullability below are mirrored field-for-field from the zod
-- schemas in packages/schemas/src/index.ts, the single source of truth for
-- these shapes — if a shape changes there, this file needs a follow-up
-- migration, not a hand-edit of an already-applied one.
--
-- RLS is the enforcement boundary, not application code: every table is
-- tenant-scoped, and every read policy re-checks tenants.status = 'active'
-- via is_active_tenant_member() below. A tenant that gets suspended/banned/
-- cancelled loses row-level access immediately and everywhere, even if a
-- client still holds a valid session and a stale UI.

-- ---------------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------------
create extension if not exists "pgcrypto"; -- gen_random_uuid()

-- ---------------------------------------------------------------------------
-- Enums (mirror packages/schemas/src/index.ts — keep in sync)
-- ---------------------------------------------------------------------------

-- Mirrors tenantStatusEnum. Note there is no 'pending' member: a tenant row
-- is created already 'active' in this template; product-specific onboarding
-- gates (e.g. "awaiting first payment") should read subscriptions/
-- manual_payments instead of overloading tenant status for that.
create type public.tenant_status as enum (
  'active',
  'suspended',
  'soft_banned',
  'banned',
  'cancelled'
);

-- Mirrors subscriptionTierEnum.
create type public.subscription_tier as enum (
  'free',
  'starter',
  'pro',
  'enterprise'
);

-- Mirrors manualPaymentMethodEnum.
create type public.manual_payment_method as enum (
  'gcash',
  'maya',
  'gotyme',
  'bank_transfer',
  'paypal',
  'crypto'
);

-- Mirrors manualPaymentStatusEnum.
create type public.manual_payment_status as enum (
  'pending',
  'approved',
  'rejected'
);

-- audit_log.action and .target_type are free-form text in the zod schema
-- (z.string(), not z.enum) — intentionally NOT a Postgres enum here either,
-- so mission-control can log new action/target kinds without a migration.

-- ---------------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------------

-- Mirrors packages/schemas tenantSchema.
create table public.tenants (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  name text not null check (char_length(name) between 1 and 120),
  status public.tenant_status not null default 'active',
  owner_user_id uuid not null references auth.users (id) on delete restrict,
  primary_locale text not null default '{{PRIMARY_LOCALE}}',
  contact_email text not null check (contact_email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
  status_reason text check (char_length(status_reason) <= 500),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.tenants is
  'One row per customer/organization. status is the server-side kill switch enforced via RLS on every table below.';

-- Internal join table — not part of packages/schemas' client-facing shapes.
-- Required so RLS can answer "which tenant(s) can this auth.uid() see".
create table public.tenant_members (
  tenant_id uuid not null references public.tenants (id) on delete cascade,
  user_id uuid not null references auth.users (id) on delete cascade,
  role text not null default 'member', -- 'owner' | 'admin' | 'member' — extend with a check/enum if roles grow
  created_at timestamptz not null default now(),
  primary key (tenant_id, user_id)
);

-- Mirrors packages/schemas subscriptionSchema.
create table public.subscriptions (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (id) on delete cascade,
  tier public.subscription_tier not null default 'free',
  is_trial boolean not null default false,
  trial_ends_at timestamptz,
  expires_at timestamptz,
  auto_renew boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Mirrors packages/schemas manualPaymentSchema, plus submitted_by_user_id
-- (an internal bookkeeping column, not in the client-facing zod shape) which
-- the insert RLS policy below depends on to prove "the submitter is who
-- they say they are".
create table public.manual_payments (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (id) on delete cascade,
  subscription_id uuid references public.subscriptions (id) on delete set null,
  method public.manual_payment_method not null,
  status public.manual_payment_status not null default 'pending',
  amount numeric(12, 2) not null check (amount > 0),
  currency char(3) not null default 'PHP',
  receipt_url text,
  note text check (char_length(note) <= 1000),
  submitted_by_user_id uuid references auth.users (id) on delete set null,
  submitted_at timestamptz not null default now(),
  reviewed_at timestamptz,
  reviewed_by_user_id uuid references auth.users (id) on delete set null,
  rejection_reason text check (char_length(rejection_reason) <= 500),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.manual_payments is
  'Manual/offline payment proofs (GCash, Maya, bank transfer, ...) awaiting verify/approve/reject in mission-control. Written offline-first from apps/pwa via its IndexedDB write queue, synced here on reconnect.';

-- Mirrors packages/schemas auditLogEntrySchema.
create table public.audit_log (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references public.tenants (id) on delete cascade,
  actor_user_id uuid references auth.users (id) on delete set null,
  action text not null check (char_length(action) between 1 and 120),
  target_type text not null check (char_length(target_type) between 1 and 60),
  target_id text check (char_length(target_id) <= 120),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

comment on table public.audit_log is
  'Append-only trail of tenant lifecycle and payment-ops actions taken from mission-control.';

-- ---------------------------------------------------------------------------
-- updated_at triggers
-- ---------------------------------------------------------------------------

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger tenants_set_updated_at
  before update on public.tenants
  for each row execute function public.set_updated_at();

create trigger subscriptions_set_updated_at
  before update on public.subscriptions
  for each row execute function public.set_updated_at();

create trigger manual_payments_set_updated_at
  before update on public.manual_payments
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- Helper: is the current user an active member of a given tenant?
--
-- SECURITY DEFINER so it can read tenant_members/tenants regardless of the
-- calling role's own RLS visibility into those tables, without recursing
-- into tenants' own select policy (which itself calls this function).
-- ---------------------------------------------------------------------------

create or replace function public.is_active_tenant_member(check_tenant_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.tenant_members tm
    join public.tenants t on t.id = tm.tenant_id
    where tm.tenant_id = check_tenant_id
      and tm.user_id = auth.uid()
      and t.status = 'active'
  );
$$;

comment on function public.is_active_tenant_member is
  'Server-side ban/suspend enforcement point: returns false for ANY tenant whose status is not ''active'' (suspended, soft_banned, banned, cancelled), regardless of membership. Every RLS policy below calls this instead of duplicating the status check inline.';

revoke all on function public.is_active_tenant_member(uuid) from public;
grant execute on function public.is_active_tenant_member(uuid) to authenticated, service_role;

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------

alter table public.tenants enable row level security;
alter table public.tenant_members enable row level security;
alter table public.subscriptions enable row level security;
alter table public.manual_payments enable row level security;
alter table public.audit_log enable row level security;

-- tenants: members can read their own tenant row, but ONLY while active.
-- A suspended/soft_banned/banned/cancelled tenant becomes invisible to its
-- own users the instant its status flips — this is the "server-side ban
-- enforcement" the scaffold spec calls for.
create policy "tenants_select_active_members"
  on public.tenants for select
  to authenticated
  using (public.is_active_tenant_member(id));

-- No insert/update/delete policy for `authenticated` on tenants: status
-- changes (activate/suspend/ban/cancel) and tenant creation are reserved
-- for mission-control, which runs with the service_role key and bypasses
-- RLS entirely. Regular users can never write their own tenant row.

-- tenant_members: a user can see the membership rows of tenants they
-- belong to (used to resolve "which tenant(s) am I in" client-side),
-- gated the same way — active tenants only.
create policy "tenant_members_select_active"
  on public.tenant_members for select
  to authenticated
  using (public.is_active_tenant_member(tenant_id));

-- subscriptions: tenant-isolated read, active tenants only. Writes are
-- service_role-only (billing/mission-control owns this table).
create policy "subscriptions_select_active_tenant"
  on public.subscriptions for select
  to authenticated
  using (public.is_active_tenant_member(tenant_id));

-- manual_payments: members of an active tenant can see their own tenant's
-- payment proofs and submit new ones (e.g. from apps/pwa, including via its
-- offline write queue once back online). Review fields (status,
-- reviewed_by_user_id, rejection_reason, ...) are only ever mutated by
-- mission-control via service_role — no update/delete policy is granted to
-- `authenticated` here, so a submitter cannot self-approve their own payment.
create policy "manual_payments_select_active_tenant"
  on public.manual_payments for select
  to authenticated
  using (public.is_active_tenant_member(tenant_id));

create policy "manual_payments_insert_active_tenant"
  on public.manual_payments for insert
  to authenticated
  with check (
    public.is_active_tenant_member(tenant_id)
    and submitted_by_user_id = auth.uid()
    and status = 'pending' -- a submitter can only ever create rows in the initial state
  );

-- audit_log: read-only for tenant members of an active tenant (plus
-- tenant-less system entries, tenant_id is null). All writes are
-- service_role-only, from mission-control's payment-ops / tenant-lifecycle
-- actions — regular users never insert audit rows directly.
create policy "audit_log_select_active_tenant"
  on public.audit_log for select
  to authenticated
  using (tenant_id is null or public.is_active_tenant_member(tenant_id));

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------

create index tenant_members_user_id_idx on public.tenant_members (user_id);
create index subscriptions_tenant_id_idx on public.subscriptions (tenant_id);
create index manual_payments_tenant_id_idx on public.manual_payments (tenant_id);
create index manual_payments_status_idx on public.manual_payments (status);
create index audit_log_tenant_id_idx on public.audit_log (tenant_id);
create index audit_log_created_at_idx on public.audit_log (created_at desc);
