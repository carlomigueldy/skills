# Shared Context — Business & Product Constraints

Canonical home for the "what the product is and what the business rules are" surface of the SaaS Launch Blueprint. Every phase skill reads this file at its start; do not restate these rules elsewhere — point back here instead. Throughout this file, first-person pronouns (I / ME / MY) refer to the USER — the founder; "you" is Claude.

## Context & Constraints

- Solo founder, minimal budget, not yet DTI-registered — no payment gateways or app store billing.
- Payments collected manually (GCash, Maya, GoTyme, bank transfer, PayPal, crypto). I verify payments and gate access manually. This is a core product feature, not backstory — and it must cover the REVENUE side, not just the lockout side: activation flow, trial policy, renewal reminders and dunning nudges BEFORE expiry, grace period, subscription expiry + lockout on lapse, refund/cancellation policy, dispute handling, customer-facing receipts, manual receipt notes. If the market is Worldwide, PayPal and crypto become the primary rails (flag the personal-PayPal-account freeze risk and a mitigation); GCash/Maya/GoTyme/bank transfer serve PH customers.
- Target market: chosen by ME in Phase 1 — BOTH the customer segment AND the geographic scope. The baseline assumptions (mobile-first, social-centric users, offline resilience, Tagalog/Taglish i18n) hold for PH-centric picks; if I choose "Other" or a non-PH-centric segment/scope, re-confirm each baseline assumption via AskUserQuestion before ideation and drop what doesn't apply.
- MVP always ships as a mobile-first PWA — lowest cost and friction for me the owner.
- i18n from day one: English / Tagalog / Taglish, user-switchable (English becomes the default/primary locale if Worldwide). The agent generates all locale files, then records a ledger entry for me to review and correct the Tagalog/Taglish copy before launch.
- Pricing: affordable monthly recurring adjusted to the chosen segment and scope — PH anchor ₱99–₱499/mo; if Worldwide, recommend a USD-equivalent anchor and whether to price regionally. Exact tiers in the PRD; the anchor is a hypothesis until tested against real prospects (see Gate 3's validate-first path).
- Distribution: organic social only — Facebook (posts, stories, reels, page, friends promoting), Instagram (stories, profile), Threads, X/Twitter (threads, articles). Score ideas against THIS channel and include a content plan in the PRD (X/Twitter and Threads carry more weight for Worldwide and Web3 audiences).
- LLM: open-weight models on FREE inference tiers only (hard requirement: ₱0 inference cost at MVP). Candidates: Groq free tier, Cloudflare Workers AI, Cerebras free tier, OpenRouter free models. Design within free-tier rate limits (queueing, caching, fallbacks). The PRD must state the scaling breakpoint: at how many users the free tier breaks and what plan B costs per month. Account creation for these providers is an owner-ledger task.

## CTA Contact Block (single source of truth)

All videos and dossiers reference this block; never restate it elsewhere:

> +63 916 776 4350 · carlomigueldy@gmail.com · Facebook/Instagram @carlomigueldy

Confirm or override it once during the Phase 2 branding interview (recommend a product-branded email/page over personal handles for public distribution).

## Session Boundary

THIS session covers Phases 1–3 plus the Build Handoff ONLY. It never starts the build. Phase 4 runs in a SEPARATE Claude Code session that I start manually, using the handoff prompt this session prepares for me.

## Owner Task Ledger

During Phases 1–3.5 there is NO GitHub repo yet — never attempt to file GitHub issues in this session. Instead, accumulate every owner action (Taglish locale review, provider/account creation, domain purchase, ElevenLabs key setup, prospect pitching, launch content) in an OWNER-TASKS.md file delivered alongside the PRD. The handoff prompt instructs the build session to convert this ledger into GitHub issues once the repo exists.
