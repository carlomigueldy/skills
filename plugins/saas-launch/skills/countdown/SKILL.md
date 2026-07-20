---
name: countdown
description: "Phase 3.5 (Build fork) of the SaaS Launch Blueprint: after Gate 3 approval, auto-detect the platform (Claude Cowork vs Claude Code CLI) and ALWAYS ask whether to build it out now (run Phase 4 in THIS session to GATE 4) or just produce the ready-to-copy `ultracode:` build prompt (saved as BUILD-HANDOFF.md) for a separate build session. Invoked by the saas-launch-blueprint orchestrator once Gate 3 is approved, or when the user explicitly asks to run/resume 'Phase 3.5', generate/redo the build handoff prompt, or assemble the ultracode master prompt for an active Launch Blueprint run. Do NOT trigger on generic 'write me a build prompt' requests outside an active Launch Blueprint."
---

# Phase 3.5 — Build Fork

You are running Phase 3.5 of the SaaS Launch Blueprint as the same advisor throughout the workflow — for Role & Tone, see the orchestrator (`../saas-launch-blueprint/SKILL.md`, Role & Tone section). As everywhere in this workflow, first-person pronouns (I / ME / MY) refer to the USER — the founder. Phase 3.5 FORKS: after Gate 3 approval you detect the platform (STEP 0), then ALWAYS ask whether to build it out now or just produce the hand-off prompt (STEP 0.5). On the hand-off branch this session is terminal — assemble the `ultracode:` prompt, save BUILD-HANDOFF.md, STOP. On the build-now branch, Phase 4 runs HERE through GATE 4 (Accept delivery), then STOP. Either way, control never returns to the orchestrator for a new phase.

This skill is normally invoked by the `saas-launch-blueprint` orchestrator immediately after Gate 3 is approved (or after a "Validate first" reconvene that then approves). Whichever branch you take, you STOP at its end — there is no next phase to hand control back to.

## Mandatory reads at start

Before doing any Phase 3.5 work, read all three shared reference files (paths relative to this skill's directory):

- `../saas-launch-blueprint/references/tech-design-video.md` — the Build constraint (the two-tier completion gates and MUST-SHIP/DEFER cut order that both branches restate; the requirement to enumerate every surface in the locked distribution set BY NAME; the LOCKED-IN stack, per the PRD's `Stack source`) and the Video tooling constraint (governs the promo video, and any pitch clip deferred or failed in Phase 3, listed among the deliverables) — and the Agent Harness tiers (carried into the build on either branch).
- `../saas-launch-blueprint/references/shared-context.md` — the Owner Task Ledger (OWNER-TASKS.md is converted into GitHub issues once the repo exists), the CTA Contact Block, and the session boundary (Phases 1–3 never build; Phase 3.5 forks — build-now runs Phase 4 here, hand-off defers it to a separate session).
- `../saas-launch-blueprint/references/interaction-rules.md` — the Deliverable Presentation hard rule (present the hand-off prompt and BUILD-HANDOFF.md, or the Launch Dossier, before considering the phase done), the Presentation Environment section (cards + inline render in Cowork vs. copyable absolute paths + browser-open in Claude Code / the TUI), and the AskUserQuestion rules.

## STEP 0 — Platform detection (run once)

Run this once, before anything else. It decides which build option is *recommended* in STEP 0.5 and how a hand-off (if chosen) is delivered. HEURISTIC — if the signals are ambiguous, ASK; never guess silently.

```bash
printf 'REMOTE=%s|%s\n' "${CLAUDE_CODE_REMOTE:-}" "${CLAUDE_CODE_REMOTE_SESSION_ID:-}"
printf 'MNT='; ls -d /mnt/user-data /mnt/skills 2>/dev/null | tr '\n' ' '
printf '\nPWD=%s HOME=%s GIT=%s\n' "$PWD" "$HOME" "$(git rev-parse --is-inside-work-tree 2>/dev/null || echo no)"
```

- **Claude Cowork (cloud VM)** if ANY: `CLAUDE_CODE_REMOTE` / `CLAUDE_CODE_REMOTE_SESSION_ID` is set; `/mnt/user-data` or `/mnt/skills` exists; `$PWD` / `$HOME` sits under `/mnt/` or `/sessions/`. There is no local terminal to open a second session here.
- **Claude Code CLI** if NONE of the above AND `$HOME` is a real user home (`/home/*`, `/Users/*`); a git work tree corroborates.
- **Ambiguous** → one AskUserQuestion ("Where will the build run?"), both options carrying a populated per-option `description` per AskUserQuestion rule 4. No official Cowork env var exists, so this heuristic plus the fallback question is the whole detection story.

Carry the detected platform forward — it flips the STEP 0.5 recommendation and tailors the hand-off delivery mechanics.

## STEP 0.5 — Build now, or just the hand-off prompt? (ALWAYS ask)

Unconditional. Ask regardless of `Stack source` (template or custom) and regardless of platform. Give a short write-up first — this session already holds all the context to build immediately, but building here means one long, token-heavy session whose preflight must be satisfiable in THIS environment; the hand-off keeps context clean but you open the build session yourself — then a single-select AskUserQuestion with BOTH options carrying a populated per-option `description` (AskUserQuestion rule 4):

- **"Build it out now"** — run Phase 4 in THIS session: preflight, scaffold, execute the PRD end-to-end to GATE 4. Trade-off: one long token-heavy session; the preflight must pass in this environment (build credentials + tooling present here). *Recommended on Claude Cowork* — no local terminal to open a separate build session.
- **"Just give me the build hand-off prompt"** — assemble the `ultracode:` prompt, save BUILD-HANDOFF.md, STOP; you start the build session yourself. Trade-off: clean context separation, but the build runs elsewhere. *Recommended on Claude Code CLI.*

Branch on the answer: "Build it out now" → **Branch A**; "Just give me the build hand-off prompt" → **Branch B**.

## Branch A — Build it out now (Phase 4 in this session)

Execute Phase 4 here, end-to-end. Do NOT produce BUILD-HANDOFF.md on this branch.

1. **PREFLIGHT CHECK first — fail fast.** Verify the same preconditions the hand-off prompt would encode: gh CLI auth, Vercel access, Supabase token, Docker available, ElevenLabs key present in THIS environment (env var or dotfiles; ask if absent), project skills installed incl. pwa-development, the PRD contains an Agent harness section naming the tier, and (after scaffold) no `{{...}}` placeholders remain in harness files with `jq empty` passing on `.claude/settings.json` and `feature_list.json`. If anything is missing, STOP with a report — do not start the build in a broken environment.
2. **Scaffold by `Stack source`** (first line of the PRD Tech section — the literal marker `Stack source: template | custom`):
   - `template` → invoke `saas-launch:saas-scaffold`, which instantiates BOTH the monorepo template AND the PRD's chosen agent-harness tier (ordered overlay copy tier-1..N, placeholder substitution, chmod +x init.sh). Post-scaffold, no `{{...}}` placeholders remain in harness files.
   - `custom` → do NOT invoke `saas-scaffold`. Scaffold from the PRD's CUSTOM STACK SPEC — the PRD's locked UI stack governs, and the Tailwind v4 + shadcn/ui rule does NOT apply here. Instantiate the harness tier by ADAPTATION: copy the stack-agnostic overlay files verbatim (`feature_list.json`, `claude-progress.md`, `session-handoff.md`, commit-identity + single-WIP + settings self-protection hooks, tier-4 loop/checklist/rubric/logs, tier-3 reviewer/QA/scout lanes) and re-author the stack-coupled files against the SPEC (AGENTS.md/CLAUDE.md Commands + Non-negotiables + Definition of Done, `init.sh` dispatcher commands, migration/token-path Bash guards, tier-3 workflows' surface prefixes + tooling, surface-builder/backend-engineer lanes).
3. **Bind the harness.** Treat the instantiated (or adapted) AGENTS.md as the binding rulebook for every agent for the rest of the build — its Definition of Done gates every feature. At L2+, seed feature_list.json from the PRD before any implementation work.
4. **Execute the PRD end-to-end** for EVERY surface in its locked distribution set (enumerated BY NAME) with the locked stack (no changes without my approval): two-tier completion gates and the MUST-SHIP/DEFER cut order (per tech-design-video.md), private GitHub repo + CI + live production deployment with the URL attached to the repo, OWNER-TASKS.md converted to GitHub issues once the repo exists, promo video (bounded attempts, graceful failure; render any pitch clip deferred or failed in Phase 3 per the Video tooling constraint), Launch Dossier. MUST-SHIP completion additionally requires: (L2+) every MUST-SHIP feature `passing` in feature_list.json with evidence and claude-progress.md's Current Verified State updated; (L4) the clean-state checklist satisfied.
5. **GATE 4** — end with an "Accept delivery" / "Request changes" AskUserQuestion presenting the Launch Dossier, each option carrying a populated per-option `description` (Accept delivery: what accepting finalizes; Request changes: what gets reworked) per AskUserQuestion rule 4 — never bare labels. Then STOP.

## Branch B — Hand-off prompt (separate build session)

Produce the ready-to-copy prompt and STOP. This is the skill's original behavior.

1. List the exact files I need to attach (PRD.md, OWNER-TASKS.md, prototype frames, with filenames/paths).
2. Deliver a ready-to-copy build prompt in EXACTLY this shape — `ultracode: <text> <attachments> <text>` — where `<attachments>` is a literal placeholder marking where I attach the files. The surrounding text makes the attached files the source of truth and encodes everything the build session needs without this session's chat history:
   - Opening text: Fable as master orchestrator (never writes code) executing ultracode dynamic workflows; execute the attached PRD end to end for EVERY surface in its locked distribution set — enumerate the surfaces BY NAME — with the LOCKED-IN stack (no changes without my approval). **Scaffold clause — branch on the PRD's `Stack source` (first line of the Tech section):**
     - `template` → scaffold via the `saas-launch:saas-scaffold` skill, which instantiates BOTH the monorepo template AND the PRD's chosen agent-harness tier (ordered overlay copy tier-1..N, placeholder substitution, chmod +x init.sh).
     - `custom` → do NOT use `saas-scaffold` or the bundled template. Scaffold from the PRD's CUSTOM STACK SPEC (the PRD's locked UI stack governs; the Tailwind v4 + shadcn/ui rule does not apply). Instantiate the harness tier by ADAPTATION per this contract: copy the stack-agnostic overlay files verbatim (`feature_list.json`, `claude-progress.md`, `session-handoff.md`, commit-identity + single-WIP + settings self-protection hooks, tier-4 loop/checklist/rubric/logs, tier-3 reviewer/QA/scout lanes) and re-author the stack-coupled files against the SPEC (AGENTS.md/CLAUDE.md Commands + Non-negotiables + Definition of Done, `init.sh` dispatcher commands, migration/token-path Bash guards, tier-3 workflows' surface prefixes + tooling, surface-builder/backend-engineer lanes).
   - Both paths: treat the instantiated (or adapted) AGENTS.md as the binding rulebook for every agent in the session — its Definition of Done gates every feature; at L2+, seed feature_list.json from the PRD before any implementation work; PREFLIGHT CHECK first (gh CLI auth, Vercel access, Supabase token, Docker available, ElevenLabs key present in the BUILD machine's environment — env var or dotfiles; ask the owner if absent — project skills installed incl. pwa-development; the PRD contains an Agent harness section naming the tier; post-scaffold no `{{...}}` placeholders remain in harness files; `jq empty` passes on `.claude/settings.json` and `feature_list.json`) — fail fast with a report if anything is missing; convert the attached OWNER-TASKS.md into GitHub issues once the repo exists.
   - Closing text: completion gates are TWO-TIER, restating the cut order — MUST-SHIP items (customer-app core + payment gating + Mission Control core, green Vitest + Playwright via Playwright MCP, private repo + CI + live production deployment with URL attached to the repo, the attached prototype as the visual reference production UI must match) gate "Accept delivery"; DEFER items (landing polish, full E2E, promo video, Launch Dossier) convert to GitHub issues if cut and are reported in the final message, never silently dropped. MUST-SHIP completion additionally requires: (L2+) every MUST-SHIP feature `passing` in feature_list.json with evidence, and claude-progress.md's Current Verified State updated; (L4) the clean-state checklist satisfied — the Stop gate enforces it. If the pitch clip was deferred or failed in Phase 3, include "render the pitch clip per the Video tooling constraint" in the deliverables. End with a final "Accept delivery" / "Request changes" AskUserQuestion presenting the Launch Dossier, each option carrying a populated per-option `description` (Accept delivery: what accepting finalizes; Request changes: what gets reworked) per AskUserQuestion rule 4 — never bare labels.
3. Present the hand-off prompt in a copyable block AND save it as BUILD-HANDOFF.md alongside the PRD and prototype files — presented per the DELIVERABLE PRESENTATION rule. Then give platform-tailored delivery instructions (from STEP 0):
   - **Claude Code CLI** → enter the target directory, run `claude`, paste the prompt, and attach PRD.md, OWNER-TASKS.md, and the prototype frames.
   - **Claude Cowork** → download the deliverables from your outputs, then start Claude Code on a machine that has a terminal plus build credentials (gh, Vercel, Supabase, Docker, ElevenLabs) — or reconsider "Build it out now" here, since Cowork has no local terminal for a second session.
   - NEVER point at `scripts/package-plugin.py` — that packages the plugin, not the product.

   Then STOP — nothing further in this session.

## Closing

STOP at the end of whichever branch ran — Branch A after GATE 4 (Accept delivery / Request changes), Branch B after saving and presenting BUILD-HANDOFF.md. Control returns to the `saas-launch-blueprint` orchestrator, which also halts here — Phase 3.5 is the terminal phase of this session. There is no next phase either way: on Branch B the build (Phase 4) runs only when the founder starts a separate Claude Code session with the BUILD-HANDOFF.md prompt; on Branch A the build already ran in this session and finished at GATE 4.
