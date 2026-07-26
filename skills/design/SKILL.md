---
name: design
description: Resolve interface-shape uncertainty into an ADR and interface contract, using independent architect proposals adjudicated by a judge.
---

# design

Shape: judge panel

You are the ROOT ORCHESTRATOR for this run. Do not implement inline: design
resolves *shape* uncertainty, not sequencing uncertainty — it decides what
the interface looks like and why, and it never writes product code itself.
Its deliverable is an ADR paired with an interface contract, not a task
graph.

design does not decide work order. If you already know the interface and
need to know in what order to build it, that is `plan`'s job, not design's.
The discriminator is mechanical: if the interface is settled and the order
is not, use plan; if the order is settled (or doesn't matter yet) and the
interface is not, use design.

## Required inputs

design fails closed. It requires the design question stated as a decision to
be made — not "review this area" but "should the interface take X shape or Y
shape, and why" — plus enough context about the interface's consumers and
constraints for a proposal to be judged against something real rather than
taste. If that context does not exist yet, design stops and names `research`
as the prerequisite, rather than having an `architect` lane guess at
constraints nobody gathered.

If the actual uncertainty turns out to be sequencing rather than shape — the
interface is effectively decided and the open question is what order to
build it in — design stops and redirects to `plan`, per the discriminator
above.

## Lane plan

| Lane | Role | Tier | Access | Owns | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `propose-a`, `propose-b` (wave 0, independent) | `architect` | deep | read_only | none | drafts an ADR — the decision, the alternatives considered, and why each rejected alternative was rejected — plus an interface contract precise enough to implement without further judgement |
| `adjudicate` (wave 1, depends on both propose lanes) | `judge` | deep | read_only | none | selects or synthesizes one ADR and interface contract from the drafts, states why the rejected proposal fails against the stated constraints, and the result is precise enough that a `plan` workflow could decompose work against it without raising a new design question |

Each `propose` lane drafts without reading the other's draft, so the panel
produces two genuinely different shapes rather than one architect's opinion
dressed up as two. `adjudicate` is the only lane that reads both.

## Delegation contract

You dispatch at depth one; `architect` and `judge` both have
`canDelegate: false`, so design never approaches depth two.
Maximum delegation depth is two is not a live constraint on design's own
lanes for that reason, but it still bounds whatever `plan` later derives from
design's output, and `adjudicate` should note in its rationale if the
interface contract implies work that would need delegation beyond that
ceiling.

On a host that cannot dispatch parallel subagents, design degrades to a sequential fresh-context role-pass: `propose-a` runs to completion in a
fresh context, then `propose-b` runs in its own fresh context without
reading `propose-a`'s draft. `adjudicate` still runs last and still reads
both, preserving the same independence the parallel form relies on.

## Quality gates

G3's isolation principle motivates the panel's independence even though G3
itself is `verify`'s gate: a design judged against only one proposal is a
rubber stamp, not an adjudication, so `propose-a` and `propose-b` never see
each other's draft before `adjudicate` reads both. G6 caps whatever
delegation depth `adjudicate`'s accepted contract implies for later work.
Because design never writes, G1, G4, G5, and G7 do not apply to design's own
lanes; they apply to the `plan` and `fan-out` runs that later act on the
interface contract design produced. Full definitions:
`../../references/gates.md`.

## Evidence and completion

Evidence, not assertions: each `propose` lane's evidence points at its
stored ADR and interface contract draft under
`.orchestra/<run>/<nn>-design/evidence/`, and `adjudicate`'s evidence points
at the specific constraint or consumer requirement that decided between
them. An adjudication that prefers one draft "on balance" with no cited
constraint is not `verified` — name what settled it or return `unverified`.

## Hard stops

HARD STOP before treating an adjudicated design as final if a rejected
proposal's objection was never actually addressed, only outvoted:
overriding a real constraint one proposal raised, without recording why it
no longer applies, is a stop. Widening the interface contract's scope past
the original design question, and silently dropping an alternative from the
ADR to make the panel converge faster, are stops in their own right. Record
every stop request in `stops.md` before making it. See
`../../references/stops.md`.

## Deterministic outputs

A design run writes `run.json` (resolved host, capabilities, tier mapping),
`baseline.md` (the state of whatever the interface will sit against,
captured before drafting), `decomposition.md` holding the adjudicated ADR
and interface contract (the file `plan` reads as its own upstream context
when the two are chained), `lanes/propose-a.md`, `lanes/propose-b.md`, and
`lanes/adjudicate.md` holding each brief and normalized result verbatim,
`evidence/<nn>-<label>.txt` for every stored draft and the constraint
citations behind the adjudication, `stops.md` for any stop request, and
`handoff.md` naming the accepted interface contract and, if one exists, the
next workflow (`plan`) that decomposes work against it. Full layout:
`../../references/run-ledger.md`.

## Failure and recovery

If neither draft survives its objections — both proposals fail a stated
constraint and no synthesis of the two clears it either — `adjudicate`
returns `unverified` naming the constraint that neither draft satisfies,
rather than picking the less-bad option and calling it a decision.
Redispatch a `propose` lane at most three times (`reopenCount` in
`run.json`) with the failing constraint stated explicitly before escalating
to the human; a fourth failure to satisfy it is an escalation, not another
attempt.
