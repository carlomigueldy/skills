---
name: wind-tunnel
description: Phase 3 (Prototype) of the SaaS Launch Blueprint: choosing storyboard vs clickable format, selecting device targets, building the high-fidelity Tailwind-CDN HTML prototype, the optional Hyperframes pitch clip, and Gate 3 (including the 'Validate first' prospect-pitch-kit path), ending before the build. Invoked by the saas-launch-blueprint orchestrator after Gate 2 approval, or when the user explicitly asks to run/resume 'Phase 3', rebuild the prototype, or attempt the pitch clip for an active Launch Blueprint run. Do NOT trigger on generic 'make me a prototype/mockup' requests outside an active Launch Blueprint — the saas-launch-blueprint orchestrator is the entry point, and this session never starts the build.
---

# Phase 3 — Prototype

You are running Phase 3 of the SaaS Launch Blueprint, as the same advisor throughout the workflow. For Role & Tone, see the orchestrator (`../saas-launch-blueprint/SKILL.md`, Role & Tone section). This skill is normally invoked by the `saas-launch-blueprint` orchestrator after Gate 2 approval, and it hands control back to that orchestrator at Gate 3.

Loading the `/frontend-design` skill is a HARD REQUIREMENT for every agent producing UI work — no frontend task starts without it.

## Mandatory reads at start

Before doing any Phase 3 work, read:

- `../saas-launch-blueprint/references/tech-design-video.md` — the Design Bar (the prototype must feel like $50k of design and implement the PRD's design-system tokens), the Apps & Tech Stack note on the SANCTIONED Tailwind-v4-CDN / no-shadcn prototype exception, and the Video tooling constraint (governs STEP 3's pitch clip: rendered MP4 only, Hyperframes local, two-attempt bound + failure path, ElevenLabs key discovery/graceful-skip).
- `../saas-launch-blueprint/references/interaction-rules.md` — the AskUserQuestion rules, the Deliverable Presentation hard rule (present all prototype files + any clip BEFORE Gate 3), the Presentation Environment section (client detection → widget in Cowork vs. markdown scorecard / copyable-paths block in the TUI), Known Failure Modes #2 (deliverables never shown) and #3 (HTML instead of video), and the Approval Gates rule.
- `../saas-launch-blueprint/references/shared-context.md` — the CTA Contact Block (the pitch clip ends with it).

## STEP 0 — Prototype format

Write-up first, then AskUserQuestion: explain both formats with their cost/benefit for THIS product, recommend one, then let the founder choose:
- **Storyboard View** — a gallery of static high-fidelity screens covering the product's flows breadth-first. Cheaper per screen; capped at 12 screens total — if the core flows genuinely need more, ask with a scoping AskUserQuestion before exceeding it. Past ~10 screens its total cost catches up to a clickable prototype; say so.
- **Clickable Prototype** — max 3 DISTINCT pages, each rendered for every selected device (so up to 3 × N frames), with working navigation, states, and interactions. More token-intensive per screen; best for FEELING the product.

## STEP 1 — Device targets

Write-up first, then AskUserQuestion as a MULTI-SELECT checklist: let the founder tick every device the prototype must present — Mobile PWA, Tablet, Desktop web, plus any surfaces from the PRD's locked distribution set (desktop app shell, native mobile frame). Recommend a default (typically Mobile PWA + Desktop web). Every selected device gets its own genuinely designed layout — never a naive shrink.

## STEP 2 — Build

High-fidelity HTML-only prototype in the chosen format for every selected device, implementing the settled design direction — saved as standalone file(s) attachable to the build session. Plain HTML/CSS/JS with Tailwind v4 from CDN — the sanctioned no-shadcn exception; faithfully implement the PRD's design-system tokens so the prototype matches what production will become. Must feel premium — $50,000 of work from a real UI/UX designer and creative artist — and, in clickable format, balanced with real working functionality.

## STEP 3 — Pitch clip (OPTIONAL — always ASK first)

Hyperframes rendering frequently fails, so never attempt it silently. Post a short write-up of the trade-off (great investor material vs. tokens burned on a failure-prone render), then AskUserQuestion:
- **"Attempt pitch clip now"** — render per the Video tooling constraint (two attempts max), showcasing the selected devices, ending with the CTA CONTACT BLOCK. Only a rendered .mp4 satisfies an opted-in attempt.
- **"Skip — defer to the build session"** — the clip moves to Phase 4's deliverables; Phase 3.5 MUST include it in the handoff prompt.

A failed attempt follows the Video tooling failure path and does not block Gate 3.

## GATE 3

BEFORE asking, present all deliverables per the DELIVERABLE PRESENTATION rule and the Presentation Environment section (`../saas-launch-blueprint/references/interaction-rules.md`) — in Cowork: cards for every file plus inline rendering of a representative subset when the set is large; in Claude Code / the TUI: every file's absolute path in one copyable block with an open command, the HTML prototype opening in the browser (no inline render); the clip if one exists. Then AskUserQuestion:
- "Approve — prepare build handoff"
- "Validate first" — before any build spend, produce a PROSPECT PITCH KIT: a shareable version of the prototype, a short pitch script that includes the ACTUAL price, and a response tracker for 5 prospects; pause here while the founder pitches, then reconvene at this gate with real reactions (which may revise pricing or scope via "Go back")
- "Request changes" / "Go back — revisit an earlier decision"

DO NOT START THE BUILD. This session never builds.

## Closing / handback

On "Approve — prepare build handoff" (or a "Validate first" reconvene that then approves), return control to the `saas-launch-blueprint` orchestrator so it invokes `saas-launch:countdown` — do not start the handoff inline. On "Request changes", iterate Phase 3 in place and re-present Gate 3. On "Go back", return control to the orchestrator so it re-invokes the named earlier phase's skill; downstream deliverables must be revised or regenerated. Never build here — the workflow continues via the orchestrator until Phase 3.5's STOP.
