---
name: flight-plan
description: Phase 2 (PRD) of the SaaS Launch Blueprint: interview-mode selection, the themed interview rounds, and authoring the complete end-to-end business PRD.md plus OWNER-TASKS.md via the doc-coauthoring skill, ending at Gate 2. Invoked by the saas-launch-blueprint orchestrator after Gate 1 approval, or when the user explicitly asks to run/resume 'Phase 2', write or revise the PRD, or redo the tech-stack/design/branding interview for an active Launch Blueprint run. Do NOT trigger on generic 'write me a PRD' or product-spec requests outside an active Launch Blueprint — the saas-launch-blueprint orchestrator is the entry point.
---

# Phase 2 — PRD

You are running Phase 2 of the SaaS Launch Blueprint, as the same advisor throughout the workflow — for Role & Tone see the orchestrator (`../saas-launch-blueprint/SKILL.md`, Role & Tone section). This skill is normally invoked by the `saas-launch-blueprint` orchestrator once Gate 1 is approved, and it hands control back to the orchestrator at Gate 2.

Use the doc-coauthoring skill for the PRD.

## Mandatory reads before starting

Phase 2 draws on essentially every cross-phase rule and constraint this workflow has — read all three reference files in the orchestrator's directory before doing any Phase 2 work:

- **`../saas-launch-blueprint/references/shared-context.md`** — the FULL manual-payments lifecycle (feeds the PRD's payment-lifecycle section), the target market / pricing / i18n / distribution / free-tier-LLM constraints, the CTA Contact Block (confirm or override it during the branding interview), the Owner Task Ledger (accumulate owner actions into OWNER-TASKS.md), and the session boundary.
- **`../saas-launch-blueprint/references/tech-design-video.md`** — the Apps & Tech Stack DEFAULT (map it onto the chosen product during the tech-stack interview), including the NON-NEGOTIABLE UI STACK; the Design Bar (drives the design-direction question set and the design-system spec); the Video tooling constraint (governs the PRD's launch promo video); and the Build constraint (drives the single-session MVP cut order documented in the PRD).
- **`../saas-launch-blueprint/references/interaction-rules.md`** — the AskUserQuestion rules (each interview round needs its own standalone write-up first; contested choices get comparison widgets), the Delegation Model (fan research out to subagents, keep judgments yourself), the Deliverable Presentation hard rule (present PRD.md + OWNER-TASKS.md before Gate 2), and the Approval Gates rule.

## STEP 0 — Interview mode

Standalone write-up explaining the two paths, then AskUserQuestion:

"Interview me" · "You decide everything" (agent decides all open items, documents each decision + rationale in the PRD)

## STEP 1 — Interview (if "Interview me")

AskUserQuestion rounds grouped by theme, each preceded by its own standalone explainer write-up, until NOTHING material is ambiguous:

- **Product**: MVP scope boundaries, must-have vs nice-to-have, trial policy, tiers and price points
- **Tech stack**: map the DEFAULT stack onto the chosen product in a standalone write-up — for EVERY major choice explain WHY it fits THIS product, cost (₱0/free tier), and the strongest alternative's trade-off; stack-comparison widget for contested choices. Product-driven deviations (realtime, heavy media, Web3 wallets, edge inference) go through AskUserQuestion. Iterate until LOCKED IN; the locked stack supersedes the default, recorded in the PRD with per-choice rationale.
- **App distribution**: the DEFAULT surfaces are the landing page, the mobile PWA, and Mission Control. Discuss (write-up first, then AskUserQuestion) which distribution targets this product ships on: mobile PWA, web app, desktop app (Tauri or Electron — recommend one with trade-offs), and/or native mobile app (React Native ONLY — never Flutter or any other cross-platform framework). Explain per-option build effort, cost, and fit. The selected set becomes the PRD's LOCKED DISTRIBUTION SET — every later reference to "surfaces" means exactly this list, and the monorepo extends accordingly.
- **Design**: the full design-direction question set from the Design Bar
- **Branding**: naming preferences, tone of voice, names/domains the founder has in mind — and confirm/override the CTA CONTACT BLOCK for public deliverables
- **Operations**: support hours (timezone coverage if Worldwide), payment verification turnaround, launch timing
- **Anything else** only the founder can decide

## The complete end-to-end PRD.md contents

Write the complete end-to-end business PRD — saved as a standalone file (PRD.md) the founder can attach to the build session. Reproduce every section and sub-item below; cross-references to constraint blocks (e.g. "per the Video tooling constraint", "built FROM shadcn/ui per the Design Bar", "cut order per the Build constraint") are pointers to the reference files above — do not copy those rule bodies into the PRD's authoring instructions here, only into the PRD itself as needed:

- **Product**: problem, personas, user stories (customer + Mission Control), single-session MVP scope with cut order, post-MVP roadmap, pricing tiers, FULL payment lifecycle across PWA and Mission Control — activation, trials, renewal reminders + dunning cadence (in-app + Messenger/email, N days before expiry), grace period, expiry/lockout, refund/cancellation policy, dispute runbook (incl. PayPal chargebacks + personal-account freeze mitigation), customer-facing receipts — and the tenant-lifecycle state machine (active → suspended/soft-banned/banned/cancelled and back)
- **Tech**: LOCKED-IN stack with per-choice rationale, architecture, multi-tenant data model with server-side status enforcement, LLM feature design within free-tier limits, i18n strategy, offline-first sync strategy (caching, write queue, conflict resolution), testing strategy (Vitest + Playwright MCP loop incl. offline scenarios)
- **Observability & analytics**: Sentry (production + local dev) and the chosen analytics tool, with events/funnels measuring the success criteria
- **Design system spec**: built FROM shadcn/ui, never from scratch — customization through shadcn's own theming layers (CSS variables/design tokens, Tailwind v4 @theme, component variants) on top of stock components, per the Design Bar and settled direction: tokens, type scale, color story, motion language. MUST include the DETERMINISTIC SCAFFOLD: the exact, reproducible initialization sequence every build session runs verbatim — pnpm + Turborepo workspace creation, Tailwind v4 setup per app, `pnpm dlx shadcn@latest init` with the chosen theme config, the component add list, and the shared ui/design-system package wiring — same commands, same structure, same token file locations, so every future build from this skill scaffolds identically and correctly
- **Production quality bar**: polished and production ready — consistent design system; loading/error/empty/offline/pending-sync states everywhere; react-hook-form + zod validation; responsive mobile/tablet/desktop; accessibility basics; Lighthouse ≥90 mobile (landing + PWA); security review (RLS incl. ban enforcement, no leaked secrets); SEO meta, OG images, favicons, PWA manifest; Sentry + analytics wired. The orchestrator gates completion on this checklist.
- **Branding & domains**: name, positioning, voice — 3 recommended domains checked with whatever web tooling THIS session has (search/registrar fetch), marked "indicative — reverify at purchase" (agent-browser is a build-session tool; .com + .ph for PH, .com priority Worldwide). Purchase = owner-ledger task; agents configure DNS after.
- **Legal & compliance** (scoped STRICTLY to the chosen geography): PH-only → exclusively Philippine law — pre-DTI operation with a CONCRETE registration trigger (register before or immediately upon first paid customer; cite the actual DTI/BIR rule), BIR receipts, Data Privacy Act, consumer-protection rules, parental-consent flows if Gen-Z Teens; Worldwide → add international basics (GDPR, cross-border payments). Where laws impose requirements, TAILOR the product's features to comply — surface every compliance-driven requirement in the PRD so the app violates nothing and the founder stays safe from lawsuits. A customer-facing refund/cancellation policy is REQUIRED (it is what makes the discretionary suspend/ban ToS clause defensible); ToS expressly reserves the founder's right to suspend/ban/cancel at sole discretion.
- **Customer support & bug triage**: support workflow for customer concerns (channels per scope — Messenger/FB page primary for PH; email/X DMs added for Worldwide), bug intake and triage classifying severity and ESCALATING to the founder (via the ledger now, GitHub issues once the repo exists) whenever a code fix or owner decision is needed, and an FAQ page shipped as part of the landing page/app.
- **Marketing kit**: brand kit for social media (logo variants, color/typography usage rules, post/story/reel templates, profile + cover assets for FB, IG, Threads, X), comprehensive SEO implementation (technical, on-page, structured data, content plan), a ready-to-publish launch blog post, and the distribution plan across the founder's organic channels.
- **Business ops**: scope-tuned social go-to-market plan, unit economics at ₱0 inference cost + the free-tier scaling breakpoint
- **Build budget**: an honest estimate of the Phase 4 session's token/compute cost per surface — the build is the founder's largest real cash outlay and they should see it BEFORE approving the handoff
- **Success criteria**: validation targets (e.g., 5 paying customers in 30 days) and kill/pivot criteria — measurable via analytics
- **Repo & deployment**: build-session agents create a PRIVATE GitHub repo, link Vercel, ship a live production deployment, attach the URL to the repo (About + README), and convert OWNER-TASKS.md into GitHub issues
- **Launch promo video**: RENDERED MP4 per the Video tooling constraint — same bounded-attempts and graceful-failure status as the Phase 3 clip (never blocks delivery; failure downgrades to composition + script + issue); ends with the CTA CONTACT BLOCK
- **Launch Dossier**: final self-contained HTML artifact (Tailwind v4 CDN, product's own design system) summarizing the delivery — pitch line, production URL, repo, locked stack + distribution set, gate history, analytics links, open owner issues, promo video, CTA CONTACT BLOCK. File + inline render; the build session's handoff document.
- **Project-level skills to install and document**: find-skills (https://www.skills.sh/vercel-labs/skills/find-skills, on demand), agent-browser (https://www.skills.sh/vercel-labs/agent-browser/agent-browser, on demand), frontend-design (https://www.skills.sh/anthropics/skills/frontend-design, HARD REQUIREMENT for all frontend agents), pwa-development (`npx skills add https://github.com/alinaqi/claude-bootstrap --skill pwa-development`, REQUIRED for the PWA workstream), hyperframes agent skill (https://hyperframes.heygen.com/quickstart, for video work)
- **Agent orchestration** (ultracode dynamic workflows): Fable is MASTER ORCHESTRATOR ONLY — never writes code; owns decomposition, dependency ordering, routing, delegation, integration review. Sonnet: most implementation + code reviews (parallel workers per surface workstream). Opus: architectural decisions and complex reasoning only, on escalation. Haiku/Explore: trivial mechanical tasks, spawnable by Sonnet agents. Frontend delegation requires design direction settled + frontend-design loaded (+ pwa-development for PWA). All agents verify UI via Playwright MCP; completion gated on green Vitest + Playwright AND the quality bar. The PRD documents this as the build session's execution plan.

## Gate 2

Present the PRD file and OWNER-TASKS.md per the Deliverable Presentation rule (`../saas-launch-blueprint/references/interaction-rules.md`), then AskUserQuestion:

"Approve PRD — proceed to prototype" / "Request changes" / "Go back — revisit the idea, segment, or scope"

## Closing / handback

The deliverables of this phase are PRD.md and OWNER-TASKS.md as standalone files, presented before Gate 2 is asked.

- On **"Approve PRD — proceed to prototype"**: do NOT start the prototype inline. Return control to the `saas-launch-blueprint` orchestrator so it invokes `saas-launch:wind-tunnel`.
- On **"Request changes"**: iterate Phase 2 in place (revise the interview answers, the PRD, or both) and re-present Gate 2. Do not hand control back to the orchestrator yet.
- On **"Go back — revisit the idea, segment, or scope"**: return control to the orchestrator, which re-invokes the named earlier phase's skill; re-approving that earlier gate invalidates this PRD, which must be revised or regenerated once the earlier decision is re-confirmed.

The overall workflow continues via the orchestrator — this phase finishing is not the end of the session.
