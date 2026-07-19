# Claude — read this first

Read `AGENTS.md`. It is the single rulebook for this repo — every non-negotiable, domain rule, orchestration role, and the Definition of Done live there, not here.

## Claude-specific machinery active at this tier (Guarded)

- `.claude/settings.json` hooks enforce the rulebook for you: edits to applied `supabase/migrations/*` files are blocked (create a NEW migration instead), the hook config itself is edit-protected, destructive Bash against protected paths is blocked, and every write to `feature_list.json` is validated (valid JSON, legal status values, at most ONE `in_progress`).
- Track work ONLY in `feature_list.json`; a feature is `passing` only with `verification` and `evidence` filled.
- At session start read `claude-progress.md` (Current Verified State) and `session-handoff.md`; before ending, update the verified state, append a session record, and rewrite the handoff.
