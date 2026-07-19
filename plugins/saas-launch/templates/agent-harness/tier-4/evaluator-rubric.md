# Evaluator Rubric

The `qa-verifier` agent scores every feature against this rubric before flipping it to `passing` in `feature_list.json`. Score each dimension 0–2. A feature PASSES only if the total is **>= 10 AND no dimension scored 0**. Anything else is `blocked` with notes explaining the gap — never `passing`.

| Score | Meaning |
|---|---|
| 0 | Missing or broken — disqualifying on its own |
| 1 | Present but incomplete or shaky |
| 2 | Solid, meets the bar |

## Dimensions

1. **Correctness of user-visible behavior** — does the feature do what the PRD/task description says, for the actual user-facing flow (not just the happy path internally)?
2. **Completeness vs Definition of Done** — every item in AGENTS.md's Definition of Done is satisfied for this feature, not partially.
3. **Verification evidence quality** — the evidence attached to the feature (Playwright MCP run, Vitest output, screenshots) is real, current, and actually demonstrates the claim, not a stale or generic note.
4. **Code quality & convention adherence** — follows AGENTS.md non-negotiables (stack, RLS + tenant-status, append-only migrations, no secrets), reasonably idiomatic, no obvious debt dumped for later.
5. **UX quality bar** — loading/error/empty/offline states present, responsive across breakpoints, basic accessibility (labels, focus, contrast) — not just the default state.
6. **Tracking & memory hygiene** — `feature_list.json`, `claude-progress.md`, and `session-handoff.md` are all updated consistently with this feature's outcome.

## Recording

Write the per-dimension scores, total, and pass/fail into the feature's evidence entry in `feature_list.json`. A `blocked` verdict must name the specific dimension(s) that failed and what would need to change to pass.
