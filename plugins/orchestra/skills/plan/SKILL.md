---
name: plan
description: Resolve sequencing uncertainty into a machine-checkable task graph with exclusive path ownership, using independent architect proposals adjudicated by a judge.
---

# plan

Shape: judge panel

You are the ROOT ORCHESTRATOR for this run. Do not implement inline: plan
resolves *sequencing* uncertainty, not shape uncertainty — it decides how a
goal decomposes into lanes, what depends on what, and who owns which paths,
and it never writes product code itself. Its deliverable is a dispatchable
lane plan: the exact artifact every write-workflow, including `fan-out`,
fails closed without.

plan does not decide interface shape. If the question is "what should the
interface look like," not "in what order should the work happen," that is
`design`'s job, not plan's — dispatch `design` first and decompose against
its output. The discriminator is mechanical: if you already know the
interface and need the order, use plan; if you already know the order and
need the interface, use design.

## Required inputs

plan fails closed. It requires a goal stated precisely enough to bound a
decomposition — what is in scope, what is explicitly out — and read access to
whatever the decomposition partitions (a repository, a set of documents, a
set of services). Without a bounded goal, an architect lane cannot state
acceptance a reader can check, and an unboundable decomposition is not
dispatchable.

If the goal's interface shape is still undecided — the decomposition would
have to guess what the pieces are before it can sequence them — plan stops
and names `design` as the prerequisite, per the discriminator above, rather
than producing a task graph over an interface nobody has committed to.

Every lane the panel produces must conform to `../../schemas/lane.schema.json`;
read that schema before drafting or adjudicating, because a plan that does
not validate against it is not dispatchable regardless of how sound its
reasoning is.

## Lane plan

| Lane | Role | Tier | Access | Owns | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `decompose-a`, `decompose-b` (wave 0, independent) | `architect` | deep | read_only | none | drafts a lane plan conforming to `../../schemas/lane.schema.json` — every lane carries a stable id, one role, one tier, one access mode, an ordered `dependsOn`, its owned paths or none, its inputs, exactly one deliverable, and acceptance a reader other than the lane can check |
| `adjudicate` (wave 1, depends on both decompose lanes) | `judge` | deep | read_only | none | selects or synthesizes one lane plan from the drafts, states why the rejected draft or the rejected parts of each fail, and the result still validates against `../../schemas/lane.schema.json` |

Each `decompose` lane drafts without reading the other's draft — that is what
makes two proposals worth adjudicating instead of one being rubber-stamped.
`adjudicate` is the only lane that reads both.

## Delegation contract

You dispatch at depth one; `architect` and `judge` both have
`canDelegate: false`, so nothing here reaches depth two.
Maximum delegation depth is two remains the ceiling plan itself must respect
if a drafted plan proposes delegation beyond that: a lane plan that assigns a
`mechanic` lane anywhere but depth two, or proposes depth three at all, fails
validation and needs a written justification in the run record before
`adjudicate` may accept it.

On a host that cannot dispatch parallel subagents, plan degrades to a sequential fresh-context role-pass: `decompose-a` runs to completion in a
fresh context, then `decompose-b` runs in its own fresh context without
reading `decompose-a`'s draft, preserving the independence the panel depends
on. `adjudicate` still runs last and still reads both.

## Quality gates

G7 is what plan exists to make checkable downstream: one writer per path,
declared before dispatch. The adjudicated plan is the declaration — every
`write` lane's owned paths must be pairwise disjoint, and `adjudicate`
rejects a draft that cannot satisfy this rather than passing the collision
downstream for a `builder` lane to discover. G6 caps the depth any drafted
plan may declare, as above. Because plan itself never writes, G1, G4, and G5
do not apply to plan's own lanes; they apply to whatever the plan's lanes
look like once dispatched by `fan-out`, and `adjudicate`'s acceptance check
is what keeps those gates satisfiable later. Full definitions:
`../../references/gates.md`.

## Evidence and completion

Evidence, not assertions: each `decompose` lane's evidence points at its
stored draft, and `adjudicate`'s evidence includes the raw output of
validating the final plan against `../../schemas/lane.schema.json` — a
synthesis that was never actually run through the schema is not `verified`.
A plan accepted on the reasoning alone, without that validation output
stored under `.orchestra/<run>/<nn>-plan/evidence/`, is a failure of the
`adjudicate` lane.

## Hard stops

HARD STOP before treating an unvalidated plan as dispatchable: if
`adjudicate` cannot produce a lane plan with disjoint ownership and complete
acceptance conditions, that is a stop, not a plan shipped with a known gap.
Widening ownership after the fact, accepting a plan that proposes delegation
depth beyond two without a recorded justification, and silently dropping a
lane's acceptance condition to make the panel converge are stops in their own
right. Record every stop request in `stops.md` before making it. See
`../../references/stops.md`.

## Deterministic outputs

A plan run writes `run.json` (resolved host, capabilities, tier mapping,
delegation depth), `baseline.md` (state of whatever the decomposition
partitions, captured before drafting), `decomposition.md` (the adjudicated
lane plan, written once `adjudicate` accepts it — this is the file `fan-out`
reads as its own required input), `lanes/decompose-a.md`,
`lanes/decompose-b.md`, and `lanes/adjudicate.md` holding each brief and
normalized result verbatim, `evidence/<nn>-<label>.txt` including the
schema-validation output, `stops.md` for any stop request, and `handoff.md`
naming the adjudicated plan and the first dispatchable lane in it. Full
layout: `../../references/run-ledger.md`.

## Failure and recovery

If neither draft converges — both decompose lanes propose incompatible
ownership and neither the drafts nor a synthesis of them clears schema
validation — `adjudicate` returns `unverified` naming what would settle it,
rather than forcing a plan through on the confidence of one draft over the
other. Redispatch a `decompose` lane at most three times (`reopenCount` in
`run.json`) with a sharper goal statement before escalating to the human; a
fourth non-convergence is an escalation, not another attempt.
