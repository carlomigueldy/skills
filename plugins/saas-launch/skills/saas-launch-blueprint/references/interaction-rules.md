# Interaction Rules

Canonical home for the SaaS Launch Blueprint's **process rules** — how you work and how you talk to the founder, as opposed to what the product/business constraints are (those live in `shared-context.md`) or what the engineering/design/video standards are (those live in `tech-design-video.md`). Every phase skill in this workflow (Phase 1 ideation, Phase 2 PRD, Phase 3 prototype, Phase 3.5 handoff) reads this file at its start and operates under these rules for its entire run. Nothing here is phase-specific; it applies EVERYWHERE across the workflow. Throughout this file, first-person pronouns (I / ME / MY) refer to the USER — the founder; "you" is Claude.

## Delegation Model (this session, Phases 1–3.5)
You, the executing agent, are the strategist. Reserve your own context and effort for the work only you can do well: planning, brainstorming, architectural design, interviewing the user, writing the PRD, and writing the handoff prompt. Do NOT do heavy legwork inline:
- Web research — market sizing, competitor scans, pricing references, free-tier limits, domain availability checks, legal/regulatory references — fans out to subagents: Sonnet for research requiring judgment, Haiku/Explore for simple lookups. Launch independent research tasks in PARALLEL and synthesize their findings yourself.
- Simple, trivial, mechanical tasks — file conversions, boilerplate, renames, packaging, render invocations — delegate to Haiku-class helpers whenever possible.
- Keep delegation scoped: subagents fetch and summarize; YOU decide. Never outsource the ideation scoring, PRD judgments, design direction, or anything the user will be interviewed about — those are the deliverables this skill exists for.
Why this matters: inline research bloats your context and measurably degrades the strategic outputs (idea quality, PRD coherence, prompt precision) that are your actual job — and parallel fan-out is faster anyway.

## Known Failure Modes (each observed in real runs — do not repeat them)
1. **Widget with no context.** A selection widget appeared listing bare product names; the user had nothing to base a decision on. The analysis existed only as narration between tool calls, which the UI summarized away. This is why AskUserQuestion rules 1–3 demand the standalone write-up land visibly BEFORE the widget.
2. **Deliverables never shown.** A prototype phase "finished" with files written to disk and described in prose — nothing clickable, nothing rendered — and the approval gate fired anyway. This is why the DELIVERABLE PRESENTATION rule requires files in front of the user before any gate question.
3. **HTML instead of video.** The pitch "clip" shipped as an HTML composition with no rendered MP4, quietly reframed as if that were the deliverable. This is why the Video tooling constraint (see `tech-design-video.md`) counts only a rendered .mp4 — and why the clip is opt-in (Phase 3 STEP 3) rather than silently attempted.
4. **Stack drift.** Builds shipped without Tailwind v4 + shadcn/ui, or with hand-rolled design systems. This is why the UI stack is non-negotiable in production and the design system must derive from shadcn/ui with a deterministic scaffold in the PRD.

These are not hypotheticals; each one cost the user a session. Whenever speed and one of these rules pull in opposite directions, the rule wins.

## AskUserQuestion rules (apply EVERYWHERE, HARD REQUIREMENT)
1. ALWAYS deliver a full write-up of the options BEFORE calling AskUserQuestion — each option's name, a clear explanation of what it is, key details, and trade-offs. Never call AskUserQuestion cold.
2. The write-up must reach the user as a COMPLETE, VISIBLE message before the widget appears. In Cowork, push it via the user-message tool (it renders verbatim mid-run), then call AskUserQuestion. In clients without that tool, emit the write-up as the final uninterrupted text block immediately preceding the AskUserQuestion call. What is forbidden is narration scattered between unrelated tool calls — that text gets summarized away and the user sees a context-free widget.
3. SELF-CHECK before every AskUserQuestion call: has the full write-up for these exact options visibly reached the user? If not, STOP and deliver it first.
4. Every option in the widget must still carry a meaningful description — the widget summarizes; the write-up is where full context lives. Widget option names must match the write-up's names exactly.
5. When multiple decisions happen back to back (segment → scope → product idea), EACH decision gets its own write-up and its own widget — never chain widgets without the intervening write-ups.
6. VISUAL COMPARISON WIDGETS: for major selections (customer segment, geographic scope, product idea, tech-stack deviations), ALSO render an inline visual comparison scorecard when the environment supports inline HTML widgets. It SUPPLEMENTS the text write-up, never replaces it.
7. OPTION CAP: the widget holds at most 4 options. When a decision has more, show the top 4 by the decision's own ranking (segments: listed order; ideas: total score, recommendation first) and state in the write-up that the remaining options are reachable via "Other". The write-up always covers ALL options, capped widget or not.

## APPROVAL GATES (hard rule)
Every phase ENDS with an explicit approval prompt via AskUserQuestion carrying THREE standing options: "Approve — proceed", "Request changes" (iterate in place), and "Go back — revisit an earlier decision" (reopens the named earlier phase; re-approving an earlier gate invalidates all downstream deliverables, which must be revised or regenerated). NO phase begins until the previous gate is approved. Gates exist so a wrong early guess — segment, idea, pricing — never fossilizes into the expensive phases.

Each phase skill's own gate (GATE 1, GATE 2, GATE 3 — Phase 3.5 has no gate of its own; the final "Accept delivery" gate runs in the separate build session, encoded in the Phase 3.5 handoff prompt) adds its own phase-specific option labels on top of these three standing options — see that phase skill for the exact wording. The mechanics below are the same at every gate regardless of phase:
- **"Approve — proceed"** hands control back to the orchestrator, which immediately invokes the next phase's skill. A phase skill finishing is NOT the end of the workflow — it only pauses at the gate for the user's decision.
- **"Request changes"** keeps control inside the current phase skill: iterate in place and re-present the same gate. The orchestrator does not advance.
- **"Go back — revisit an earlier decision"** returns control to the orchestrator, which re-invokes the named earlier phase's skill; that phase's downstream deliverables are treated as invalidated and must be revised or regenerated once the earlier decision changes.

## DELIVERABLE PRESENTATION (hard rule)
A phase is NOT complete when its deliverables are merely written to disk and described in text — they must be put IN FRONT of the founder before the gate question appears:
- In Claude Cowork: present every deliverable file with the file-presentation tool (clickable cards), AND render HTML deliverables inline as widgets. For LARGE sets (e.g., a storyboard), cards for ALL files but inline rendering for a representative subset only (3–5 key frames or a thumbnail index) — duplicating every byte inline defeats the Delegation Model's context economy.
- In Claude Code / Claude Desktop: print each deliverable's absolute path in a copyable block with the one-line command to open it (`wslview` in WSL, `start` on Windows, `open` on macOS), or clickable file:// links — whichever gives one-click access.
- NEVER call the gate AskUserQuestion before the deliverables under review have been presented this way.
