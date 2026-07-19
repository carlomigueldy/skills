---
name: ignition
description: Phase 1 (Target Market + Ideation) of the SaaS Launch Blueprint: customer-segment selection, geographic-scope selection, and scored product ideation, ending at Gate 1. Invoked by the saas-launch-blueprint orchestrator as the first step of that workflow, or when the user explicitly asks to run or resume 'Phase 1', reopen target-market/scope selection, or regenerate the scored idea list for an active Launch Blueprint run. Do NOT trigger on generic 'give me SaaS ideas' or app-brainstorm questions outside an active Launch Blueprint — the saas-launch-blueprint orchestrator is the entry point for those.
---

# Phase 1 — Target Market + Ideation

You are running Phase 1 of the SaaS Launch Blueprint, as the same advisor throughout the workflow — for Role & Tone, see the orchestrator (`../saas-launch-blueprint/SKILL.md`, Role & Tone section). This skill is normally invoked by the `saas-launch-blueprint` orchestrator and hands control back to it once Gate 1 is resolved.

## Mandatory reads at start

Before doing any Phase 1 work, read:

- `../saas-launch-blueprint/references/shared-context.md` — the business constraints that idea scoring is judged against: target-market baseline assumptions (segment + scope) and the re-confirm rule for non-PH-centric picks, the manual-payments model, the organic-social distribution channel set, the free-tier LLM requirement, and pricing anchors.
- `../saas-launch-blueprint/references/interaction-rules.md` — the Delegation Model (fan market/competitor research out to parallel subagents; keep scoring judgments yourself), AskUserQuestion rules 1–7 (write-up-BEFORE-widget, the option-cap rule 7, per-decision write-ups when chaining segment → scope → idea, and the Presentation Environment + rule-6 Comparison Format policy: widget in Cowork vs. rich markdown scorecard table in Claude Code / the TUI), Known Failure Mode #1 (a widget with no context — why the standalone write-up must land visibly first), and the Approval Gates hard rule (the three standing options every gate carries).

## STEP 1 — Customer segment

Post a standalone write-up describing each segment (who they are, what they'd pay for, what selling to them looks like), plus a segment comparison scorecard per the Comparison Format rule (`../saas-launch-blueprint/references/interaction-rules.md`, Presentation Environment section + AskUserQuestion rule 6) — segments as rows; who-they-are, willingness-to-pay, sell-motion, and risk as columns — rendered as the inline widget in Cowork and as a rich markdown table inline in this write-up in Claude Code / the TUI. THEN prompt via AskUserQuestion (option-cap rule 7 applies):

Local PH SMEs · Gen-Z Teens · PH Content Creators · PH Vloggers · Web3 users & communities (traders, builders, DAO/NFT/DeFi) · Individuals (everyday people, daily challenges)

If the founder picks "Other" or any non-PH-centric segment, re-confirm the baseline assumptions (see Context) before ideation. Note: Gen-Z Teens carries contracting-with-minors and parental-consent obligations — surface them in the write-up. Wait for the founder's selection.

## STEP 2 — Geographic scope

Standalone write-up explaining trade-offs per scope for the chosen segment (payment rails, pricing power, competition, support hours, legal exposure), plus a scope comparison scorecard per the Comparison Format rule (AskUserQuestion rule 6) — scopes as rows, those trade-off dimensions as columns, THEN AskUserQuestion:

Philippines only · Worldwide · PH-first then global

Wait for the founder's selection. All downstream work (currency, rails, locale priority, content plan, legal scope) adapts.

## STEP 3 — Ideation (HARD SEQUENCE — widget FORBIDDEN until (a) is visibly delivered)

(a) Post the complete scored analysis as its own standalone write-up: one titled section PER IDEA — name, what it does (2–3 plain-language sentences), who pays and why, pricing potential, scores against: willingness to pay, organic-social sellability, one-session buildability, LLM leverage on free tiers, manual-payment-gating fit, low solo-owner support burden. Mark ONE recommendation with justification. 4–6 ideas tailored to segment AND scope. Also present the idea scorecard per the Comparison Format rule (`../saas-launch-blueprint/references/interaction-rules.md`, AskUserQuestion rule 6) — ideas as rows, the six scoring criteria above as columns, and a Verdict row marking the recommendation: the inline widget in Cowork, a rich markdown scorecard table inline in this write-up in Claude Code / the TUI. A reader seeing ONLY the text must fully understand every idea. (Delegate market/competitor research to parallel subagents per the Delegation Model; the scoring judgments stay yours.)

(b) ONLY THEN AskUserQuestion — same names, each option with a 1–2 sentence description, recommendation first labeled "(Recommended)", cap rule 7 for 5–6 ideas. If the analysis didn't visibly render, re-deliver before asking.

Exclude: booking/queue system for service SMEs, Kolekta (lending), Sweldo, Suki (digital loyalty), Benta (Messenger/FB/TikTok order tracker), Labada (laundry tracker).

Do NOT implement anything.

## GATE 1

AskUserQuestion: "Approve — proceed to PRD" / "Request changes" / "Go back — change segment or scope".

## Handback

- **"Approve — proceed to PRD"**: do NOT start the PRD inline. Return control to the `saas-launch-blueprint` orchestrator so it invokes `saas-launch:flight-plan`.
- **"Request changes"**: iterate Phase 1 in place (revise the segment write-up, scope write-up, or scored analysis as needed) and re-present Gate 1. Do not return to the orchestrator yet.
- **"Go back — change segment or scope"**: reopen segment (STEP 1) or scope (STEP 2) selection here, then re-run the affected downstream steps and re-present Gate 1.

Finishing this phase does not end the workflow — it only pauses at Gate 1 for the founder's decision. The overall Launch Blueprint continues via the orchestrator, which immediately invokes the next phase's skill as soon as Gate 1 is approved.
