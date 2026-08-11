# Team Operations

Read this reference before delegating through a lead, retiring team resources, or closing a run.

## Contents

1. Default topology
2. Lead delegation
3. Team reporting
4. Integration and retirement
5. Workflow accounting

## Default topology

Use a root integration checkout plus isolated worktrees for concurrent writers:

```text
root coordinator / integration checkout
├── team lead worktree, when the lead writes
│   ├── read-only worker panes may share this checkout
│   └── each concurrent child writer gets another worktree
└── quality lead, independent of builder teams
```

Record Herdr workspace, tab, pane, worktree, branch, team, task, and parent IDs. Group the run logically through those records and consistent labels; do not force one visual layout when the task is smaller.

## Lead delegation

Root activates only teams required by the dependency graph. Give every lead a copied `assets/team-contract.yaml`, delivery profile, and capability ledger before it launches children.

A lead must:

1. Accept one subsystem outcome and frozen interfaces from root.
2. Decide whether to implement directly or delegate independent tasks.
3. Create one child task contract per delegation.
4. Load the exact `find-skills` SKILL.md recorded in the lead contract, record loading evidence, then inspect existing skills and discover, vet, install, and commit only approved repo-local capability gaps.
5. Assign only approved specialists/models/skills/tools within its budget.
6. Create child writer worktrees from the capability commit.
7. Monitor Herdr lifecycle while verifying Git/artifact/test evidence separately.
8. Resolve ordinary child questions, retries, and subsystem integration.
9. Escalate cross-team, authority, destructive, security, data-loss, or repeated-failure decisions.
10. Send checkpoint, incident, and final-handoff events using `assets/team-report.md`.
11. Retire child resources after the integration disposition is durable.

Workers never delegate. Leads never create other leads or grant production authority. Root may audit any child but normally coordinates through the lead.

Prefer a coordinating lead for multi-worker teams. A lead may implement bounded integration glue; avoid assigning it a large feature while it manages several active children.

## Team reporting

Write every report to a unique run-owned path and notify root through Herdr. Root reconciles the report into the single-writer global ledger.

- Send a `CHECKPOINT` after decomposition and before subsystem integration, and whenever scope, ownership, or risk materially changes.
- Send an `INCIDENT` immediately for an actual disruptive event. Never invent an incident to fill a template.
- Send a `FINAL_HANDOFF` after subsystem integration evidence is ready.

Include adopted, rejected, and unresolved child claims. Summarize evidence; do not forward raw transcripts as the decision record.

## Integration and retirement

Track resource state separately from task and Herdr lifecycle state:

```text
active -> retirement-pending -> retired
                            \-> retained-for-recovery
                            \-> retirement-failed
```

Begin retirement only after:

- Commit or artifact is durable and reachable.
- Handoffs and verification evidence are recorded.
- Root records the integration disposition: accepted, rejected, superseded, or retained.
- No unique uncommitted work or artifact remains.
- A recovery branch/commit is preserved when needed.

Then:

1. Inventory run-owned agents, panes, worktrees, processes, listeners, and temporary infrastructure.
2. Stop run-owned processes and agents.
3. Close only run-owned panes/tabs/workspaces.
4. Remove eligible worktrees using the current `herdr worktree` syntax; do not force removal over unpreserved work.
5. Verify registrations, processes, listeners, and paths are absent.
6. Record each action, result, retained resource, failure, and timestamp.

Do not delete unmatched or user-owned resources. Perform a final global sweep after all team-level retirements.

## Workflow accounting

Generate the root report from ledger evidence using `assets/final-report.md`. Include teams activated, agents spawned, leads/workers, waves, peak concurrency when observed, models/efforts, fallbacks, retries, incidents, commits, gates, and retirement results.

Record token/context accounting only from authoritative runtime/provider telemetry:

- `available`: every relevant agent has observed data.
- `partial`: some agents have observed data; identify missing agents.
- `unavailable`: no authoritative data is exposed.

Use `null`, not `0`, for unavailable numeric values. State the source and exact limitation. Never estimate tokens from transcript length or confuse model context capacity, quota remaining, or lifecycle metadata with consumed context.
