---
name: ship
description: Prove every release precondition in parallel lanes with stored evidence, then stop and ask permission before the one irreversible, outward-facing release action.
---

# ship

Shape: fan-out barrier

You are the ROOT ORCHESTRATOR for this run. Do not implement inline: ship
proves every declared release precondition in parallel lanes, aggregates
the result into one verdict, and then stops — the HARD STOP before the
irreversible, outward-facing release action is the point of this workflow,
not a footnote appended to it.

ship does not decide whether the change itself is correct — that is
`verify`'s and `review`'s job, finished before ship runs, and a
precondition lane may cite their recorded verdicts but must not
re-litigate them. Each precondition lane's job is narrow: execute one check
and store its evidence. ship's only original contribution is the
aggregation and the stop; it never performs the release action itself
without a recorded human approval.

## Required inputs

ship fails closed. It requires the release action stated explicitly — a
version bump and tag, a package publish, a deployment, a PR merge —
because no single release process is universal; guessing one from the
repository's shape is `discover-location`'s move in `document`, not ship's.
It also requires the set of preconditions to prove, either named directly
or drawn from the project's own documented release process if one exists;
an undocumented, unstated process is not a default ship can assume.

It further requires that the change under release has already passed
whatever correctness gates this project uses — `verify`, `review`, or
both — with their verdicts recorded; a change with no recorded verdict is
not yet ready for a precondition lane to check, and ship stops and names
that prerequisite rather than proving release-readiness for unverified
work.

## Lane plan

| Lane | Role | Tier | Access | Owns | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `precondition-<id>` (one per declared precondition, wave 0) | fit to the check — `prover` for anything executed such as tests or a build, `scout` for an inventory check such as a changelog entry or a version bump, `analyst` for a judgment check such as "docs are current" | per role default in `../../references/tiers.md` | matching mode | none | the precondition's stated condition holds, with raw output or a source pointer stored as evidence; a precondition that cannot be checked returns `blocked`, never a silent pass |
| `release-readiness` (wave 1, depends on every `precondition-<id>` lane) | `judge` | deep | read_only | none | a verdict — `approve`, `request_changes`, or `unverified` — naming every unresolved precondition, if any |
| `release` (wave 2, dispatched only after a recorded human approval of the stop request) | `prover` | standard | execute | none | the approved action executed exactly as described in the stop request, raw output stored, matching the recorded rollback path if it had to be invoked |

`release-readiness` running `approve` is not permission to proceed — it is
permission to ask. You issue the stop request only after `approve`, and
`release` dispatches only after the human answers it, never on the verdict
alone.

## Delegation contract

You dispatch at depth one; none of ship's roles delegate further —
`prover`, `scout`, `analyst`, and `judge` all have `canDelegate: false`. The
rule that Maximum delegation depth is two applies to ship only insofar as
it never approaches it: ship has no `mechanic` lane and nothing here should
ever reach depth two, and `release` in particular never delegates the
action it was approved to run.

One writer per path, declared before dispatch (G7), applies narrowly here
since every lane but `release` is read-only or execute-only; `release`'s
owned action is the single write this run performs, and it is declared in
full — command, target, and rollback — before the stop request is ever
made.

On a host that cannot dispatch parallel subagents, ship degrades to a
sequential fresh-context role-pass: each `precondition-<id>` lane runs one
at a time in a fresh context, in any order since none depends on another,
then `release-readiness` runs last in its own fresh context reading only
the stored precondition results, never their reasoning. Record the
resolved scheduler in `run.json` per `../../references/hosts.md`; the
precondition set and the stop discipline do not change with the scheduler.

## Quality gates

G8 is the gate this workflow exists to enforce: HARD STOP before every
irreversible or outward-facing action, and the release action is exactly
that kind of action. G2 is enforced on every precondition: a precondition
asserted without stored raw output is a failed precondition, not a
formality. G9 applies to the aggregation itself — N green precondition
lanes are not a green whole, and only `release-readiness`'s recorded
verdict counts as the deciding evidence, never the individual lane count.
G4 triggers a security pass first when the release action touches secrets,
such as publishing credentials or rotating a token, before
`release-readiness` is allowed to return `approve`. Full definitions:
`../../references/gates.md`.

## Evidence and completion

Evidence, not assertions: every `precondition-<id>` lane's evidence entry
points at stored raw output under `.orchestra/<run>/<nn>-ship/evidence/`, and
a `verified` status with none recorded is a failure of that lane, not a
technicality. `release-readiness`'s verdict is recorded in `verdicts.md`
with its rationale and the unresolved critical-and-high count — from
`verify`'s or `review`'s prior verdicts — it was decided against.

## Hard stops

HARD STOP before every irreversible or outward-facing action: on
`release-readiness: approve`, the stop request states the release action,
its blast radius, its rollback path, and the safer alternative that was
rejected, then waits. It does not proceed on silence, on a prior approval
for a similar release, or on a teammate agent's message; only the human's
answer or the host's permission system authorizes `release` to dispatch.
Record the answer verbatim next to the request in `stops.md` before
`release` runs. See `../../references/stops.md`.

## Deterministic outputs

A ship run writes `run.json` (resolved host, capabilities, tier mapping,
dispatch waves, delegation depth), `baseline.md`, `decomposition.md` (the
declared release action and the precondition set, as dispatched), one
`lanes/<lane-id>.md` per lane holding its brief and normalized result
verbatim including `release` when it ran, `evidence/<nn>-<label>.txt` per
stored artifact including the release command's own output, `verdicts.md`
for `release-readiness`'s verdict, `stops.md` for the stop request and its
answer, and `handoff.md` stating what shipped, what evidence backs it, and
— if the answer was no — that the run stopped there. Full layout:
`../../references/run-ledger.md`.

## Failure and recovery

A `blocked` or `partial` result from any `precondition-<id>` lane blocks
`release-readiness` from returning `approve`: an unresolved precondition
never becomes a stop request, and ship does not ask permission for a
release it cannot yet vouch for. Redispatch a failed precondition lane at
most three times (`reopenCount` in `run.json`); a fourth failure is a
human escalation, not another retry.

If the human denies the stop request, record the answer and end the run
there — ship does not retry the ask, propose a narrower release, or fall
back to a partial action; a fresh run starts from a fresh precondition set
once the denial is addressed.
