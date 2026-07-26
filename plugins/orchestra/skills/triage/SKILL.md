---
name: triage
description: Sweep a bounded set of problems, classify and rank each one, and emit a routing table naming which sibling workflow handles it next — triage fixes nothing itself.
---

# triage

Shape: sweep

You are the ROOT ORCHESTRATOR for this run. Do not implement inline: triage
is the only orchestra workflow whose input is a set of problems and whose
output is routing, not fixes. It sweeps the declared set, classifies each
item's nature, ranks the set by a stated rationale, and emits a routing table
naming which sibling workflow every item goes to — `debug` for one defect
with an unknown cause, `implement` for known work, `harden` for a security
surface, `migrate` for a boundary crossing, `upgrade` for an external-version
driven change, and so on. Say this plainly: triage fixes nothing itself. Its
product is the map, not a change to the terrain.

The discriminator against `debug` is the whole reason this workflow exists
separately: `debug` is one defect with an unknown cause; triage is many
problems with an unknown ranking. When the input set collapses to exactly one
item, triage should say so and route that single item directly to `debug`
(or whichever workflow its nature calls for) rather than running a full
sweep-classify-rank exercise on a set of one — that ceremony has no payoff
when there is nothing to rank against.

## Required inputs

triage fails closed. It requires a bounded, enumerable input set with a
source a `scout` lane can sweep exhaustively: an issue tracker query, a prior
run's `findings.md`, a pasted list, or a directory convention that names its
own edges. A set with no declared boundary — "find all the problems in this
codebase" — cannot be swept exhaustively, and a partial sweep presented as
complete is worse than no sweep at all; stop and name the missing scope
boundary (a directory, a query filter, a time window) rather than guessing
one.

If the input is already known to be exactly one defect with an unknown
cause, don't run triage at all — dispatch `debug` directly.

triage also requires a captured baseline — `git status` and `git diff` —
before any lane starts, the same as every orchestra run, even one with no
write lanes. See `../../references/run-ledger.md`.

## Lane plan

A sweep shape runs its lanes once, in dependency order, with no promotion
ladder: sweep, then classify, then rank.

| Lane | Role | Tier | Access | Owns | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `sweep` | `scout` | fast | read_only | none | every item in the declared input set inventoried with a pointer (file-and-line, ticket id, or `findings.md` entry id), an explicit count including zero, and `partial` naming the uncovered remainder if the set could not be finished |
| `classify` | `analyst` | standard | read_only | none | every swept item assigned a nature — one defect with unknown cause, known work, a security surface, an external-version-driven change, a boundary crossing, or a bundle of several problems — and one candidate destination workflow with a one-line rationale traced to the item's own evidence; an item the evidence does not decide is labeled `needs scoping`, never force-routed |
| `rank` | `analyst` | standard | read_only | none | the classified set ordered by a stated rationale (severity, blast radius, cost of delay), the ordering traceable per item; an item `classify` left `needs scoping` carries into the ranking unranked and flagged, never silently dropped or guessed into a slot |

`classify` depends on `sweep`'s stored deliverable and `rank` depends on
`classify`'s, each reading the artifact, never the reasoning behind it.

## Delegation contract

You dispatch at depth one. Maximum delegation depth is two in principle, but
nothing in triage should ever reach it: every lane is read_only and none owns
a path, so there is no `mechanic` lane and no repetitive edit for one to
apply — the rule that applies to every orchestra workflow simply has nothing
to bind here.

On a host that cannot dispatch parallel subagents, triage degrades to a
sequential fresh-context role-pass: `sweep`, `classify`, and `rank` already
run in strict dependency order, so degradation changes only the scheduler,
never the lane count or the order — the same three lanes, one at a time in a
fresh context each. Record the resolved scheduler in `run.json` per
`../../references/hosts.md`.

## Quality gates

G2 binds every lane: a classification or ranking entry with no traceable
pointer back to `sweep`'s inventory is a failure of that lane, not an
acceptable shortcut. G4 has a direct routing consequence here — an item
`classify` names as touching auth or authz, payments, secrets,
deserialization, file upload, or shell, SQL, or template construction routes
to `harden` specifically, not to generic `implement`, and the routing table
says so explicitly.

G5 and G7 do not bind on this run's own output — there is no write lane and
no lane owns a path — but they resume being fully load-bearing the instant a
routed item is dispatched into a write-capable workflow; triage's routing
table does not carry any exemption forward. G6 has nothing to cap, as above.
G9 likewise does not bind here — there is nothing to integrate — and
resumes applying in full to whichever workflow eventually acts on a routed
item. Full definitions: `../../references/gates.md`.

## Evidence and completion

Evidence, not assertions: `sweep`'s inventory, `classify`'s per-item
rationale, and `rank`'s ordering rationale are the completion evidence, and a
`verified` status on any of the three with no evidence entry pointing at
`.orchestra/<run>/<nn>-triage/evidence/` is a failure of that lane. A routing
decision with no traceable rationale is an opinion, not a routing decision.

## Hard stops

HARD STOP before every irreversible or outward-facing action; triage itself
is read-only by construction, so nothing inside it is a stop condition on its
own. The stop that matters is downstream: before the root, or whatever called
triage, treats a routing-table row as authorization to dispatch the named
workflow — most pointedly a row routed to `migrate` or one flagged by G4. A
routing table is a recommendation with a stated rationale, not a queued
dispatch, and presenting it as one skips the stop the destination workflow
would otherwise take on its own. Record every stop request in `stops.md`
before making it. See `../../references/stops.md`.

## Deterministic outputs

A triage run writes `run.json` (resolved host, dispatch order), `baseline.md`
(state before dispatch — useful even for a read-only run as a record of what
was examined), `decomposition.md` (the sweep/classify/rank lane plan as
dispatched), `lanes/sweep.md`, `lanes/classify.md`, and `lanes/rank.md` each
holding their brief and normalized result verbatim, and
`evidence/<nn>-<label>.txt` for every stored inventory and rationale. triage's
signature deliverable is the routing table itself, and it lives in
`handoff.md` — the file every orchestra workflow already uses to state what's
next — rather than a bespoke filename, since routing to the next workflow is
exactly what `handoff.md` exists to say; here it says it once per item
instead of once per run. `findings.md` is written only if `classify` surfaces
a genuine finding — a reachable precondition with stored evidence — while
reading an item, rather than merely a routing note. `verdicts.md` is not
used: triage dispatches no `judge`. Full layout:
`../../references/run-ledger.md`.

## Failure and recovery

A `partial` result from `sweep` blocks `classify` and `rank` from treating
the inventory as complete: either extend the sweep, redispatch capped at
three times (`reopenCount` in `run.json`), or narrow the declared scope and
say so explicitly in the routing table's coverage note — never rank a set
that was never fully swept as though it were.

An item `classify` cannot resolve is labeled `needs scoping`, not forced into
a destination. If `rank` finds a `classify` entry insufficient to order — for
example, missing the blast-radius detail a ranking rationale needs — `rank`
returns `blocked` on that item requesting reclassification rather than
guessing at its place in the order; redispatch `classify` for that item,
capped at three redispatches before it becomes a human escalation instead of
another retry.
