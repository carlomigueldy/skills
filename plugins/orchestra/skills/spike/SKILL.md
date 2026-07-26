---
name: spike
description: Answer one falsifiable question with throwaway code and kill criteria declared before work starts, then decide and discard.
---

# spike

Shape: fan-out barrier

You are the ROOT ORCHESTRATOR for this run. Do not implement inline: spike
answers one falsifiable question by writing code that is never meant to
ship, then discards it. Its deliverable is a decision, not a feature — a
spike whose code ends up in the mainline has failed regardless of what the
decision said. spike shares `fan-out`'s barrier discipline — competing
prototype lanes run concurrently, the barrier holds until both return, and
one decision follows — but it exists as its own workflow because its gates
are inverted rather than merely relaxed.

spike is not `implement` run carelessly. `implement` (via `fan-out` or on
its own) owns tests-first, mainline paths, and code meant to last; spike
owns a timeboxed answer to a question, throwaway paths, and code meant to
be deleted. Do not reach for spike to skip tests on real work, and do not
let a spike's prototype quietly become the implementation — that conversion
is `implement`'s job, done from scratch against the spike's decision, not a
rename of the spike's code.

## Required inputs

spike fails closed. It requires a question stated so it can be answered yes
or no, and kill criteria — the specific observation that would end the
spike early with a "no" — declared before any prototype lane is dispatched,
not written up afterward to match whatever happened. It also requires a
throwaway path declaration: where the prototype code will live, distinct
from every path any other lane or the mainline owns.

If the real uncertainty is interface shape with no time pressure to resolve
it quickly, that is `design`'s job, not spike's; if the question is really
about work order over a shape everyone already agrees on, that is `plan`'s.
spike is for the case where the fastest way to answer the question is to
build a small throwaway thing and look at it.

## Lane plan

| Lane | Role | Tier | Access | Owns | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `declare-kill-criteria` (wave 0) | `analyst` | standard | read_only | none | states the question, the falsifiable kill criteria, and the throwaway path(s), before any prototype lane dispatches |
| `prototype-a`, `prototype-b` (wave 1, depends on declare-kill-criteria) | `builder` | standard | write | its own declared throwaway path, disjoint from the other prototype's and from every mainline path | the declared question is answered against the kill criteria; G1 is suspended for this lane and the suspension is recorded in the run record |
| `decide` (wave 2, depends on both prototype lanes) | `analyst` | standard | read_only | none | records go or no-go against the kill criteria stated in wave 0, cites each prototype's evidence, and confirms every throwaway path is excluded from anything the run would commit |

A single prototype lane is enough when there is only one approach worth
trying; two competing approaches is the common case spike exists for, and
both run in the same wave without reading each other's code.

## Delegation contract

You dispatch at depth one. Maximum delegation depth is two still applies if
a `prototype` lane needs repetitive throwaway edits and hands them to a
`mechanic` confined to its own declared throwaway path — the depth cap does
not relax along with G1.

On a host that cannot dispatch parallel subagents, spike degrades to a sequential fresh-context role-pass: `prototype-a` and `prototype-b` run one
at a time in fresh contexts, neither reading the other's code, before
`decide` runs last against both. The kill criteria and the throwaway path
declarations do not change with the scheduler.

## Quality gates

G1 is explicitly suspended for `prototype` lanes: no failing test is
required before the throwaway code exists, and this suspension is recorded
in the run record rather than silently skipped — a spike whose run record is
silent about the suspension is indistinguishable from a `builder` lane that
just skipped its test, and that ambiguity is the failure mode this rule
exists to prevent. G5 is not suspended: a `prototype` lane confined to its
declared throwaway path that reaches outside it is still a scope violation,
kill criteria or not. G9 does not apply in its literal form — there is no
mainline integration to run the full repository gate against, since the code
is not staying — but its discipline survives in `decide`: two prototypes
returning is not a decided spike, and `decide` runs exactly once, after both
return, with only that pass counting. G4 still triggers if a prototype
touches a security surface; "throwaway" does not exempt a prototype from the
same automatic security pass a real change would get, because throwaway code
has a way of getting copied into something that ships. Full definitions:
`../../references/gates.md`.

## Evidence and completion

Evidence, not assertions: `declare-kill-criteria`'s evidence is the stored
criteria themselves, each `prototype` lane's evidence is whatever raw output
demonstrates its answer to the question, and `decide`'s evidence cites both,
stored under `.orchestra/<run>/<nn>-spike/evidence/`. A go or no-go decision
with no cited prototype evidence is a failure of the `decide` lane, kill
criteria or not.

## Hard stops

HARD STOP before dispatching a `prototype` lane without recorded kill
criteria — building throwaway code with no declared way to stop early is
exactly the failure mode spike exists to prevent. HARD STOP before any
commit, push, or PR that includes a path a `prototype` lane owned: that is
what actually enforces "a spike that ships its code has failed" — the code
does not leave the throwaway path without going through the same stop every
outward-facing action does, and re-implementing the decision through
`implement` is the sanctioned path to shipping it. Record every stop request
in `stops.md` before making it. See `../../references/stops.md`.

## Deterministic outputs

A spike run writes `run.json` (resolved host, capabilities, the recorded G1
suspension, delegation depth), `baseline.md` (state before any prototype
lane starts), `decomposition.md` (the question, the kill criteria, and the
throwaway path declarations from wave 0), `lanes/declare-kill-criteria.md`,
`lanes/prototype-a.md`, `lanes/prototype-b.md`, and `lanes/decide.md`
holding each brief and normalized result verbatim,
`evidence/<nn>-<label>.txt` for every stored artifact demonstrating the
answer, `stops.md` for any stop request, and `handoff.md` naming the
go/no-go decision and confirming the throwaway code's final disposition —
discarded or left uncommitted under its declared path. Full layout:
`../../references/run-ledger.md`.

## Failure and recovery

A prototype lane that hits a declared kill criterion mid-build stops there
and returns naming the criterion that fired — that is a correct early
result, not a failure to redispatch. A prototype that returns `blocked` for
an unrelated reason (environment, missing input) may be redispatched,
capped at three attempts (`reopenCount` in `run.json`), before the question
itself is escalated to the human as unanswerable within the timebox. If
both prototypes return but `decide` cannot reach a go or no-go from their
evidence, `decide` returns `unverified` naming what a third attempt would
need to show, rather than picking the more promising prototype and calling
it a decision.
