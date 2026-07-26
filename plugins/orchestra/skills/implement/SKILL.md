---
name: implement
description: Deliver one feature end-to-end through an opinionated pipeline — a failing test first, execution evidence, adversarial falsification, integration, and one full gate run — with a capped fix loop before escalating to the human.
---

# implement

Shape: pipeline

You are the ROOT ORCHESTRATOR for this run. Do not implement inline: your job
is to run one feature through a fixed sequence of lanes — build behind a
failing test, gather execution evidence, falsify the result, integrate, and
gate once — never to write the change yourself. implement is the canonical
composite workflow other skills point to when someone asks for the default
way to ship a feature.

implement does not decompose a body of work into a partition of generic
lanes; it imposes one fixed pipeline on one feature. Discriminator against
`fan-out`: `fan-out` takes a partition that already exists and dispatches
whatever roles the decomposition calls for; `implement` takes a single
feature and always runs the same builder-prover-adversary-gate sequence,
regardless of what the feature is. A request to ship several independent
features concurrently is a `fan-out` run with one `implement` lane per
feature, not a single wider implement run.

## Required inputs

implement fails closed. It requires a feature stated as a checkable
deliverable — what changes, for whom, and how a reader who did not write the
change can tell it is done — plus acceptance criteria specific enough that a
single `builder` lane's paths can be declared without further decomposition.
If the feature actually spans multiple surfaces that need independent,
concurrently-writable path ownership, that is a partition, not a single
feature; stop and name `fan-out` as the workflow that should own the split,
with one `implement` lane per partition unit.

If the feature is not yet decided — the request is "figure out what to
build" rather than "here is what to build" — stop and name the prerequisite:
run `plan` (or `design` for an interface-shape question) first, then return
with its output as this run's required input.

implement also requires a captured baseline — `git status` and `git diff`
before the first lane dispatches — so a failed lane's edits can be
quarantined against a known-clean state. See `../../references/run-ledger.md`.

## Lane plan

The pipeline is a strict sequential chain; each lane depends on exactly the
lane before it, and no two lanes in this plan run concurrently.

| Lane | Role | Tier | Access | Owns | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `build` | `builder` | standard | write | the feature's declared paths | first stored artifact is a failing test with raw output, then the smallest passing implementation with raw output, diff confined to declared paths (G1) |
| `prove` (depends on `build`) | `prover` | standard | execute | none | the feature's full claim — not just the new test — executed with raw output stored and an explicit pass/fail per claim |
| `falsify` (depends on `prove`) | `adversary` | standard by default, escalate to `deep` only on a declared trigger (see `../../roles/adversary.md`) | read_only | none | every finding names a reachable precondition and points at stored evidence; a concern with no path to reach it goes in a labeled speculation list |
| `integration-gate` (depends on `falsify`) | `prover` | standard | execute | none | full repository gate exits clean, raw output stored; the only run counting toward G9 |

`falsify` reads `build`'s diff and `prove`'s stored output — its deliverables,
never their reasoning — from a context that never saw the authoring work, so
its independence holds even though the chain is sequential rather than
parallel.

## Delegation contract

You dispatch at depth one. Maximum delegation depth is two, and `mechanic` is
the only role dispatchable at depth two: `build` may hand a repetitive edit
it has already specified to a `mechanic` confined to its own declared paths
(see `../../roles/mechanic.md`); no other lane delegates, and `mechanic`
never delegates further.

On a host that cannot dispatch parallel subagents, implement degrades to a
sequential fresh-context role-pass: the same four lanes, in the same order,
each in a fresh context, never merged into one worker and never skipped.
`falsify` in particular must still get a context that never saw `build`'s or
`prove`'s reasoning, only their stored deliverables — a degraded host that
cannot provide even that isolation records `isolation: degraded` in
`run.json` per `../../references/hosts.md` and treats `falsify`'s output as
`unverified` rather than a clean pass.

## Quality gates

G1 is checked on `build` alone: its first stored artifact must be the failing
test, not the passing one. G2 applies to every lane — a claimed pass with no
stored raw output is a failure of that lane. G3 governs `falsify`'s
isolation. G4 triggers automatically when the integrated diff touches auth or
authz, payments, secrets, deserialization, file upload, or shell, SQL, or
template construction, regardless of whether the feature description
mentioned security — check the diff, not the stated intent. G6 caps
delegation depth as above. G9 is the deciding gate: `build` passing its own
test and `prove` confirming it are not a green whole until
`integration-gate` runs once, after `falsify`, and its output is the record
that counts. Full definitions: `../../references/gates.md`.

## Evidence and completion

Evidence, not assertions: every lane's `verified` status requires at least
one evidence entry pointing at stored raw output under
`.orchestra/<run>/<nn>-implement/evidence/`. `build`'s failing-then-passing
pair, `prove`'s claim-by-claim output, `falsify`'s findings evidence, and
`integration-gate`'s final run together are the run's completion evidence — a
`verified` status on any one of them with no evidence entry recorded is a
failure of that lane, not a formality to backfill later.

## Hard stops

HARD STOP before every irreversible or outward-facing action, and never take
one inside a lane: a lane that reaches a stop condition returns `blocked`
with an escalation naming what would unblock it, and you own the decision.
Widening `build`'s declared paths past what was dispatched, exceeding
delegation depth two, and overwriting a file no lane declared are stops in
their own right, mid-pipeline or not. A fourth reopen of the same lane (see
Failure and recovery) is also a stop, not another retry. Record every stop
request in `stops.md` before making it. See `../../references/stops.md`.

## Deterministic outputs

An implement run writes `run.json` (resolved host, capabilities, tier
mapping, delegation depth, `reopenCount`), `baseline.md` (the pre-dispatch
`git status` and `git diff`), `decomposition.md` (the feature statement and
the pipeline as dispatched), one `lanes/<lane-id>.md` per lane holding its
brief and normalized result verbatim, `evidence/<nn>-<label>.txt` per stored
artifact including the failing test, the passing test, `prove`'s output, and
`integration-gate`'s raw output, `stops.md` for every hard-stop request and
its answer, and `handoff.md` stating what is verified with evidence pointers,
what is open, and the next dispatchable lane. `findings.md` is written only
if `falsify` raised any; `verdicts.md` is written only if a verdict was
requested directly — implement itself renders neither by default. Full
layout: `../../references/run-ledger.md`.

## Failure and recovery

A `blocked` or `partial` result from any lane halts the chain: do not
dispatch the next lane past an unresolved one, and do not substitute your own
judgment for a missing deliverable. Quarantine is bounded by the pre-dispatch
baseline — revert `build`'s edits only for paths it exclusively owned and
that were clean at baseline; anything else is a hard stop, not an automatic
revert.

Redispatch a fixed lane at most three times (`reopenCount` in `run.json`); a
fourth failure on the same lane is itself an escalation to the human rather
than another retry. When `falsify` raises a finding, reopen `build` with the
finding as input, then rerun `prove` and `falsify` after the fix lands — do
not rerun only `build` and assume the downstream lanes still hold. If
`integration-gate` fails after every upstream lane reported `verified`, scope
the fix to whichever lane's deliverable the gate output implicates and rerun
the gate once after that fix lands.
