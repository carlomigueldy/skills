---
name: countdown
description: "Phase 3.5 (Build Handoff) of the SaaS Launch Blueprint: after Gate 3 approval, list the exact files the founder must attach and produce the ready-to-copy `ultracode:` build prompt (saved as BUILD-HANDOFF.md) for a SEPARATE Claude Code build session, then STOP. Invoked by the saas-launch-blueprint orchestrator once Gate 3 is approved, or when the user explicitly asks to run/resume 'Phase 3.5', generate/redo the build handoff prompt, or assemble the ultracode master prompt for an active Launch Blueprint run. Do NOT trigger on generic 'write me a build prompt' requests outside an active Launch Blueprint, and never start the build in this session."
---

# Phase 3.5 — Build Handoff

You are running Phase 3.5 of the SaaS Launch Blueprint as the same advisor throughout the workflow — for Role & Tone, see the orchestrator (`../saas-launch-blueprint/SKILL.md`, Role & Tone section). As everywhere in this workflow, first-person pronouns (I / ME / MY) refer to the USER — the founder. This is the FINAL step of this session: after Gate 3 approval, the build happens in a SEPARATE Claude Code session the founder starts manually, attaching PRD.md, OWNER-TASKS.md, and the prototype files.

This skill is normally invoked by the `saas-launch-blueprint` orchestrator immediately after Gate 3 is approved (or after a "Validate first" reconvene that then approves). When you finish here, you STOP — there is no next phase to hand control back to.

## Mandatory reads at start

Before doing any Phase 3.5 work, read all three shared reference files (paths relative to this skill's directory):

- `../saas-launch-blueprint/references/tech-design-video.md` — the Build constraint (the two-tier completion gates and MUST-SHIP/DEFER cut order that the handoff's closing text restates; the requirement to enumerate every surface in the locked distribution set BY NAME; the LOCKED-IN stack) and the Video tooling constraint (governs the promo video, and any pitch clip deferred or failed in Phase 3, listed among the handoff's deliverables) — and the Agent Harness tiers (the handoff must carry the chosen tier into the build session).
- `../saas-launch-blueprint/references/shared-context.md` — the Owner Task Ledger (this handoff instructs the build session to convert OWNER-TASKS.md into GitHub issues once the repo exists), the CTA Contact Block, and the session boundary (this session never builds; Phase 4 is a separate, manually-started session).
- `../saas-launch-blueprint/references/interaction-rules.md` — the Deliverable Presentation hard rule (present the handoff prompt and BUILD-HANDOFF.md before considering this phase done), the Presentation Environment section (cards + inline render in Cowork vs. copyable absolute paths + browser-open in Claude Code / the TUI), and the AskUserQuestion rules.

## Steps

Upon Gate 3 approval:

1. List the exact files I need to attach (PRD.md, OWNER-TASKS.md, prototype frames, with filenames/paths).
2. Deliver a ready-to-copy build prompt in EXACTLY this shape — `ultracode: <text> <attachments> <text>` — where `<attachments>` is a literal placeholder marking where I attach the files. The surrounding text makes the attached files the source of truth and encodes everything the build session needs without this session's chat history:
   - Opening text: Fable as master orchestrator (never writes code) executing ultracode dynamic workflows; execute the attached PRD end to end for EVERY surface in its locked distribution set — enumerate the surfaces BY NAME — with the LOCKED-IN stack (no changes without my approval); scaffold via the `saas-launch:saas-scaffold` skill, which instantiates BOTH the monorepo template AND the PRD's chosen agent-harness tier (ordered overlay copy tier-1..N, placeholder substitution, chmod +x init.sh); treat the instantiated AGENTS.md as the binding rulebook for every agent in the session — its Definition of Done gates every feature; at L2+, seed feature_list.json from the PRD before any implementation work; PREFLIGHT CHECK first (gh CLI auth, Vercel access, Supabase token, Docker available, ElevenLabs key present in the BUILD machine's environment — env var or dotfiles; ask the owner if absent — project skills installed incl. pwa-development; the PRD contains an Agent harness section naming the tier; post-scaffold no `{{...}}` placeholders remain in harness files; `jq empty` passes on `.claude/settings.json` and `feature_list.json`) — fail fast with a report if anything is missing; convert the attached OWNER-TASKS.md into GitHub issues once the repo exists.
   - Closing text: completion gates are TWO-TIER, restating the cut order — MUST-SHIP items (customer-app core + payment gating + Mission Control core, green Vitest + Playwright via Playwright MCP, private repo + CI + live production deployment with URL attached to the repo, the attached prototype as the visual reference production UI must match) gate "Accept delivery"; DEFER items (landing polish, full E2E, promo video, Launch Dossier) convert to GitHub issues if cut and are reported in the final message, never silently dropped. MUST-SHIP completion additionally requires: (L2+) every MUST-SHIP feature `passing` in feature_list.json with evidence, and claude-progress.md's Current Verified State updated; (L4) the clean-state checklist satisfied — the Stop gate enforces it. If the pitch clip was deferred or failed in Phase 3, include "render the pitch clip per the Video tooling constraint" in the deliverables. End with a final "Accept delivery" / "Request changes" AskUserQuestion presenting the Launch Dossier, each option carrying a populated per-option `description` (Accept delivery: what accepting finalizes; Request changes: what gets reworked) per AskUserQuestion rule 4 — never bare labels.
3. Present the handoff prompt in a copyable block AND save it as BUILD-HANDOFF.md alongside the PRD and prototype files — presented per the DELIVERABLE PRESENTATION rule. Then STOP — nothing further in this session.

## Phase 4 — Build (reference only; runs in the separate session)

What the handoff prompt must produce: execute the attached PRD end to end via ultracode dynamic workflows for every surface in the locked distribution set, preflight first, two-tier completion gates per the cut order, repo + CI + live deployment, ledger converted to owner issues, promo video (bounded attempts, graceful failure), Launch Dossier — with GATE 4 ("Accept delivery" / "Request changes") presenting the Launch Dossier at the end. The agent harness tier named in the PRD is instantiated during scaffolding and obeyed for the rest of the build per the Agent Harness rule — its AGENTS.md Definition of Done, not this reference, is the binding gate.

## Closing

STOP after saving BUILD-HANDOFF.md and presenting it. Control returns to the `saas-launch-blueprint` orchestrator, which also halts here — Phase 3.5 is the terminal phase of this session. The build (Phase 4) never runs in this session; it runs only when the founder manually starts a separate Claude Code session with the BUILD-HANDOFF.md prompt.
