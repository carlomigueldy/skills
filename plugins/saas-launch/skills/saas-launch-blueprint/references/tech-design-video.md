# Tech, Design & Video Standards

Canonical home for engineering, design, and production-media standards used across the SaaS Launch Blueprint. Phase skills point here rather than restating these blocks — read the section(s) you need at the start of the phase, per that phase skill's "Mandatory reads" list. Throughout this file, first-person pronouns (I / ME / MY) refer to the USER — the founder; "you" is Claude.

This file references the CTA CONTACT BLOCK (used by the Video tooling constraint below). That block's canonical home is `shared-context.md` in this same `references/` directory — do not restate its values here, only point to it.

## Build constraint (for the SEPARATE Phase 4 session)
Working MVP built in a SINGLE Claude Code session executed via ultracode dynamic workflows with Fable as master orchestrator. Full scope is the target: EVERY surface in the PRD's locked distribution set. Cut order applies ONLY on session failure — MUST SHIP: customer-app core workflow + offline/sync, manual payment gating, Mission Control core. DEFER only if forced: landing page, full E2E suite, promo/pitch videos, Launch Dossier — deferred items convert to owner-ledger/GitHub issues, they do not silently vanish.

## Apps & Tech Stack (DEFAULT — final stack locked in during the Phase 2 tech-stack interview)
This stack is my starting preference, not a decree. After I select a product, the stack is interviewed, adapted to the product, and LOCKED IN. Deviations must be justified and documented in the PRD.

NON-NEGOTIABLE UI STACK (exempt from the interview — can never be removed or substituted): Tailwind v4 + shadcn/ui on EVERY PRODUCTION web surface — the Next.js landing page, the responsive PWA web app, Mission Control, and any additional surfaces locked in the distribution interview. The interview may adjust routers, state, hosting, providers; it may NOT touch this pair. The ONE sanctioned exception: the Phase 3 HTML prototype (Tailwind v4 via CDN, no shadcn — it must still implement the PRD's design-system tokens). Every production surface ships as a beautifully crafted, fully responsive web experience. Past builds drifted off this stack — that is a violation: the orchestrator must verify Tailwind v4 + shadcn/ui are actually installed and used in every production UI workstream, and reject any UI work scaffolded without them.

- pnpm + Turborepo monorepo — ALWAYS, regardless of app count. Structured for future growth: apps/ + packages/ layout, shared configs (tsconfig, ESLint, Tailwind), remote caching ready.
- Landing page: Next.js (App Router), Tailwind v4, shadcn/ui, Motion, transitions.dev (https://transitions.dev).
- Customer app: mobile-first PWA, responsive up to tablet and desktop — Vite + React + TypeScript, Tailwind v4, shadcn/ui, TanStack Router (recommended over React Router: type-safe routes, first-class TanStack Query integration), TanStack Query, Zustand, react-hook-form + zod for all forms and validation, service worker, error tracking.
- i18n (REQUIREMENT — established libraries, never hand-rolled): next-i18next (or next-intl if better suited to App Router — justify) for the landing page; react-i18next for the Vite apps. Locale files shared from a common package where practical.
- Offline mode & sync (required PWA functionality): offline-first — app shell and data cached locally (IndexedDB + TanStack Query persistence), writes queued offline and synced to Supabase on reconnect with conflict handling, clear offline/pending-sync UI indicators. Customers on bad connections must NEVER lose data.
- Install prompt / Add-to-Home-Screen (REQUIRED PWA functionality): every PWA MUST prompt end-users to install it on their phones — capture and fire the `beforeinstallprompt` flow on Android/Chrome, and show guided Add-to-Home-Screen instructions on iOS Safari where that event is unavailable. This is NON-NEGOTIABLE on every PWA surface — never ship a PWA without it.
- Admin console — "Mission Control" (REQUIRED, same Vite/React stack, shared UI packages): my command center with FULL super-admin powers:
    - Payment ops: verify/approve/reject manual payments, record receipts and notes, payment history per tenant
    - Tenant lifecycle: activate, suspend, soft-ban, hard-ban, cancel — with a reason or no reason at all, at my sole discretion; instant effect, reversible where applicable
    - Subscription management: extend/shorten, change tiers, comps/trials, force-expire, renewal-reminder oversight
    - Oversight: tenant directory with search/filters, per-tenant activity, platform metrics (signups, active tenants, MRR, pending payments)
    - Safety rails: audit log of admin actions, confirmation dialogs on destructive actions — no approval chains; I am the sole super admin
- Observability & analytics (free tiers only): Sentry across all production surfaces (production AND local development); PostHog free tier or Umami (recommend one) for funnel/activation/validation metrics.
- Shared packages: zod schemas (single source of truth), shared UI/design-system package, shared locale files.
- Backend: Supabase (auth, Postgres, RLS, storage) — multi-tenant, per-tenant isolation; tenant status flags enforced at RLS/policy level so bans take effect server-side.
- Hosting: Vercel for all web surfaces (Dockerfile.vercel container functions if needed); Render only for a service Vercel can't run.
- Local dev: Docker + Docker Compose for non-blocking integration/E2E testing (Supabase local + Playwright in Compose).
- Testing: Vitest for unit/integration; Playwright for E2E via the Playwright MCP — every completed feature verified before marked done; dedicated offline-emulation E2E coverage.
- CI/CD: GitHub + GitHub Actions (lint, typecheck, Vitest, Playwright).

## Design Bar
Produce award-winning-caliber web design across ALL surfaces: landing page, customer app (desktop, tablet, mobile PWA), Mission Control, and any additional locked surfaces. The bar: a $50,000 engagement from a top-tier UI/UX designer and creative artist — Awwwards/Godly/Mobbin caliber. In production apps, the design system is DERIVED FROM shadcn/ui — never built from scratch: start from stock shadcn components and customize through its intended layers (CSS variables/design tokens, Tailwind v4 @theme, component variants) into distinctive art direction, an ownable color story, intentional typography, generous spatial rhythm, polished micro-interactions — never templated defaults, and (in production apps) never a hand-rolled component library. Premium stays balanced with function: usable, fast, accessible.

Design direction clarification (part of the Phase 2 interview): ask about design language (editorial, premium/luxury, minimal, playful/bold, brutalist, soft/organic), mood, color preferences, typography feel, density, motion intensity, and reference sites. My answers bind the design system spec and all frontend work. If I chose "you decide everything," commit to a direction using best taste and document it.

Loading the /frontend-design skill is a HARD REQUIREMENT for every agent producing UI work — no frontend task starts without it. The orchestrator enforces design-direction-settled + skill-loaded as preconditions and rejects UI work below the bar.

## Video tooling
Applies to ALL videos — the Phase 3 pitch clip and the end-of-build promo video:
- THE DELIVERABLE IS A RENDERED MP4 FILE. An HTML composition/timeline is only an intermediate artifact. The sole exception is the documented render-failure path below, which openly DOWNGRADES the deliverable — it never silently reframes HTML as the deliverable.
- Rendering: Hyperframes LOCALLY only — the npm package installed in the repo, via npx, or via the agent skill (https://hyperframes.heygen.com/quickstart). No other Hyperframes integration is permitted. A render attempt is bounded: two tries, then invoke the failure path (deliver composition + narration script as files, state the failure plainly, record a ledger entry, hand rendering to the build session).
- Audio: voice narration AND sound effects generated via the ElevenLabs API (TTS for narration, its sound-effects generation for SFX), mixed into the final MP4.
- Key discovery (environment-aware): check for the key ON THE MACHINE PERFORMING THE RENDER — the ELEVENLABS_API_KEY environment variable and standard dotfiles (`~/.zshrc`, `~/.bashrc`, `~/.profile`, `~/.zshenv`). In sandboxed sessions where my real home directory is not mounted, an empty sandbox does NOT mean "no key" — ASK me for the key or for explicit permission to skip before skipping. Never commit the key; move it into proper env/Vercel secrets if needed at runtime.
- Graceful skip: if no key is available after asking, SKIP the ElevenLabs audio pipeline — do NOT block the phase. Still render and deliver the MP4 (silent or with on-frame captions carrying the narration text), state clearly that audio was skipped and why, and record a ledger entry so I can add the key and re-render later.

Every video produced under this constraint ALWAYS ends on the CTA CONTACT BLOCK — its FINAL clip, without exception, is the founder's CTA (canonical values in `shared-context.md`). The block is collected once during Phase 2's always-asked STEP 2 (see its contact-collection step in `shared-context.md`), then reused as-is to close every subsequent video and dossier.

## Agent Harness (four cumulative tiers)
The scaffolded product repo ships an agent-orchestration harness, not just app code. Four cumulative tiers, each a strict superset of the one below: L1 Minimal (AGENTS.md rulebook with Definition of Done, CLAUDE.md pointer, init.sh dispatcher) → L2 Guarded (+ hooks enforcing migrations-append-only, single-WIP, and human-only commit identity; feature_list.json, progress/handoff memory) → L3 Structured Crew (+ named subagents — surface-builder, backend-engineer, qa-verifier, code-reviewer, research-scout — and PRD-keyed workflow playbooks) → L4 Autonomous Factory (+ clean-state checklist, evaluator rubric, JSONL observability, autonomous-loop.md, and a blocking Stop gate).

The tier is a founder-only call chosen in the Phase 2 flight-plan harness step — ALWAYS asked, even in "You decide everything" mode (delegable via "Other," in which case the agent picks and documents rationale in the PRD).

Instantiation is DETERMINISTIC SCAFFOLD, mirroring the design-system scaffold above: `saas-scaffold` copies `templates/agent-harness/tier-1/` through the chosen tier's directory in order via `cp -R`, higher tiers intentionally overwriting `AGENTS.md`, `CLAUDE.md`, and `.claude/settings.json` with superset files, then runs the same five-placeholder substitution pass as the rest of the monorepo — same tier choice, same values, byte-identical harness output every time. `templates/agent-harness/HARNESS.md` is the source of truth for this mechanic; it is never copied into products.

EVERY tier ships BOTH instruction files — AGENTS.md AND CLAUDE.md; tiering changes only how in-depth the harness is and how constrained agents are, never which file exists. AGENTS.md is the agent-agnostic rulebook — any coding agent reads and obeys it; CLAUDE.md is Claude Code's entry point, a per-tier superset that points at AGENTS.md and lists the Claude-specific machinery active at that tier; `.claude/settings.json` hooks and `.claude/agents/` are the Claude-specific enforcement layer of those same rules, not a separate rulebook. At L2 and above, feature completion is tracked in `feature_list.json` under single-WIP discipline (never more than one `in_progress` feature); at L4 the Stop gate blocks session end while any feature remains `in_progress`.

At EVERY tier, commits and PRs carry the human founder's identity — the author/committer is whatever `git config user.name` / `user.email` (equivalently, the authenticated `gh` account) already says, never overridden via `--author` / `-c user.*` and never reconfigured mid-session, with no AI/LLM attribution of any kind (no `Co-Authored-By:` trailers, no "Generated with ..." footers, no bot sign-offs) in commit messages or PR bodies. This is a rulebook line at L1 and hook-enforced at L2+.
