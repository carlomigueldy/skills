---
name: herdcraft
description: Use when building a feature or product through multiple autonomous coding agents managed in Herdr, especially when work must be parallelized, isolated, recovered after coordinator restarts, integrated, independently verified, or carried through staging and release gates.
---

# Herdcraft

## Overview

Use Codex as the coordinator and Herdr as the durable process control plane. Treat Git, artifacts, tests, and a run ledger as truth; agent lifecycle labels and chat are only signals.

**REQUIRED SUB-SKILL:** Use `herdr` for current CLI discovery, pane control, and lifecycle semantics.

## Preflight

1. Verify the `herdr` and `find-skills` skills are available in the active Codex environment and read both `SKILL.md` files completely. If either skill is missing, stop and report the repo-local installation commands from the plugin README; do not weaken or silently replace either prerequisite.
2. Verify `HERDR_ENV=1`. If false, stop; do not control another Herdr session from outside Herdr.
3. Run `herdr --help` and the relevant bare command groups. The installed CLI is authoritative. Do not transfer flags between `agent` and `pane` commands; validate the exact surface before use.
4. Resolve the repository root using `references/capabilities-and-delivery.md`. If no repository exists, choose research-only, locate/request existing code, create an explicit child project for a new build, or use a recorded single-writer non-Git fallback. Never initialize a broad parent directory. For a new Git project, create a minimal root-owned bootstrap commit before any worktree or capability branch.
5. Inspect repository instructions, dirty state, current branch, test commands, deployment path, and rollback path.
6. Preserve unrelated user changes. Never assign concurrent writers to one dirty checkout.
7. Establish a product contract before dispatching builders: user outcome, scope, non-goals, interfaces, acceptance scenarios, safety boundaries, and human gates.
8. Copy `assets/delivery-profile.yaml`; record constraints, tradeoffs, budgets, delivery level, and promotion triggers before selecting teams.

## Create Durable Run State

When the bundled plugin scripts are present, resolve the plugin root three directories above this `SKILL.md` and initialize an existing Git repository with:

```bash
python3 <plugin-root>/scripts/init-run.py --repo <repo> --run-id <id> \
  --objective <objective> --team <team-id>
```

Repeat `--team` for each active team. The helper refuses unsafe identifiers, unresolved Git history, and overwriting an existing run. It creates `.orchestration/runs/<run-id>/` from the bundled contracts; instantiate task contracts from its `templates/` directory as tasks become ready. For research-only non-repository work, use a task-local output directory instead of pretending worktrees exist. Keep secrets out of these files.

After resolving the product, delivery, team, and capability contracts, set run status to `ready` and run `python3 <plugin-root>/scripts/validate-run.py <run-dir>` before dispatch. The validator deliberately rejects unresolved dispatch placeholders once a run leaves `planning`.

At closeout, use `python3 <plugin-root>/scripts/summarize-run.py <run-dir>` as the factual draft, complete every `final-report.md` field from observed evidence, record verification and retirement, set run status to `completed`, then run `validate-run.py` again. Completed runs fail validation when evidence, retirement, or report fields remain unresolved. If the helpers are unavailable, reproduce the same asset layout manually rather than weakening the contract.

Update run state after every dispatch, lifecycle transition, artifact report, verification result, integration decision, retry, and escalation. Commit it when appropriate. Chat is never the only ledger: a restarted coordinator must reconstruct the run from Herdr, Git, task files, and test evidence.

Read `references/operating-contract.md` before running a multi-wave build, recovering a run, or releasing.

## Build the Dependency Graph

Dispatch only tasks that satisfy all four conditions:

| Condition | Required evidence |
|---|---|
| Independent | No unresolved upstream product or interface decision |
| Owned | Exact files, subsystem, branch, and sole writer are named |
| Verifiable | Deterministic acceptance commands or inspection criteria exist |
| Useful | Its result changes implementation, integration, or release decisions |

Do not honor an arbitrary agent count. Use one strong agent when work is tightly coupled. Use read-only investigators for parallel diagnosis. Use isolated Git worktrees for concurrent writers. Complete product and architecture decisions before downstream builders begin.

Apply the delivery profile at root and team levels. Reuse the existing stack and choose the minimum sufficient architecture. Add agents, services, abstractions, dependencies, tools, or skills only when they resolve an acceptance, ownership, risk, or evidence need within budget.

## Select Specialists and Models

Read `references/specialists.yaml` before assigning agents. Treat it as the canonical default roster and escalation policy. Override it only for a user-requested model, unavailable model, observed task-specific reason, or project instruction; record the reason and fallback in run state.

Keep the hierarchy shallow: root coordinator -> team lead -> worker. Root owns the global ledger and release decision. A team lead may fan out to at most eight direct workers within its recorded delegation budget; use fewer when the dependency graph does not justify eight. Workers never delegate.

Keep quality independent: assign the `quality-lead` directly under root, then place reviewers and release verifiers under that lead. Never route their certification through a builder lead.

Verify a model with a real inference before its first assignment in the active provider. `gpt-5.4-mini` is conditional and read-only; fall back to `gpt-5.6-luna` when unavailable. Do not treat a listed model or successful agent startup as proof of inference usability.

Record agent name, specialist ID, model, reasoning effort, model-inference evidence, parent, access mode, fallback, delegation budget, verifier independence, task ID, Herdr pane ID, worktree, lifecycle state, and task state for every assignment. Prefer a verifier model different from the builder model.

## Delegate Through Team Leads

Read `references/team-operations.md` and instantiate `assets/team-contract.yaml` before a lead launches children. Activate only teams required by the dependency graph.

Root delegates a subsystem outcome to a lead. The lead may implement it directly or decompose it, create child contracts/worktrees, select allowed specialists, fan out and monitor up to eight direct workers, verify their evidence, integrate its owned surface, report to root, and retire its children. The eight-worker ceiling is per lead and includes all workers spawned by that lead during the run, not only concurrently active workers. Workers never delegate. Root retains the global ledger, cross-team integration, human gates, and release decision.

Require leads to send `CHECKPOINT`, actual `INCIDENT`, and `FINAL_HANDOFF` reports with `assets/team-report.md`. Never manufacture an incident when none occurred.

## Equip Teams With Skills and Tools

Read `references/capabilities-and-delivery.md`. Require each lead to inspect existing repo-local skills, then use `find-skills` only for concrete gaps. Put the resolved `find-skills` SKILL.md path in the lead contract, require the lead to read it completely before discovery, and record that load in `assets/capability-ledger.yaml`. Vet and record candidates there; install accepted skills repo-locally with `npx skills add <package>`, never `-g`. Review and commit the capability diff before creating child writer worktrees from that commit.

List only task-required skill names/paths in each child contract. Require children to read those SKILL.md files completely before acting and report successful loading. Inventory configured Playwright MCP, Chrome DevTools MCP, Sentry MCP, `agent-browser`, and other relevant tools; assign each only to an evidence question it is suited to. Missing skills, MCP connections, or credentials are recorded constraints, not permissions to invent setup.

## Dispatch Through Herdr

Prefer Herdr-created worktrees for writing agents. Parse opaque IDs from command JSON; never infer them.

```bash
herdr worktree create --cwd "$PWD" --branch agent/<task-id> --base <base-ref> --no-focus
herdr agent start <unique-name> --kind <codex-or-supported-kind> --pane <returned-root-pane-id>
herdr agent prompt <unique-name> "$(cat <task-contract-path>)"
```

For Codex, pass the selected model and effort after Herdr's `--` separator:

```bash
herdr agent start <unique-name> --kind codex --pane <pane-id> -- \
  -m <model> -c 'model_reasoning_effort="<effort>"' --no-alt-screen
```

Start independent prompts without `--wait`, then monitor them concurrently. Use `--wait` for bounded follow-ups. Give each agent the task contract plus instructions to report commit SHA or artifact path, changed files, commands and results, assumptions, and unresolved risks.

## Reconcile, Do Not Merely Wait

Run a coordinator loop:

1. Read `herdr agent list`, then `agent get` and `agent read` for changed or uncertain agents.
2. Treat `done` and `idle` as settled lifecycle states, not proof of correctness.
3. Inspect `blocked` before answering. Escalate only when the choice requires new authority, destructive action, secrets, spending, external communication, or unresolved product semantics.
4. Inspect `unknown`; never resend blindly. Determine whether output advances, a question is visible, the process exited, or durable work already exists.
5. Verify reported commits, diffs, artifacts, and tests independently.
6. Update the durable ledger and unlock newly ready tasks.

Retry only a proven failed or absent deliverable. Cap ordinary retries at two; after that, change the task boundary, agent, or plan rather than repeating the same prompt.

Use the correct read surface:

```bash
# Agent lifecycle/UI detection
herdr agent read <agent-name> --source detection --lines 100

# Raw terminal output; pane read supports visible, recent, or recent-unwrapped
herdr pane read <pane-id> --source recent-unwrapped --lines 200
```

Never use `--source detection` with `herdr pane read`.

## Integrate and Verify

Use one integration owner. Integrate commits in dependency order into a clean integration branch. During convergence, allow one writer per conflicting surface and use other agents for read-only diagnosis or review.

Run validation commands in a shell or Herdr pane whose `cwd` is the target worktree. Use `git -C <worktree> ...` only for Git subcommands; never place a package, test, build, or deployment command after `git -C`.

Apply four gates:

1. Task: focused acceptance, tests, lint, and type checks.
2. Integration: merged build and affected suites.
3. Product: real API/browser user journeys and negative paths.
4. Operational: migrations, configuration, observability, staging health, and rollback readiness.

Give an independent verifier the integrated artifact and acceptance contract, not the builder's conclusions. A builder may repair findings; it may not self-certify the gate.

## Retire Completed Teams

After root records a durable integration disposition, move team resources through `active -> retirement-pending -> retired`, `retained-for-recovery`, or `retirement-failed`. Preserve unique work and recovery commits first. Inventory, stop, close, remove, and verify only run-owned resources as specified in `references/team-operations.md`. Perform a final global sweep.

## Release and Finish

Keep production deployment, destructive migrations, secrets/permissions, material spending, and acceptance of security or data-loss risk behind explicit human gates unless the user has already granted that exact authority.

Declare success only from observed evidence. Complete `assets/final-report.md` with outcome, fan-out, models, evidence, incidents, retirement, residual risk, and authoritative token/context telemetry. Mark unavailable usage as unavailable with `null` values; never estimate it. Cleanup is part of completion unless the user explicitly asks to retain run resources.

## Red Flags

- Agent count chosen before task decomposition
- Delivery level, constraints, tradeoffs, or weekly usage budget omitted
- Speculative architecture, agents, skills, dependencies, or tools without a decision-changing need
- Agent launched without a recorded specialist, model, effort, parent, and access mode
- Worker delegates, or a lead exceeds its recorded delegation budget
- Lead launches children without a team contract or outside team ownership
- Lead installs globally, skips skill vetting, or launches children before the repo-local capability commit is visible
- Greenfield worktrees are attempted before a root-owned bootstrap commit exists
- Lead invokes skill discovery without loading the exact recorded `find-skills` SKILL.md
- Child starts before loading its exact required skills
- Tool assigned without a distinct evidence question or available connection
- Incident invented to satisfy a report template
- `gpt-5.4-mini` assigned writes or used before a real inference succeeds
- Several writers in one checkout or overlapping ownership
- Builders started before the product/interface contract is frozen
- Chat used as the only ledger
- `done`, `idle`, or `unknown` treated as acceptance
- Integration delegated without one accountable owner
- Production deployed because a command exited zero, without health and rollback checks
- Run declared complete before resource retirement and the final workflow report
- A Herdr flag used on a different command surface, or a non-Git command placed after `git -C`

Stop and reconcile whenever one appears.
