# HARNESS.md — agent-harness overlays

This is the source of truth for turning these tier directories into the
agent-harness layer of a real product repo. It is deterministic on purpose:
run the same tier choice, in the same order, and every product ends up with
byte-identical harness files for that tier. If a step here is unclear or out
of date, fix this file — don't improvise around it.

**This file is NOT copied into products.** Only the contents of `tier-1/`
through `tier-N/` are copied — `HARNESS.md` stays behind in the plugin as
documentation for whoever maintains this template.

## 1. What this is

Four cumulative overlay directories that instantiate the agent-orchestration
harness described at a prose level in the PRD's "Agent orchestration" and
"Agent harness" sections — AGENTS.md rulebook, `init.sh` command dispatcher,
task tracking, memory files, a structured crew of named subagents, workflow
playbooks, and (at the top tier) autonomous-loop infrastructure with
observability and a blocking Stop gate. Each tier is a strict superset of
the one below it — see §3.

Every tier ships BOTH instruction files: `AGENTS.md` (the agent-agnostic
rulebook every coding agent reads) and `CLAUDE.md` (Claude Code's entry
point — points at AGENTS.md and lists the Claude-specific machinery active
at that tier). Tiering changes only how in-depth the harness is — how
strict and how constrained agents are — never which of the two files exists.

| Tier | Name | Adds |
|---|---|---|
| `tier-1` | Minimal | `AGENTS.md` (rulebook: non-negotiables, domain rules, orchestration roles, Definition of Done), `CLAUDE.md` (pointer to AGENTS.md), `init.sh` (install/verify/test/start dispatcher) |
| `tier-2` | Guarded | + `.claude/settings.json` hooks (migrations append-only guard, hook self-protection, destructive-Bash guard, commit-identity guard — no AI attribution, no author/identity overrides, `feature_list.json` schema + single-WIP validation), `feature_list.json`, `claude-progress.md`, `session-handoff.md`; `AGENTS.md` + `CLAUDE.md` supersets |
| `tier-3` | Structured Crew | + `.claude/agents/` (surface-builder, backend-engineer, qa-verifier, code-reviewer, research-scout), `workflows/` PRD-keyed playbooks (payment-lifecycle, tenant-lifecycle, surface-build, release, README routing table), shared task-id conventions; `AGENTS.md` + `CLAUDE.md` supersets |
| `tier-4` | Autonomous Factory | + `clean-state-checklist.md`, `evaluator-rubric.md`, `logs/` JSONL observability, `autonomous-loop.md`, `.claude/settings.json` superset adding a `SessionStart` reminder + a blocking `Stop` gate; `AGENTS.md` + `CLAUDE.md` supersets |

The tier is chosen once, during the Phase 2 flight-plan interview, and
recorded in the PRD's "Agent harness" section — `saas-scaffold` reads it
from there and never guesses.

## 2. Directory layout

```
templates/agent-harness/
├── HARNESS.md              # this file — NOT copied
├── tier-1/
│   ├── AGENTS.md
│   ├── CLAUDE.md
│   └── init.sh
├── tier-2/
│   ├── AGENTS.md            # tier-1 + pure append
│   ├── CLAUDE.md            # tier-1 + pure append (Guarded machinery)
│   ├── .claude/settings.json
│   ├── feature_list.json
│   ├── claude-progress.md
│   └── session-handoff.md
├── tier-3/
│   ├── AGENTS.md            # tier-2 + pure append
│   ├── CLAUDE.md            # tier-2 + pure append (Crew machinery)
│   ├── .claude/agents/*.md
│   └── workflows/*.md
└── tier-4/
    ├── AGENTS.md            # tier-3 + pure append
    ├── CLAUDE.md            # tier-3 + pure append (Factory machinery)
    ├── .claude/settings.json  # superset of tier-2's
    ├── clean-state-checklist.md
    ├── evaluator-rubric.md
    ├── autonomous-loop.md
    └── logs/.gitkeep
```

## 3. Overlay mechanics — replace, never merge

Files that grow across tiers (`AGENTS.md`, `CLAUDE.md`,
`.claude/settings.json`) ship as
**complete superset files** in each higher tier, not as diffs or partial
fragments. Instantiation is an ordered `cp -R`, tier by tier, from `tier-1`
up to the chosen tier N — a later tier's copy overwrites a same-path file
from an earlier tier on purpose:

```bash
target=path/to/new-product
tier=3   # from the PRD's Agent harness section — ask if absent, never guess

for t in $(seq 1 "$tier"); do
  cp -R "${CLAUDE_PLUGIN_ROOT}/templates/agent-harness/tier-$t/." "$target/"
done
```

This is why each higher-tier `AGENTS.md` and `CLAUDE.md` is written as
"previous tier's full content, PLUS appended sections" rather than just the
new sections —
after the loop runs, whatever tier-N's copy left on disk IS the file, in
full, with nothing to merge. Same for `.claude/settings.json` at tier 4: it
is not "tier-2's settings plus a patch," it is tier-2's `PreToolUse` /
`PostToolUse` arrays reproduced byte-for-byte plus new `SessionStart` and
`Stop` entries, so the ordered copy produces the correct final file whether
or not `tier-2/.claude/settings.json` was ever independently copied first.

**Superset invariant**: for any chosen tier N, every file that exists after
instantiating tier N-1 alone also exists after instantiating tier N (same
path; content identical unless that path is one of the three superset files
above, in which case content is the superset). This holds by construction
because the copy loop is ordered and cumulative, and because AGENTS.md /
CLAUDE.md / settings.json are authored as supersets rather than patches —
verify a change to any of them preserves it with `head -n
<tier-(N-1)-line-count> tier-N/AGENTS.md | diff - tier-(N-1)/AGENTS.md`
(same for `CLAUDE.md`) and `jq -S '.hooks.PreToolUse, .hooks.PostToolUse'`
diffed between `tier-2` and `tier-4`.

## 4. Placeholder map

The agent-harness overlay copy happens **before** the saas-monorepo
template's own placeholder-substitution pass (see
`../saas-monorepo/SCAFFOLD.md` §3.2 and §7), so the same single
find-and-replace sweep across the target directory covers harness files for
free. Reuse ONLY the five placeholders already established by the monorepo
template — never invent a new one here:

| Placeholder | Meaning | Appears in |
|---|---|---|
| `{{PRODUCT_NAME}}` | Human-readable product name | `AGENTS.md`, `claude-progress.md`, `session-handoff.md`, `autonomous-loop.md` |
| `{{PRODUCT_SLUG}}` | Lowercase, hyphenated slug | `AGENTS.md` |
| `{{PRODUCT_DESCRIPTION}}` | One-line description | `AGENTS.md` |
| `{{PRIMARY_LOCALE}}` | Default locale code | `AGENTS.md` |
| `{{CONTACT_EMAIL}}` | Support/owner contact | `AGENTS.md` |

## 5. Post-copy steps

Run these immediately after the tier loop in §3, before anything else:

```bash
chmod +x "$target/init.sh"

# tier >= 2 only — settings.json and feature_list.json now exist
jq empty "$target/.claude/settings.json"
jq empty "$target/feature_list.json"

bash -n "$target/init.sh"
```

All three must succeed. A non-zero exit means the copy or substitution step
upstream is broken — fix the template, don't hand-patch the product repo's
copy.

## 6. Determinism statement

Given the same tier choice N and the same five placeholder values, the
ordered `cp -R` loop in §3 followed by the standard substitution pass (per
`../saas-monorepo/SCAFFOLD.md` §3.2) produces byte-identical harness output
across runs, machines, and time — there is no randomness, no network call,
and no CLI-version drift in this path (contrast with e.g. `shadcn` component
generation, which the monorepo template deliberately vendors instead of
regenerating for exactly this reason). Re-running the loop for the same tier
into a fresh directory and diffing against a prior run should always come
back empty.
