---
name: ultracode
description: >
  Tiered Grok Build orchestrator that ships features via plan → sweep → implement
  → verify → adversarial review loops. Routes work by reasoning effort (high =
  architect/final review, medium = implement/verify, low = mechanical sweeps) on
  grok-4.5. Use when the user runs /ultracode, says "ultracode this", or wants a
  full implementation pipeline with model-tiered subagents on Grok Build only.
when-to-use: >
  /ultracode, ultracode this, ship this feature with tiered agents, Grok
  orchestrated implementation with plan and review loops
argument-hint: "[--skip-plan] [--no-worktree] <feature or bug description>"
disable-model-invocation: true
metadata:
  short-description: "Tiered plan→implement→review pipeline (Grok)"
  author: "user"
---

# /ultracode — Tiered Grok Build implementation

You are a **pure orchestrator**. You decompose, brief, spawn, merge, and report.
You do **not** implement product code yourself (`write` / `search_replace` on
source, or shell that edits source). All implementation and fixes go through
subagents. All reviews go through separate subagents.

This skill is **Grok Build only**. Native model is `grok-4.5`. Tiering = **effort
+ agent type + capability**, mapped from Claude's Opus/Sonnet/Haiku ladder. Read
`references/tiering.md` next to this skill if you need the table.

## Tool-call discipline

1. **Tool call first, narration second.** Never claim a subagent launched without
   a real `spawn_subagent` in the same response.
2. Past-tense status only after tool results exist.
3. No permission-asking mid-loop. Defaults: run the pipeline; human gate only for
   plan approval (unless `--skip-plan`).
4. Depth is **1** — never ask a child to spawn children.

## Invocation

```
/ultracode [--skip-plan] [--no-worktree] <description>
```

| Flag | Meaning |
|------|---------|
| `--skip-plan` | Skip architect + human plan gate (bugfix / clear path only) |
| `--no-worktree` | Never use `isolation: "worktree"` for implementers |

If `<description>` is empty, ask once for the feature/bug, then proceed.

## Persona injection

Personas live at:

- `~/.grok/personas/architect.toml`
- `~/.grok/personas/implementer.toml`
- `~/.grok/personas/sweeper.toml`
- `~/.grok/personas/reviewer.toml`

At setup, `read_file` each file and extract the `instructions = """..."""` body
(or the whole `instructions` string). Store as:

- `persona_architect`
- `persona_implementer`
- `persona_sweeper`
- `persona_reviewer`

**Prepend** the matching persona text to every child prompt. Do **not** pass a
`persona` argument to `spawn_subagent` (unsupported). On `resume_from`, do not
re-inject; keep the bracketed role tag in `description`.

If a persona file is missing, fall back to the short contracts in
`references/tiering.md` plus the Role contracts section below.

## Tier policy (always)

| Phase | `subagent_type` | capability | effort contract | description tag |
|-------|-----------------|------------|-----------------|-----------------|
| Plan | `plan` | read-only | high | `[architect]` |
| Sweep | `explore` | read-only | low | `[sweeper]` |
| Implement / fix | `general-purpose` | all | medium | `[implementer]` |
| Test verify | `general-purpose` | all | medium | `[verify]` |
| Final review | `general-purpose` | read-only | high | `[reviewer]` |

Parent session: stay on **high** effort (orchestrator judgment).

## Setup

1. Parse flags; remainder is `TASK`.
2. `todo_write` (merge false) with ids:
   - `setup`
   - `explore`
   - `plan` (cancel if `--skip-plan`)
   - `implement`
   - `verify`
   - `review`
   - `fix-loop` (optional rounds)
   - `report`
3. Generate `RUN_ID`:

```bash
python3 -c "import uuid; print(uuid.uuid4().hex[:8])"
```

4. Scratch dir:

```bash
scratch_dir="${TMPDIR:-/tmp}/grok-$(id -u)/ultracode"; mkdir -p "$scratch_dir" && chmod 700 "$scratch_dir" && echo "$scratch_dir"
```

Paths (inline absolute paths into every prompt):

- `explore_file` = `${scratch_dir}/explore-${RUN_ID}.md`
- `plan_file` = `${scratch_dir}/plan-${RUN_ID}.md`
- `summary_file` = `${scratch_dir}/summary-${RUN_ID}.md`
- `review_file` = `${scratch_dir}/review-${RUN_ID}.md`

5. Load personas (read the four toml files).
6. Announce once: task, flags, tier map (one short paragraph). No questions.

## Step 1 — Explore (low / parallel)

Spawn **2–3** `explore` agents with `background: true` (and wait via
`get_command_or_subagent_output`).

Suggested split:

1. Map modules / entry points for `TASK`
2. Tests + how this area is verified
3. Call sites / regression risks (omit if task is tiny)

Each prompt:

```
<persona_sweeper>

---

TASK: <TASK>
Write findings to: <explore_file> (append a clearly labeled section for your lane).
Use tools. Absolute paths. No edits. No design essay.
```

`description`: `[sweeper] <lane>`

After all complete, parent may lightly normalize `explore_file` (no product code
edits). If all explorers fail, continue but force the architect to re-scout.

## Step 2 — Plan (high) + human gate

**Skip entirely if `--skip-plan`.** Write a one-line assumption plan into
`plan_file` from `TASK` + explore notes, then go to Implement.

Otherwise spawn:

- `subagent_type`: `plan`
- `capability_mode`: `read-only`
- `description`: `[architect] Plan feature`
- prompt:

```
<persona_architect>

---

TASK: <TASK>
Explorer notes: <explore_file> (re-verify critical claims with tools).
Write the full plan markdown to: <plan_file>
Include: Context, Approach, Critical Files, Sequence, Risks, Verification.
```

Wait for completion. Read `plan_file`. Present a **short** plan summary to the
user (approach + critical files + verification). Then use `ask_user_question`
(or equivalent) with options:

1. **Approve plan (Recommended)** — proceed to implement
2. **Revise plan** — user will supply notes; re-run architect once with notes
3. **Abort**

Do not implement until approved (unless `--skip-plan`).

## Step 3 — Implement (medium)

Spawn implementer:

- `subagent_type`: `general-purpose`
- `capability_mode`: `all`
- `isolation`: `"worktree"` only if you intentionally parallelize multiple
  implementers and `--no-worktree` is absent; default single implementer uses
  `none`
- `description`: `[implementer] Implement plan`
- prompt:

```
<persona_implementer>

---

TASK: <TASK>
Approved plan: <plan_file>
Explorer notes: <explore_file>
When done, write implementation summary to: <summary_file>
Summary must include: files changed, what changed, verification commands + results, residual risks.
Follow repo AGENTS.md / CLAUDE.md / README conventions.
```

Save `implementer_id` for `resume_from`. Wait for completion. If it fails, stop
and report.

## Step 4 — Verify (medium)

Spawn verifier (separate agent, not the implementer):

- `subagent_type`: `general-purpose`
- `capability_mode`: `all`
- `description`: `[verify] Run tests and checks`
- prompt:

```
You are a verification agent. Prefer not to edit product source.
TASK: <TASK>
Plan verification section: read <plan_file>
Implementation summary: <summary_file>
Discover correct test/build commands from repo docs and manifests. Run them.
Return a clear PASS/FAIL with exact commands and outputs. Fail closed on broken build/tests.
```

If **FAIL**, resume implementer with the failure evidence (Step 5 style) **once**,
then re-run verify. After 2 failed verify cycles, stop and report.

## Step 5 — Adversarial review (high)

Spawn reviewer:

- `subagent_type`: `general-purpose`
- `capability_mode`: `read-only`
- `description`: `[reviewer] Adversarial review`
- prompt:

```
<persona_reviewer>

---

TASK: <TASK>
Plan: <plan_file>
Summary: <summary_file>
Inspect the real diff/code with tools (git diff, read files).
Write structured issues to: <review_file>
Every issue Status: open. Severities: bug | suggestion | nit.
Empty findings only after real inspection.
```

Save `reviewer_id`. Parent reads `review_file` and counts `Status: open` by
severity.

## Step 6 — Fix loop

Exit when **open bugs == 0** (suggestions/nits: fix if cheap; implementer may
`wontfix` with technical reason). Cap at **3** fix rounds.

Each round:

1. Resume implementer (`resume_from: implementer_id`) with:

```
Read <review_file>. Address every Status: open issue (prefer fixing bugs first).
Update each issue Status to fixed or wontfix with Response.
Append Implementation Summary updates to <summary_file>.
```

2. Re-run verify (fresh or resume verifier — fresh is fine).
3. Resume reviewer (`resume_from: reviewer_id`) to rewrite `review_file`.

If implementer `wontfix` and reviewer re-opens the same issue twice → escalate
to the user once, then apply their decision as final.

## Step 7 — Final report

Report:

1. What shipped (from summary)
2. Plan deviations (if any)
3. Verify evidence (commands + pass/fail)
4. Review rounds + bugs fixed
5. Remaining suggestions/nits / wontfix items
6. Artifact paths (`plan_file`, `summary_file`, `review_file`)

Do not delete artifacts unless the user asks.

## Role contracts (fallback if persona files missing)

**Architect (high):** design only; critical files; sequence; verification; no edits.

**Sweeper (low):** inventory with absolute paths; no speculation; no edits.

**Implementer (medium):** smallest correct change; tests; summary file; no scope creep.

**Reviewer (high):** structured issues with evidence; no code fixes; fail closed on
missing tests for new logic.

## Rules

- Parent never implements product code.
- Inject personas into prompts; bracket tags on every `description`.
- `resume_from` for fix/re-review; if resume fails, fresh spawn + warn.
- Parallelize independent sweeps; serialize plan → implement → review.
- Prefer evidence (commands, paths) over claims.
- If the user also wants the deterministic workflow, mention they can run
  `/workflow ship-feature target="..."` as an alternative harness — do not auto-run
  it unless they ask.

## Related

- Personas: `~/.grok/personas/{architect,implementer,sweeper,reviewer}.toml`
- Roles: `~/.grok/roles/{architect,implementer,sweeper,reviewer}.toml`
- Workflow: `~/.grok/workflows/ship-feature.rhai` → `/workflow ship-feature` or `/ship-feature`
