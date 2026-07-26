---
name: fan-out
description: Partition a known body of work into independent lanes, dispatch them concurrently behind a barrier, integrate the results, and run the full quality gate exactly once.
---

# fan-out

Shape: fan-out barrier

You are the ROOT ORCHESTRATOR for this run. Do not implement inline: your role
is to decompose a known body of work into independent lanes, dispatch them
concurrently, hold a barrier until every lane returns, integrate the results,
and run the full quality gate exactly once. fan-out is the raw primitive other
workflows cite for barrier discipline — cite it wherever a workflow needs to
run independent lanes and merge them safely, rather than re-deriving barrier
semantics locally.

fan-out does not decompose an unclear goal into a partition; it consumes a
partition that already exists (see Required inputs). It does not own
falsification of a claim either — that is `verify`'s job, and a fan-out run
that wants an adversarial pass over its integrated result dispatches `verify`
as a lane or as the workflow that follows it, rather than reimplementing the
reverse-check here. fan-out's only job is the partition, the barrier, and the
one gate run that counts.

## Required inputs

fan-out fails closed. It requires a partition that is already decided: a set
of lane boundaries with, for every lane, a role, a tier, an access mode, the
paths it owns (or none), its inputs, exactly one deliverable, and acceptance a
reader other than the lane can check. This is normally the deliverable of an
`architect` or `analyst` lane recorded in `decomposition.md`, or the output of
a planning workflow such as `plan` or `design`.

If no partition exists — if the request is "figure out how to split this up"
rather than "here is the split, go" — fan-out stops and names the
prerequisite: run `plan` (or `design` for an interface-shape question) first,
then return with its decomposition. Guessing a partition here would hide the
decomposition step from the run ledger and make the resulting lane plan
unreviewable before dispatch.

fan-out also requires a captured baseline — `git status` and `git diff` before
any lane starts — so a failed lane's edits can be quarantined against a
known-clean state rather than an assumed one. See
`../../references/run-ledger.md`.

## Lane plan

Every lane in the plan carries a stable id, one role, one tier, one access
mode, and acceptance a reader other than the lane can check; a lane without
acceptance is not dispatchable (see `../../references/lanes.md`). fan-out is
generic — the roles below are whatever the decomposition calls for, not a
fixed pipeline — but the shape of the wave is fixed: every partition lane runs
in wave 0, the barrier holds until all of them return, and exactly one gate
lane runs in wave 1 after integration.

| Lane | Role | Tier | Access | Owns | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `lane-<id>` (one per partition unit, wave 0) | fit to the work — `scout`, `analyst`, `builder`, or `prover`, per `../../references/tiers.md` | per role default in `../../references/tiers.md` | `read_only`, `write`, or `execute`, matching the role | for `write` lanes, a path set disjoint from every other lane in the wave; none for `read_only` or `execute` | a condition stated in the decomposition that a reader can check against the lane's own deliverable, without reading its reasoning |
| `post-integration-gate` (wave 1, depends on every wave-0 lane) | `prover` | standard | execute | none | the full repository gate exits clean and its raw output is stored; this is the only gate run that counts toward G9 |

Declare every `write` lane's owned paths before dispatch, never after, and
confirm no two lanes in wave 0 own an intersecting path — that check is what
makes the wave safe to run concurrently rather than a hope that nothing
collides.

## Delegation contract

You dispatch at depth one. Maximum delegation depth is two, and `mechanic` is
the only role a lane may legally dispatch at depth two — a `write` lane with a
repetitive edit it has already specified may hand it to a `mechanic` confined
to a subset of its own owned paths (see `../../roles/mechanic.md`); no lane
may dispatch any other role, and a `mechanic` never delegates further.

One writer per path, declared before dispatch (G7): wave 0's disjointness
check is this rule applied to a single wave, and it is what lets every wave-0
lane run without coordinating with the others mid-flight.

On a host that cannot dispatch parallel subagents, fan-out degrades to a
sequential fresh-context role-pass: the same lanes, in the same order implied
by their dependencies, run one at a time in a fresh context each, never fewer
of them and never merged into one worker. A later lane in the pass reads an
earlier lane's deliverable file, never its reasoning — that constraint is what
keeps the degraded run's lanes as independent as the parallel version's.
Record the resolved scheduler in `run.json` per `../../references/hosts.md`;
the lane plan and the acceptance conditions do not change with the scheduler.

## Quality gates

G9 is the gate this workflow exists to enforce: N green wave-0 lanes are not a
green whole. Do not treat a wave where every lane returned `verified` as done
— integrate first, then run `post-integration-gate` exactly once, and only
that run's output counts as the completion evidence. A rerun after a fix
replaces the prior gate record; it does not sit alongside it.

G5 and G7 are checked mechanically against the declared paths from the lane
plan: a lane whose diff exceeds its declared paths, or whose paths turned out
to intersect another lane's, fails regardless of the quality of its change.
G6 caps delegation depth as described above. If any wave-0 lane is a
`builder`, G1 applies to it individually — its first stored artifact is a
failing test, before any implementation exists. G4 triggers a security pass
automatically when the integrated diff touches auth or authz, payments,
secrets, deserialization, file upload, or shell, SQL, or template
construction, regardless of whether any lane declared security work; check
the integrated diff for this, not each lane's stated intent. Full
definitions: `../../references/gates.md`.

## Evidence and completion

Evidence, not assertions: every lane's `verified` status requires at least
one evidence entry pointing at stored raw output under
`.orchestra/<run>/<nn>-fan-out/evidence/`, never a paraphrase of what ran.
`post-integration-gate`'s output is the run's completion evidence and is
stored the same way. A `verified` status with no evidence entry recorded
against it is a failure of that lane, not a formality to fix later.

## Hard stops

HARD STOP before every irreversible or outward-facing action, and never take
one inside a lane: a lane that reaches a stop condition returns `blocked`
with an escalation naming what would unblock it, and you — the root — own the
decision, not the lane. Widening a lane's declared paths past what was
dispatched, exceeding delegation depth two, and overwriting a file no lane
declared are stops in their own right, even mid-barrier. Record every stop
request in `stops.md` before making it, so an abandoned run still shows what
it was about to do. See `../../references/stops.md`.

## Deterministic outputs

A fan-out run writes `run.json` (resolved host, capabilities, tier mapping,
dispatch waves, hoisted lanes, delegation depth), `baseline.md` (the
pre-dispatch `git status` and `git diff`), `decomposition.md` (the lane plan
as dispatched, not a later summary), one `lanes/<lane-id>.md` per lane holding
its brief and normalized result verbatim, `evidence/<nn>-<label>.txt` per
stored artifact including the post-integration gate's raw output, `stops.md`
for every hard-stop request and its answer, and `handoff.md` stating what is
verified with evidence pointers, what is open, and the next dispatchable
lane. `findings.md` and `verdicts.md` are written only if a lane in the plan
produced findings or a verdict; fan-out itself renders neither. Full layout:
`../../references/run-ledger.md`.

## Failure and recovery

A wave-0 lane that returns `blocked` or `partial` breaks the barrier: do not
proceed to integration with an unresolved lane, and do not substitute your
own judgment for the missing deliverable. Quarantine is bounded by the
baseline captured before dispatch — revert a failed lane's edits only for
paths that lane exclusively owned and that were clean at baseline; a path
outside its ownership, or one already dirty before dispatch, is a hard stop,
not an automatic revert.

Redispatch a fixed lane at most three times (`reopenCount` in `run.json`); a
fourth failure on the same lane is itself an escalation to the human, not
another retry. If `post-integration-gate` fails after every wave-0 lane
reported `verified`, the fix is scoped to the integration itself — reopen the
specific lane whose deliverable the gate output implicates, not the whole
wave, and rerun the gate once after the fix lands.
