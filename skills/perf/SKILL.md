---
name: perf
description: Improve measured performance in repeated rounds against one fixed harness and workload, comparing before/after numbers from that same harness, until a round fails to clear a threshold declared before the loop starts.
---

# perf

Shape: loop-until-dry

You are the ROOT ORCHESTRATOR for this run. Do not implement inline: perf
loops rounds of measure, optimize, and remeasure against one fixed harness
and one fixed workload, comparing before/after numbers produced by that same
harness, until a round fails to clear a threshold declared before the first
round runs. It reports the trend across rounds, not a single number picked
after the fact.

perf's definition of green is different from every other workflow here:
evidence is a measured delta between two comparable numbers, not a passing
test. A measurement taken with a changed harness, a different workload, or a
different machine is not evidence and must be discarded, not reported as a
data point. perf does not decide what correct behavior is either — the
existing test suite is the correctness backstop every round must keep green,
and a round that trades correctness for speed is a stop, not a result to
accept and move past.

## Required inputs

perf fails closed. It requires a fixed workload — concrete inputs, scale, and
repetition count that do not change across rounds — and an existing
measurement harness that runs that workload and emits a comparable number. If
no harness exists, stop and name the prerequisite: build one first, as a
`spike` or as part of `implement`, because inventing a harness mid-loop makes
every prior round's number incomparable to every later one.

It also requires a diminishing-returns threshold declared and recorded before
round 0 runs — for example, "stop when a round improves the primary metric by
less than 3%" — so that "no further win" is never decided after the fact once
results are already in hand. It requires the current passing test suite as
the correctness backstop for every round.

perf also requires a captured baseline — `git status` and `git diff` before
the first lane dispatches — plus round 0's harness number, stored before any
optimization begins. See `../../references/run-ledger.md`.

## Lane plan

Rounds repeat until a `measure-round` delta falls below the declared
threshold; only then does `integration-gate` run.

| Lane | Role | Tier | Access | Owns | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `measure-baseline` (round 0) | `prover` | standard | execute | none | the harness runs against the declared workload unmodified; raw numeric output stored as round 0's number, with the exact command and exit code recorded |
| `optimize` (round N, depends on `measure-round` N-1) | `builder` | standard | write | the declared implementation paths | the existing test suite still passes unchanged; diff confined to declared paths |
| `measure-round` (round N, depends on `optimize` round N) | `prover` | standard | execute | none | the harness reruns with the byte-identical command used for round 0; raw output stored; the delta against the previous round's number is computed and stored alongside it |
| `integration-gate` (after the loop exits dry) | `prover` | standard | execute | none | full repository gate exits clean, raw output stored; the only run counting toward G9 |

A round is dry when `measure-round`'s delta falls below the declared
threshold; that round's `optimize` lane is the last one dispatched, and no
further round starts.

## Delegation contract

You dispatch at depth one. Maximum delegation depth is two, and `mechanic` is
the only role dispatchable at depth two: an `optimize` lane may hand an
already-specified repetitive edit to a `mechanic` confined to its own
declared paths (see `../../roles/mechanic.md`); no other lane delegates, and
`mechanic` never delegates further.

On a host that cannot dispatch parallel subagents, perf degrades to a
sequential fresh-context role-pass: each round's `optimize` and
`measure-round` still run one at a time, each in a fresh context, never
merged and never skipped. A round's `measure-round` lane reads the previous
round's stored number, never the optimizing lane's reasoning about why it
made the change it made — that separation is what keeps a round's number an
independent measurement rather than a restatement of the builder's claim.

## Quality gates

perf's defining gate is a redefinition of what counts as evidence: a
before/after pair from the same harness, same workload, same command line,
not a passing test. G1 does not apply to `optimize` in its usual shape —
there is no new failing test to write first, because the behavior is not
new; the correctness backstop is the existing suite staying green through
every round instead. G2 applies to every measurement and every lane: a
reported delta with no stored raw output is a failure, not a warning. G4
triggers automatically when a round's diff touches auth or authz, payments,
secrets, deserialization, file upload, or shell, SQL, or template
construction. G6 caps delegation depth as above. G9 is decided by
`integration-gate`'s single run over the final state, not by any individual
round's number. Full definitions: `../../references/gates.md`.

## Evidence and completion

Evidence, not assertions: every round's number is stored raw under
`.orchestra/<run>/<nn>-perf/evidence/`, and the round-over-round deltas — not
a single "looks fast enough" from the optimizing lane — are what ends the
loop. A round is dry only when a stored delta falls below the declared
threshold; an optimizing lane's own opinion that further gains are unlikely
does not end the loop on its own. Round 0's number, every intermediate
round's number, and
`integration-gate`'s final run together are the completion evidence, so a
reader sees the whole trend, not just the last data point.

## Hard stops

HARD STOP before every irreversible or outward-facing action, and never take
one inside a lane. An `optimize` round that breaks the existing test suite,
or one whose diff exceeds its declared paths, is a stop, not a round to
accept and iterate past. Changing the harness or the workload mid-loop is a
stop as well: it invalidates every prior round's number and requires
restarting the loop at round 0, which is a decision for the human, not
something the loop resolves on its own. Record every stop request in
`stops.md` before making it. See `../../references/stops.md`.

## Deterministic outputs

A perf run writes `run.json` (resolved host, the declared threshold, the
workload and harness command, round count, `reopenCount`), `baseline.md` (the
pre-dispatch `git status` and `git diff`, plus round 0's number),
`decomposition.md` (the loop plan and threshold as declared before dispatch),
one `lanes/<lane-id>.md` per round including `measure-baseline` and
`integration-gate`, `evidence/<nn>-<label>.txt` for every stored measurement,
never overwritten across rounds, `stops.md` for every hard-stop request and
its answer, and `handoff.md` stating the current round, the latest numbers,
whether the loop is dry, and the next dispatchable round if it is not.
`findings.md` and `verdicts.md` are written only if a lane in the loop
produced one; perf itself renders neither. Full layout:
`../../references/run-ledger.md`.

## Failure and recovery

Redispatch a failed round capped at three reopens (`reopenCount` in
`run.json`); a fourth failure on the same round escalates to the human rather
than another retry. If `measure-round`'s number regresses against the
previous round — gets measurably worse, not merely fails to improve — revert
that round's `optimize` edits, bounded by the pre-dispatch baseline and only
within its declared paths, and treat the regression itself as that round's
stopping signal rather than averaging it away or discarding it as noise. If
`integration-gate` fails after the loop exited dry, scope the fix to the
final round's `optimize` lane and rerun the gate once after the fix lands.
