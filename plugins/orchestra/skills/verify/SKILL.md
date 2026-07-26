---
name: verify
description: Falsify a claim in a context that never saw the authoring work, including the reverse-check that proves a test actually fails when the behavior it covers is removed.
---

# verify

Shape: adversarial verify

You are the ROOT ORCHESTRATOR for this run. Do not implement inline: verify is
the evidence gate every other workflow calls when it needs to know whether a
claim survives an attack, not just an inspection. It takes a claim — "the fix
works," "the feature does X," "the lanes integrated cleanly" — and tries to
falsify it in a context that never saw the authoring work (G3), then reports
what it found rather than what it hoped to find.

verify owns the reverse-check: proving that the test backing a claim actually
fails when the behavior it covers is removed or inverted. A test that only
ever ran green proves nothing — it may be checking the wrong thing, or
nothing at all — so verify is not satisfied by a passing suite alone. This is
the one property fan-out does not provide on its own; a fan-out run that
wants this level of scrutiny dispatches verify rather than reimplementing
falsification inline.

## Required inputs

verify fails closed. It requires an explicit claim stated as a falsifiable
sentence, and an artifact the claim is about — a diff, a deliverable, an
integrated tree — that the adversary lane can read without asking anyone what
it means. A claim with no pointer to an artifact ("it should work now") is
not verifiable; stop and name the workflow that should have produced the
artifact first — `implement` for a change not yet made, `fan-out` for lanes
not yet integrated, `debug` for a fix not yet landed — rather than inventing
something to inspect.

verify also requires the means to run the reverse-check: either the
pre-change state to revert to, or a way to invert the behavior under test.
Without one of these the reverse-check cannot execute, and verify records
that gap rather than skipping it silently.

## Lane plan

| Lane | Role | Tier | Access | Owns | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `falsify` | `adversary` | standard by default; escalate to `deep` only on a declared trigger recorded in `run.json` (see `../../roles/adversary.md`) | read_only | none | every finding names a reachable precondition and points at stored evidence; a concern with no path to reach it goes in a labeled speculation list, not the findings list |
| `reverse-check` | `prover` | standard | execute | none | the claim's test is executed twice — once as-is (must pass) and once against the change reverted or the behavior inverted (must fail) — and both raw outputs are stored under the same evidence set |
| `adjudicate` | `judge` | deep | read_only | none | dispatched only when `falsify` and `reverse-check` disagree, or when a verdict is requested directly; the verdict names which stored artifact settles the disagreement |

`falsify` and `reverse-check` run in the same wave and neither reads the
other's output before both return — that is what keeps the reverse-check
honest instead of just confirming what the adversary already flagged.
`adjudicate` depends on both and runs only when needed.

## Delegation contract

You dispatch at depth one; none of verify's roles delegate further —
`adversary`, `prover`, and `judge` all have `canDelegate: false`. The rule
that Maximum delegation depth is two applies to verify only insofar as it
never approaches it: verify has no `mechanic` lane and nothing here should
ever reach depth two.

Adversary isolation is the one property that cannot degrade quietly. On a
host that cannot dispatch parallel subagents, verify runs as a sequential fresh-context role-pass: `falsify` runs to completion in a fresh context,
then `reverse-check` runs in its own fresh context reading only the artifact
under test, never `falsify`'s reasoning or findings. If the host cannot give
`falsify` a context that never saw the authoring work at all — not even in
degraded sequential form — record `isolation: degraded` in `run.json` and cap
the verdict at `unverified`; never let a degraded isolation produce
`approve`.

## Quality gates

G3 is the gate this workflow exists to enforce: adversarial verification runs
in a context that never saw the authoring work, full stop. G2 is enforced on
every lane's output — a claimed pass with no stored raw output is a failure,
not a warning, and that applies as much to `reverse-check`'s output as to
`falsify`'s findings. G4 triggers automatically when the artifact under test
touches auth or authz, payments, secrets, deserialization, file upload, or
shell, SQL, or template construction — `falsify` works that surface first
regardless of whether the originating claim mentioned security. G9 applies
when verify runs as part of a larger integration: N green findings-free lanes
are not a green whole, and if the claim under test is "the lanes integrated
cleanly," the deciding evidence is the post-integration gate's own output,
not the individual lane results. Full definitions:
`../../references/gates.md`.

## Evidence and completion

Evidence, not assertions: `falsify`'s findings and `reverse-check`'s two
stored runs are the completion evidence, and a `verified` status on either
lane with no evidence entry pointing at
`.orchestra/<run>/<nn>-verify/evidence/` is a failure of that lane. A finding
without a reachable precondition and stored evidence is an opinion, not a
finding, and does not enter `findings.md` (see
`../../references/findings.md`). The verdict itself — `approve`,
`request_changes`, or `unverified` — is recorded in `verdicts.md` with its
rationale and the unresolved critical-and-high count it was decided against.

## Hard stops

HARD STOP before every irreversible or outward-facing action; verify itself
is read-only and execute-only by construction, so the stops that matter here
are downstream — a `request_changes` or `unverified` verdict must reach the
human or the calling workflow before any commit, push, or release proceeds on
the claim it examined. Never let a degraded-isolation `unverified` verdict be
presented as a pass to satisfy a waiting stop. Record every stop request in
`stops.md` before making it. See `../../references/stops.md`.

## Deterministic outputs

A verify run writes `run.json` (resolved host, the adversary's tier and any
escalation trigger, isolation status), `baseline.md` (state before dispatch,
useful even for a read-only run as a record of what was examined),
`lanes/falsify.md` and `lanes/reverse-check.md` holding each brief and
normalized result verbatim, `lanes/adjudicate.md` when `adjudicate` ran,
`evidence/<nn>-<label>.txt` for every stored command output including both
reverse-check runs, `findings.md` for every finding `falsify` raised,
`verdicts.md` for the recorded verdict, `stops.md` for any stop request, and
`handoff.md` naming what was verified, what remains open, and — on
`request_changes` — the next dispatchable lane to fix it. Full layout:
`../../references/run-ledger.md`.

## Failure and recovery

A `blocked` or `partial` result from `falsify` or `reverse-check` blocks the
verdict: `adjudicate` does not resolve a disagreement it lacks evidence for,
and neither do you. When the two lanes disagree outright, that disagreement
is itself the trigger to escalate `falsify` to `deep` tier and dispatch
`adjudicate` — record the trigger in `run.json` per
`../../roles/adversary.md`.

A finding moves to `fixed` only on a retest run after the remediation lands,
using evidence the fixing lane did not produce itself; reopen the originating
lane, capped at three redispatches (`reopenCount` in `run.json`) before the
failure becomes a human escalation instead of another retry. `accepted` and
`wontfix` each require a named human decision recorded in the ledger, never a
lane's own judgment call (see `../../references/findings.md`).
