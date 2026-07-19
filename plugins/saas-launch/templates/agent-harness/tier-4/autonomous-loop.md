# Autonomous Loop — {{PRODUCT_NAME}}

The unattended operating loop for a session running without a human in the room. Every iteration is a full pass through this loop; the Stop gate in `.claude/settings.json` is the exit contract — it blocks session end while any feature is `in_progress`, forcing the loop to either finish or explicitly mark `blocked`.

## Loop

1. **Read memory** — `claude-progress.md` (Current Verified State) and `session-handoff.md` (Next task, In-flight & blockers, Verify first). Never start work blind.
2. **Pick the highest-priority `not_started` feature** in `feature_list.json`. Respect the single-WIP rule — only one feature may be `in_progress` at a time.
3. **Mark it `in_progress`** in `feature_list.json` before touching code.
4. **Route via `workflows/`** — match the feature's PRD area to the right playbook (`workflows/README.md` has the routing table) and follow it.
5. **Crew implements** — the relevant `.claude/agents/` role (surface-builder, backend-engineer) does the work per AGENTS.md non-negotiables.
6. **`qa-verifier` verifies** — runs the verification loop (Playwright MCP + Vitest), attaches evidence.
7. **Score against `evaluator-rubric.md`** — 6 dimensions, 0–2 each.
8. **If passing (>= 10, no zero dimension) with evidence attached** — flip the feature to `passing`, update `claude-progress.md` and `session-handoff.md`, go to step 2.
9. **If blocked** — mark the feature `blocked` with notes explaining exactly what's missing or who needs to decide, update memory, go to step 2 (skip it, don't stall the loop on it).
10. **Repeat** until no `not_started` features remain, or every remaining feature is `blocked`.

## Stopping

Before ending the session, run `clean-state-checklist.md` in full. The Stop gate enforces the single hard requirement (no `in_progress` feature) automatically; the rest of the checklist is on the agent's discipline. A blocked backlog with clear notes is a valid stop state — a silent `in_progress` feature is not.
