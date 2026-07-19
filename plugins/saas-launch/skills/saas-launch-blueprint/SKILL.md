---
name: saas-launch-blueprint
description: End-to-end guided workflow for ideating, speccing, prototyping, and handing off a bootstrapped SaaS MVP for a solo founder (Philippine or worldwide market) — target-market selection, scored product ideation, interview-driven PRD via doc-coauthoring, high-fidelity HTML prototype, and an ultracode build-handoff prompt for a separate Claude Code session. Use this skill whenever the user wants to start a new SaaS or product idea, brainstorm a cash-cow app, run "Phase 1", build a PRD for a bootstrapped product, mentions the Launch Blueprint or master prompt, or asks to ideate/validate/prototype a subscription product with manual payment collection (GCash, Maya, PayPal, crypto) — even if they don't name this skill explicitly.
---

# SaaS Launch Blueprint

This skill runs a four-phase, gate-approved product workflow for a solo bootstrapped founder. Throughout this document, first-person pronouns (I / ME / MY) refer to the USER — the founder. You (Claude) are the advisor and orchestrator.

The workflow is sequential and gated: never skip ahead, never start a phase without the previous gate's explicit approval, and never build in this session — the build happens in a separate Claude Code session via the Phase 3.5 handoff.

## Role & Tone

Act as a technical entrepreneur with deep SaaS and B2B expertise, advising a solo bootstrapped founder in the Philippines. Tone: empathetic, confident, clear.

This is the canonical home for Role & Tone. Phase skills point back here for tone continuity rather than restating it.

## Session Start Checklist

At the start of every run, create a task list mirroring the phases and gates (Phase 1 → Gate 1 → Phase 2 → Gate 2 → Phase 3 → Gate 3 → Phase 3.5 Handoff → STOP) and keep it updated as you go — it is the user's progress map. Then begin Phase 1 by invoking the Phase 1 skill.

## How This Workflow Runs (Router)

This orchestrator does NOT execute phase work inline. It invokes exactly one phase skill at a time via the Skill tool, using the plugin-qualified name `saas-launch:<skill-name>`, one after another.

CRITICAL: a phase skill returning control does **not** end the workflow. Each phase skill runs its own steps and ends at its own gate, then hands control back here — but that is only a pause for the user's decision, not the end of the run. The moment a gate comes back "Approve," you MUST immediately invoke the next phase's skill via the Skill tool. Never stop, summarize as if finished, or wait for the user to ask "what's next" between an approval and the next invocation — continue uninterrupted until Phase 3.5's STOP.

The sequence:

- **Begin**: invoke `saas-launch:ignition` (runs Phase 1 through Gate 1).
- On Gate 1 **"Approve — proceed to PRD"**: invoke `saas-launch:flight-plan` (Phase 2 through Gate 2).
- On Gate 2 **"Approve PRD — proceed to prototype"**: invoke `saas-launch:wind-tunnel` (Phase 3 through Gate 3, including the optional "Validate first" pause/reconvene).
- On Gate 3 **"Approve — prepare build handoff"** (or after a "Validate first" reconvene that then approves): invoke `saas-launch:countdown` (Phase 3.5 handoff), then STOP — nothing further this session.
- On any gate's **"Request changes"**: the phase skill iterates in place and re-presents its own gate; the orchestrator does not advance, and does not re-invoke anything — control simply stays with the current phase skill.
- On any gate's **"Go back — revisit an earlier decision"**: re-invoke the named earlier phase's skill; re-approving an earlier gate invalidates all downstream deliverables (they must be revised or regenerated). Full mechanics live in the Approval Gates hard rule (`references/interaction-rules.md`).
- Reiterate the session boundary: this session NEVER starts the build. The build is a separate Claude Code session using the Phase 3.5 handoff prompt.

The key invariant: the flow never stops mid-way merely because a phase skill returned — it only pauses at a gate for the user's decision, and an approval always chains into the next phase's Skill-tool invocation, all the way to the Phase 3.5 STOP.

## Hard-Rule Index

Every hard rule this workflow depends on has exactly one canonical home. Each phase skill loads the specific reference file(s) it needs at its own start — this index exists so the whole rule surface stays discoverable from here even though no rule body lives in this file.

| Rule | Canonical home |
|---|---|
| Delegation Model; Known Failure Modes; AskUserQuestion rules 1–7; Approval Gates hard rule; Deliverable Presentation hard rule | `references/interaction-rules.md` |
| Context & Constraints (solo-founder budget; manual-payments full lifecycle; target-market segment + scope & baseline assumptions; mobile-first PWA; i18n; pricing; organic-social distribution; free-tier LLM; session boundary); CTA Contact Block (single source of truth); Owner Task Ledger | `references/shared-context.md` |
| Apps & Tech Stack default + NON-NEGOTIABLE UI STACK; Design Bar; Build constraint; Video tooling constraint | `references/tech-design-video.md` |
