---
name: cover
description: Sweep a declared target for untested code paths, fan out to author the missing tests, then deliberately break the covered code to prove each new test actually fails — a test that still passes against broken code is rejected.
---

# cover

Shape: sweep

You are the ROOT ORCHESTRATOR for this run. Do not implement inline: cover
sweeps a declared target for code paths with no test reaching them, dispatches
one lane per gap to author the missing test, and then runs a mutation check
per gap — deliberately break the code the new test claims to cover and
confirm the test fails against the break, then confirm it passes again once
the break is reverted.

The mutation check is the entire reason this is not `implement` wearing a
test flavor. A new test that only ever ran green proves nothing: it may be
checking the wrong thing, or nothing at all. cover is not satisfied by a
passing new test alone, and a mutate lane whose deliberate break does not
make the test fail is a failure of that lane, not a clean result. cover also
does not decide whether the *existing* suite is still trustworthy — that
reverse-check across already-written tests is `verify`'s job; cover only
authors and mutation-tests the specific tests it adds for the gaps it found.

## Required inputs

cover fails closed. It requires a declared target — a set of paths, a
module, or a diff to sweep — sweeping an unbounded "the whole repository" is
not dispatchable; name a scope. It requires a way to measure coverage,
whether existing tooling or a documented manual method, so the gap list is a
checkable claim rather than a guess; if neither exists for the target, stop
and name the prerequisite: establish a coverage baseline first, as a `spike`
or a `plan` item, then return with the gap list.

It also requires the target to build and its existing tests to pass cleanly
before the sweep starts, so a later mutation's failure can be attributed to
the deliberate break rather than a preexisting defect — capture that clean
state as the baseline, along with `git status` and `git diff` before the
first lane dispatches. See `../../references/run-ledger.md`.

## Lane plan

| Lane | Role | Tier | Access | Owns | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `sweep` (wave 0) | `scout` | fast | read_only | none | a gap list naming, per untested path, the specific behavior no test reaches and the file-and-line evidence for the claim; the deliverable every later lane reads |
| `author-<gap-id>` (wave 1, one per gap, depends on `sweep`) | `builder` | standard | write | the new test file(s) for that gap only, disjoint from every other author lane | the new test passes against the current, unmodified code under test; raw output stored |
| `mutate-<gap-id>` (wave 2, depends on the matching `author-<gap-id>`) | `builder` | standard | write | the specific implementation path(s) the new test exercises, disjoint from every other mutate lane, reverted before the lane returns | the new test fails against a deliberate break of that path, and passes again once the break is reverted; both raw outputs stored, and the final diff against the implementation path is empty |
| `integration-gate` (wave 3, depends on every `mutate-<gap-id>`) | `prover` | standard | execute | none | full repository gate exits clean, raw output stored; the only run counting toward G9 |

`mutate-<gap-id>`'s deliverable is evidence, not a change: unlike an ordinary
`builder` lane, its final diff must be empty. A leftover diff after it
returns is a failure of that lane, not a successful mutation check.

## Delegation contract

You dispatch at depth one. Maximum delegation depth is two, and `mechanic` is
the only role dispatchable at depth two: an `author-<gap-id>` or
`mutate-<gap-id>` lane may hand an already-specified repetitive edit to a
`mechanic` confined to its own declared paths (see `../../roles/mechanic.md`);
no other lane delegates, and `mechanic` never delegates further.

One writer per path, declared before dispatch (G7): within a gap,
`author-<gap-id>` owns the test file and `mutate-<gap-id>` owns the
implementation path it exercises, and those never intersect; across gaps,
every author and every mutate lane's owned paths stay disjoint from every
other gap's.

On a host that cannot dispatch parallel subagents, cover degrades to a
sequential fresh-context role-pass: `sweep`, then each gap's `author` and
`mutate` lanes, one at a time, each in a fresh context, never merged and
never skipped. A later lane in the pass reads an earlier lane's stored
artifact — the gap list, the new test file — never its reasoning about why it
wrote what it wrote.

## Quality gates

cover's defining gate is its own: a `mutate-<gap-id>` lane returning
`verified` requires the break-run to fail; a mutate lane whose break-run
passes means the test is vacuous, and that lane is a failure, not a clean
result to wave through. G1's usual shape does not map directly — there is no
product implementation preceding the test, since the code under test already
exists; the analogous ordering is that the new test predates any deliberate
break. G2 applies to every stored run, break and revert alike. G4 triggers
automatically when the gap under test sits on auth or authz, payments,
secrets, deserialization, file upload, or shell, SQL, or template
construction — escalate that mutate lane's care accordingly. G6 caps
delegation depth as above. G7 is checked as described in Delegation
contract. G9 is decided by `integration-gate`'s single run after every gap
closes. Full definitions: `../../references/gates.md`.

## Evidence and completion

Evidence, not assertions: each `mutate-<gap-id>`'s two raw runs — the
break-run that must fail and the revert-run that must pass again — are that
gap's completion evidence, both pointing at stored raw output under
`.orchestra/<run>/<nn>-cover/evidence/`. A `verified` status with only the
passing revert-run stored, and no break-run, is a failure of that lane.
`sweep`'s gap list, every author and mutate lane's stored evidence, and
`integration-gate`'s final run together are the run's completion evidence.

## Hard stops

HARD STOP before every irreversible or outward-facing action, and never take
one inside a lane. A `mutate-<gap-id>` lane that leaves its deliberate break
unreverted at return time is a stop in its own right — do not let broken
implementation code reach `integration-gate`, and do not let a different lane
revert it on `mutate-<gap-id>`'s behalf; only that lane, or a redispatch of
it, may revert its own break. A gap with no seam a mutation can reach safely
is a stop too, not a forced-through edit. Record every stop request in
`stops.md` before making it. See `../../references/stops.md`.

## Deterministic outputs

A cover run writes `run.json` (resolved host, gap count, per-gap tier and any
escalation trigger, delegation depth, `reopenCount`), `baseline.md` (the
pre-dispatch clean-build confirmation, `git status`, and `git diff`),
`decomposition.md` (the gap list and lane plan as dispatched), one
`lanes/<lane-id>.md` per lane — `sweep`, every `author-<gap-id>`, every
`mutate-<gap-id>`, and `integration-gate` — `evidence/<nn>-<label>.txt` per
stored raw output including every break-run and revert-run, `stops.md` for
every hard-stop request and its answer, and `handoff.md` naming which gaps
are covered with evidence, which remain open, and the next dispatchable gap.
`findings.md` is written only if `sweep` or a `mutate-<gap-id>` lane surfaced
findings beyond the gap list itself; cover itself renders no `verdicts.md` by
default. Full layout: `../../references/run-ledger.md`.

## Failure and recovery

An `author-<gap-id>` lane whose test does not pass against current code, or a
`mutate-<gap-id>` lane whose break-run does not fail, is redispatched —
capped at three reopens per gap (`reopenCount` in `run.json`); a fourth
failure on the same gap escalates to the human rather than another retry.
Quarantine is bounded by the pre-dispatch baseline: revert a failed mutate
lane's edits only within the implementation path it declared and that was
clean at baseline; anything else is a hard stop, not an automatic revert. If
`integration-gate` fails after every gap reported `verified`, reopen the
specific gap whose evidence the gate output implicates, not the whole sweep.
