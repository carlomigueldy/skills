# Clean-State Checklist

Run before ending ANY session and before the Stop gate fires. Every box must be checked — the Stop gate blocks on the first false one (see `.claude/settings.json`).

- [ ] No feature in `feature_list.json` is `in_progress`. Every feature is `not_started`, `passing`, or `blocked` (with notes).
- [ ] `./init.sh verify` exits 0.
- [ ] `./init.sh test` (Vitest) exits 0.
- [ ] `git status` is clean, OR every remaining change is intentional and already committed.
- [ ] `claude-progress.md` — **Current Verified State** reflects reality (not a stale prior session) and a new entry was appended under **Session Records**.
- [ ] `session-handoff.md` was rewritten for the NEXT session: Next task, In-flight & blockers, Verify first — no stale pointers to work already finished.
- [ ] No debug artifacts left behind: no stray `console.log`/`debugger`, no scratch files, no commented-out blocks, no TODO markers standing in for real work.
- [ ] `logs/` JSONL events for this session are flushed to disk (not buffered in memory).

If any box is unchecked, fix it before stopping — do not hand off a dirty state.
