---
name: review
description: Judge a single diff through independent lenses — correctness, security, performance, maintainability, and test adequacy — then synthesize one verdict.
---

# review

Shape: judge panel

You are the ROOT ORCHESTRATOR for this run. Do not implement inline: review
judges a diff that already exists; it never writes product code and it
never re-derives what the diff should have been. It is partitioned by lens,
not by file — every lane reads the same diff in full and applies a
different standard to it, rather than each lane owning a slice of files.

review is not `verify` and it is not `harden`. `verify` executes to prove or
disprove one stated claim; `review` judges a diff through multiple standing
lenses without a single claim to falsify. `harden` attacks a surface the way
an adversary would, looking for exploitable defects; review's security lens
does that too, but review's other four lenses are asking different
questions entirely — is this correct, is this fast enough, is this
maintainable, are the tests adequate — that harden does not ask at all.
None of the three subsumes the others; a run that needs all three dispatches
all three.

## Required inputs

review fails closed. It requires a diff that already exists — a completed
change, not a plan for one. If nothing has been implemented yet, review
stops and names `implement` (or `fan-out`, for an already-decomposed
multi-lane change) as the prerequisite, rather than reviewing intent instead
of a diff. It also requires the diff's declared scope if one exists — the
paths a `builder` lane was supposed to touch — so a lens can flag scope
creep as a factual observation, not a guess.

## Lane plan

| Lane | Role | Tier | Access | Owns | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `lens-correctness` | `analyst` | standard | read_only | none | every claim about behavior traces to a path and line in the diff or a stored command output; disagreement with the diff's own tests is stated explicitly, not smoothed over |
| `lens-security` | `adversary` | standard by default; escalate to `deep` on a declared trigger recorded in `run.json` (see `../../roles/adversary.md`) | read_only | none | every finding names a reachable precondition and points at stored evidence, per G4 |
| `lens-performance` | `analyst` | standard | read_only | none | every claim cites the code path or the stored measurement that supports it, not an intuition about cost |
| `lens-maintainability` | `analyst` | standard | read_only | none | every claim points at the specific lines that would confuse a future reader, with what a clearer version would look like |
| `lens-test-adequacy` | `prover` | standard | execute | none | the diff's tests are actually run and their raw output stored, plus an explicit list of behaviors the diff changes that no test in the suite exercises |
| `adjudicate` (depends on all five lenses) | `judge` | deep | read_only | none | one recorded verdict — `approve`, `request_changes`, or `unverified` — with its rationale and the unresolved critical-and-high count it was decided against |

All five lens lanes run in the same wave over the identical diff and do not
read each other's output before returning; `adjudicate` is the only lane
that reads all five.

## Delegation contract

You dispatch at depth one; none of review's roles delegate further —
`analyst`, `adversary`, `prover`, and `judge` all have `canDelegate: false`.
Maximum delegation depth is two is not a live constraint here for that
reason; review's job is judgment, not further decomposition.

On a host that cannot dispatch parallel subagents, review degrades to a sequential fresh-context role-pass: each lens runs to completion in its own
fresh context, reading only the diff, never a prior lens's findings, before
the next lens starts. `adjudicate` still runs last and still reads all five
outputs together.

## Quality gates

G4 is `lens-security`'s gate by construction: it triggers automatically
whenever the diff touches auth or authz, payments, secrets, deserialization,
file upload, or shell, SQL, or template construction, regardless of whether
the change was framed as security work. G2 applies to every lens — a claim
with no stored evidence is a failure of that lens, not a stylistic nit.
`adjudicate` applies G9's spirit at the review layer: five green lenses are
not a green diff, so the verdict is decided from all five together, after
all five have returned, and only that pass counts. Full definitions:
`../../references/gates.md`.

## Evidence and completion

Evidence, not assertions: every lens's claims trace to stored evidence under
`.orchestra/<run>/<nn>-review/evidence/`, including `lens-test-adequacy`'s
raw test run. Normalize each lens's claims into `findings.md` using the same
inbound-label mapping the ledger defines — `bug` to `high`, `suggestion` to
`low`, `nit` to `informational` — then re-rate on the evidence rather than
trusting the lens's own severity framing (see
`../../references/findings.md`).
`adjudicate`'s verdict is recorded in `verdicts.md` and is `approve` only
while no unresolved `critical` or `high` finding remains, absent a recorded
human exception.

## Hard stops

HARD STOP before treating an `approve` verdict as authorization to merge,
push, or release: review produces a recorded judgment, not the outward
action itself, and that action still needs its own stop. Silently
downgrading a lens's finding to reach `approve`, and reviewing a diff wider
than what the lens lanes were actually given, are stops in their own right.
Record every stop request in `stops.md` before making it. See
`../../references/stops.md`.

## Deterministic outputs

A review run writes `run.json` (resolved host, the security lens's tier and
any escalation trigger), `baseline.md` (state before the review lanes read
anything), `lanes/lens-correctness.md`, `lanes/lens-security.md`,
`lanes/lens-performance.md`, `lanes/lens-maintainability.md`,
`lanes/lens-test-adequacy.md`, and `lanes/adjudicate.md` holding each brief
and normalized result verbatim, `evidence/<nn>-<label>.txt` for every stored
claim and the test-adequacy run, `findings.md` for every normalized finding
across all five lenses, `verdicts.md` for the recorded verdict, `stops.md`
for any stop request, and `handoff.md` naming the verdict and, on
`request_changes`, the next dispatchable lane to fix it. Full layout:
`../../references/run-ledger.md`.

## Failure and recovery

A `blocked` or `partial` result from any lens blocks the verdict:
`adjudicate` does not synthesize five inputs when one is missing, and
neither do you — a lens that could not complete is a gap in the review, not
an implicit pass. Reopen a blocked lens at most three times (`reopenCount`
in `run.json`) before escalating to the human instead of retrying again. A
finding moves to `fixed` only on a retest using evidence produced after the
remediation lands, per `../../references/findings.md`; reusing the evidence
that opened it leaves it `open`.
