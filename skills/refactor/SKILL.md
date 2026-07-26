---
name: refactor
description: Restructure code whose external contract must not move — lock current behavior in characterization tests before any edit lands, reshape internal structure, then prove the same lock still passes unchanged.
---

# refactor

Shape: pipeline

You are the ROOT ORCHESTRATOR for this run. Do not implement inline: refactor
runs one restructuring change through a fixed sequence — lock current
behavior in characterization tests, reshape internal structure behind that
lock, falsify the result, and gate once — never writing the change yourself.

refactor's defining property is a behavior lock before touch: the
characterization tests that capture current behavior must exist and pass
against the unmodified code before any structural edit is made. That lock is
the gate `implement` does not have — `implement` writes a failing test first
because the behavior is new; refactor writes a passing test first because
the behavior already exists and must not move. If the work turns out to
require the external contract itself to change — a different return shape,
a new side effect, a moved endpoint — that is `implement` or `migrate`, not
refactor, and this workflow stops and says so rather than absorbing the
change under a refactor label.

## Required inputs

refactor fails closed. It requires a named scope — the paths being
restructured — and an explicit non-goal: a statement that the external
contract (inputs, outputs, observable side effects) is not changing. It
requires either existing tests that already characterize the target's
current behavior, or the ability to write new characterization tests against
it. If the target has no seam a test can reach and none can be written, stop
and name the prerequisite: run `cover` to author tests over the target first,
or `spike` to establish a seam, before returning to refactor.

refactor also requires a captured baseline — `git status` and `git diff`
before any lane dispatches — so quarantine has a known-clean state to revert
to. See `../../references/run-ledger.md`.

## Lane plan

A strict sequential chain; each lane depends on exactly the lane before it.

| Lane | Role | Tier | Access | Owns | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `lock` | `builder` | standard | write | the new characterization test file(s) only | the tests pass against the current, unmodified code, raw output stored, before any structural edit exists |
| `reshape` (depends on `lock`) | `builder` | standard | write | the implementation paths under refactor, disjoint from `lock`'s test paths | `lock`'s test files are unedited; the same tests, rerun unchanged, pass against the reshaped code; the diff touches internal structure only |
| `falsify` (depends on `reshape`) | `adversary` | standard by default, escalate to `deep` only on a declared trigger (see `../../roles/adversary.md`) | read_only | none | an attempt to find an external-contract change `lock`'s tests missed; every finding names a reachable precondition and points at stored evidence |
| `integration-gate` (depends on `falsify`) | `prover` | standard | execute | none | full repository gate exits clean and `lock`'s tests are re-run one final time, raw output stored; the only run counting toward G9 |

`reshape` never touches a path `lock` owns; that disjointness is what makes
the lock trustworthy evidence rather than something the reshaping lane could
quietly edit around.

## Delegation contract

You dispatch at depth one. Maximum delegation depth is two, and `mechanic` is
the only role dispatchable at depth two: `reshape` may hand an
already-specified repetitive edit to a `mechanic` confined to its own
declared paths (see `../../roles/mechanic.md`); no other lane delegates, and
`mechanic` never delegates further.

On a host that cannot dispatch parallel subagents, refactor degrades to a
sequential fresh-context role-pass: the same four lanes, in the same order,
each in a fresh context, never merged and never skipped. A later lane in the
pass reads an earlier lane's stored artifact — the locked test file, the
reshaped diff — never its reasoning about why it wrote what it wrote; that
constraint is what keeps `falsify`'s isolation intact even in degraded mode.

## Quality gates

refactor's own gate sits beside the standard nine: `lock` must pass before
`reshape`'s first edit lands, and this deliberately inverts G1's
failing-test-first shape, because a characterization test that fails against
current behavior would be testing the wrong thing. G2 applies to every lane
— a claimed pass with no stored raw output is a failure. G5 and G7 are
checked mechanically: `reshape`'s diff touching `lock`'s owned test paths
fails both gates regardless of intent. G4 triggers automatically on the
integrated diff for auth, authz, payments, secrets, deserialization, file
upload, or shell, SQL, or template construction. G9 is decided by
`integration-gate`'s single run, which includes the final rerun of `lock`'s
tests, not by `reshape` reporting green in isolation. Full definitions:
`../../references/gates.md`.

## Evidence and completion

Evidence, not assertions: `lock`'s pre-edit passing run, `reshape`'s
unchanged-test rerun, `falsify`'s findings evidence, and
`integration-gate`'s final combined run are the completion evidence, each
pointing at stored raw output under
`.orchestra/<run>/<nn>-refactor/evidence/`. A `verified` status on `reshape`
with no side-by-side proof that `lock`'s exact test files produced the same
pass, unedited, is a failure of that lane, not a formality.

## Hard stops

HARD STOP before every irreversible or outward-facing action, and never take
one inside a lane. A `reshape` diff that touches `lock`'s test files, or a
`falsify` finding that shows the external contract actually moved, is a stop
in its own right — the run has become `implement` or `migrate` wearing a
refactor label, and continuing under refactor's gates would hide a behavior
change behind them rather than surface it. Record every stop request in
`stops.md` before making it. See `../../references/stops.md`.

## Deterministic outputs

A refactor run writes `run.json` (resolved host, capabilities, tier mapping,
delegation depth, `reopenCount`), `baseline.md` (the pre-dispatch `git
status` and `git diff`), `decomposition.md` (the declared non-goal and the
pipeline as dispatched), one `lanes/<lane-id>.md` per lane holding its brief
and normalized result verbatim, `evidence/<nn>-<label>.txt` per stored
artifact including `lock`'s original run, `reshape`'s rerun, and
`integration-gate`'s final combined run, `stops.md` for every hard-stop
request and its answer, and `handoff.md` stating what is locked and verified
with evidence pointers, what is open, and the next dispatchable lane.
`findings.md` is written only if `falsify` raised any; refactor itself
renders no `verdicts.md` by default. Full layout:
`../../references/run-ledger.md`.

## Failure and recovery

If `reshape`'s rerun of `lock`'s tests fails, that is not a flaky test — it
is proof the restructuring changed behavior. Revert `reshape`'s edits, bounded
by the pre-dispatch baseline and only within paths it exclusively owned, and
reopen it; redispatch capped at three reopens (`reopenCount` in `run.json`),
with a fourth failure escalating to the human rather than another retry. If
`falsify` surfaces a genuine external-contract change, do not patch `lock` to
accommodate the new behavior — that is scope creep into `implement` or
`migrate`, and the correct action is the stop described above, not a fix. If
`integration-gate` fails after `reshape` and `falsify` both reported
`verified`, scope the fix to `reshape` and rerun the gate once after it
lands.
