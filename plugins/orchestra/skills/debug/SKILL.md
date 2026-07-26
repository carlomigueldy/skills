---
name: debug
description: Escalate through a cheap reproduction sweep, scoped analysis, and deep hypothesis work to pin one defect's cause with a failing test — and stop there, before the fix.
---

# debug

Shape: staged escalation

You are the ROOT ORCHESTRATOR for this run. Do not implement inline: debug's
job is to escalate through progressively more expensive lanes — a cheap
reproduction sweep, then scoped analysis, then deep hypothesis work only if
the cheaper stages don't converge — and stop the moment a cause is proven and
pinned by a failing test. That stopping point is the entire discriminator: a
debug run that produces a patch has overrun its scope, no matter how obvious
the fix looked once the cause was clear.

debug does not fix the defect it finds. It hands off to `implement` with a
one-item plan: the pinned test's path, the causal explanation, and the
reproduction's raw output as evidence. debug also does not decide where a
whole backlog of problems should go — one item with an unknown cause is
debug's job; a set of many items whose ranking is unknown is `triage`'s. If
the input turns out to be a bundle of unrelated symptoms rather than one
defect, stop and name `triage` instead of debugging the bundle as if it were
one thing.

## Required inputs

debug fails closed. It requires a single observable symptom with a way to
trigger it: an error message, a failing or flaky test, or documented
reproduction steps. A request with no observable symptom ("something feels
off") has nothing to sweep — stop and name what's needed to make it
observable before dispatching.

If the input actually bundles several unrelated symptoms, stop and name
`triage`: ranking a set is not debug's job. If the input is a requested
behavior change rather than a defect, stop and name `plan` or `implement`
instead of debugging something that was never broken.

debug also requires a captured baseline — `git status` and `git diff` before
any lane starts — the same as every write-capable orchestra run. See
`../../references/run-ledger.md`.

## Lane plan

Stages are named and gated by an explicit promotion condition, not a vibe:
Stage 1 always runs; Stage 2 runs only once Stage 1 confirms a reproduction;
Stage 3 runs only on the Stage 2 disagreement or non-convergence condition
stated below.

| Lane | Role | Tier | Stage | Access | Owns | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| `repro-sweep` | `scout` | fast | 1 — reproduction sweep | read_only | none | every existing occurrence of the symptom (prior reports, matching error strings, recently changed code touching the symptom's area) with a pointer per entry and an explicit count, zero included |
| `repro-confirm` | `prover` | standard | 1 — reproduction sweep | execute | none | the symptom triggered on demand by the cheapest available method, raw pass/fail output stored; `blocked` naming what's missing if it will not reproduce |
| `scoped-analysis` | `analyst` | standard | 2 — scoped analysis | read_only | none | `repro-sweep`'s candidates narrowed to exactly one testable hypothesis about the mechanism, traced to the confirmed reproduction |
| `hypothesis-test` | `prover` | standard | 2 — scoped analysis | execute | none | the single hypothesis tested directly — toggle, bisect, or targeted probe against the reproduction — with both directions' raw output stored |
| `deep-analysis` | `analyst` | standard by default, escalated to deep only on the trigger below (see `../../roles/adversary.md` for the precedent this mirrors) | 3 — deep hypothesis work, dispatched only on promotion | read_only | none | a converged hypothesis over the full implicated boundary, not just Stage 2's shortlist, naming what evidence ruled out every rejected mechanism |
| `pin-cause` | `builder` | standard | terminal | write | exactly the new or modified test file(s) encoding the confirmed hypothesis | a test that fails, with the same failure signature the confirmed hypothesis predicts; raw failing output stored; no implementation change accompanying it; the causal explanation traced to the mechanism |

Promote Stage 1 to Stage 2 only when `repro-confirm` reproduces the symptom;
if it cannot, after exhausting the reported steps and `repro-sweep`'s
candidates, debug does not guess its way into analysis — it returns `blocked`
naming what a human needs to supply to make the defect observable. Promote
Stage 2 to Stage 3 only when `scoped-analysis` cannot converge on one
hypothesis the evidence supports, or when `hypothesis-test`'s result
contradicts it — that disagreement is itself the escalation trigger, recorded
in `run.json`. When `hypothesis-test` confirms the hypothesis cleanly, do not
promote; dispatch `pin-cause` directly.

## Delegation contract

You dispatch at depth one. Maximum delegation depth is two, and `mechanic` is
the only role a lane may legally dispatch at depth two; `pin-cause` may hand a
`mechanic` a repetitive edit already specified within its own declared paths
(see `../../roles/mechanic.md`), though a single pinning test rarely needs
one. No lane may dispatch any other role.

One writer per path, declared before dispatch (G7): `pin-cause` is debug's
only write lane, so this mostly guards against it touching anything beyond
the test file(s) it declared.

On a host that cannot dispatch parallel subagents, debug degrades to a
sequential fresh-context role-pass: the same stages, in the same order, run
one lane at a time in a fresh context each — never fewer stages, never merged
lanes. A later lane reads an earlier lane's stored deliverable, never its
reasoning; this matters most for `hypothesis-test` reading `scoped-analysis`'s
written hypothesis rather than the reasoning that produced it. Record the
resolved scheduler in `run.json` per `../../references/hosts.md`.

## Quality gates

G1 applies to `pin-cause` in its narrowest form: its only artifact is the
failing test, and that is correct here, not incomplete — the implementation
half of G1 belongs to `implement`, not to this workflow. G2 binds every
stage: a stage's `verified` status with no stored raw output is a failure of
that stage, not a formality. G4 triggers automatically when the implicated
code touches auth or authz, payments, secrets, deserialization, file upload,
or shell, SQL, or template construction — check this against the candidates
`repro-sweep` inventories, not against what the report happened to mention.
G6 caps delegation depth as described above. Full definitions:
`../../references/gates.md`.

G9 applies narrowly here: after `pin-cause` lands, run the existing suite
once more to confirm the new failing test is the only new failure — that a
diagnostic addition didn't destabilize anything else. That run's output is
the completion evidence; a rerun after adjusting the test replaces it, never
sits alongside it.

## Evidence and completion

Evidence, not assertions: every stage's `verified` status requires at least
one evidence entry pointing at stored raw output under
`.orchestra/<run>/<nn>-debug/evidence/`. `repro-confirm`'s raw failure, both
directions of `hypothesis-test`'s toggle, and `pin-cause`'s raw failing
output are the run's core evidence chain — each stage's conclusion has to be
traceable back through the one before it, not asserted on its own.

## Hard stops

HARD STOP before every irreversible or outward-facing action, and never take
one inside a lane: a lane that reaches a stop condition returns `blocked`
with an escalation, and you own the decision. Widening `pin-cause`'s declared
path past the test file(s) it was dispatched with, or writing anything that
resembles an implementation change, are stops in their own right — debug
producing a patch is exactly the failure mode this workflow exists to
prevent. Record every stop request in `stops.md` before making it. See
`../../references/stops.md`.

## Deterministic outputs

A debug run writes `run.json` (resolved host, the `deep-analysis` escalation
trigger if fired, dispatch waves), `baseline.md` (pre-dispatch `git status`
and `git diff`), `decomposition.md` (the stage plan as dispatched, including
each promotion decision and why it fired, not a later summary),
`lanes/<lane-id>.md` per lane holding its brief and normalized result
verbatim, `evidence/<nn>-<label>.txt` for every stored artifact including the
post-pin regression check, `stops.md` for any stop request, and `handoff.md`
naming the one-item plan for `implement`: the pinned test's path, the causal
explanation, and pointers to the evidence chain that proves it. `findings.md`
is written only if a lane surfaces a genuine finding along the way; debug
itself renders no verdict. Full layout: `../../references/run-ledger.md`.

## Failure and recovery

A `blocked` or `partial` result at Stage 1 stops the run there — do not
promote to analysis on an unconfirmed reproduction. A Stage 2 disagreement
promotes to Stage 3 by design, per the trigger above; a Stage 3 that still
does not converge is a human escalation, not a fourth stage to invent.

If `pin-cause`'s test fails for a different reason than the confirmed
hypothesis predicted, that is its own failure — redispatch the analysis stage
that produced the wrong prediction, capped at three redispatches
(`reopenCount` in `run.json`), rather than editing the test until it matches
whatever it happened to do. Adjusting a test to fit its own output is not
pinning a cause; it is destroying the evidence that the cause was proven.

A fourth failure on the same lane is a human escalation, not another retry.
