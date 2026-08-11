# Operating Contract

Read this reference for multi-wave builds, restart recovery, and release work.

## Run invariants

- The coordinator owns the product contract, dependency graph, ledger, integration order, and release decision.
- Each writable surface has one current owner.
- Every task has a base revision, isolated branch/worktree, acceptance evidence, and bounded retry count.
- Herdr controls processes; Git and artifacts preserve work; tests establish correctness.
- No coding agent receives broader production authority than its task requires.
- The specialist roster, model, reasoning effort, parent, access mode, fallback, and delegation budget are recorded before dispatch.
- Root delegates to leads, leads may delegate only bounded workers, and workers never delegate.

## Task states

Use `planned`, `ready`, `working`, `blocked`, `reported`, `verifying`, `accepted`, `integrated`, `failed`, or `cancelled`. Track team resource state separately as `active`, `retirement-pending`, `retired`, `retained-for-recovery`, or `retirement-failed`. Herdr lifecycle state is recorded separately because it establishes neither task acceptance nor resource retirement.

Transition `reported -> accepted` only after the coordinator or independent verifier confirms the deliverable and acceptance evidence. Transition `accepted -> integrated` only after the integration branch passes its gate.

## Coordinator reconciliation loop

1. Load run state and compare its base revision and worktrees with live Git state.
2. Inventory Herdr agents and panes by returned IDs and unique names.
3. Match each live agent to a task; mark unmatched processes for inspection, not deletion.
4. Verify claimed commits exist and belong to the recorded branch/worktree.
5. Re-run or inspect recorded acceptance commands.
6. Record contradictions explicitly and resolve from Git/artifact/test evidence.
7. Dispatch only dependency-ready work within safe capacity.

Execute non-Git checks from the worktree directory, preferably through `herdr pane run` on a pane created with that `cwd`. Keep `git -C` limited to Git operations. Confirm every Herdr flag on the current command group. Use `herdr agent read <agent> --source detection` for the detection snapshot. Use `herdr pane read <pane> --source recent-unwrapped` for raw terminal output; never pass `detection` to `pane read`.

After restart, never depend on remembered chat. If an assignment cannot be reconstructed, pause that writer, inspect its diff and transcript, then create or repair its task contract before continuing.

## Prompt contract

Every writer prompt must state:

- Objective and user-visible outcome
- Dependencies and pinned base revision
- Owned and forbidden paths
- Interfaces/invariants that must remain stable
- Required implementation and acceptance evidence
- Commit/artifact and handoff format
- Non-goals
- Conditions requiring coordinator input
- Specialist ID, model/effort, parent lead, and delegation prohibition or budget

Every verifier prompt must state the acceptance contract, integrated revision, allowed inspection commands, prohibition on implementation edits, and required evidence format.

## Failure routing

| Evidence | Route |
|---|---|
| Focused task test fails | Return exact evidence to the task owner |
| Cross-task contract mismatch | Integration owner coordinates the repair |
| Product semantics unresolved | Coordinator or human product gate |
| Destructive/irreversible choice | Human approval gate |
| Agent lifecycle is `unknown` | Inspect transcript, process, Git, and artifacts |
| Agent repeats the same failure twice | Redesign boundary or replace approach/agent |
| Reviewer stalls but evidence is available | Run deterministic checks directly; report review gap |

## Release evidence

Require the exact artifact/revision, migration result, configuration target, staging or preview checks, authenticated and unauthenticated smoke paths, telemetry/health observation, and tested rollback target. A successful deploy command alone is insufficient.

## Cleanup

Retire each completed team after its integration disposition is durable, then perform a final global sweep. Inventory resources created by the run. Close only owned agents, panes, worktrees, servers, and temporary infrastructure. Preserve branches or commits needed for recovery. Verify listeners and external resources rather than assuming termination succeeded. Finish with `assets/final-report.md`.
