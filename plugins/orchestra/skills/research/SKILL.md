---
name: research
description: Fan out independent investigation lanes, including codebase cartography, then cross-check every claim across lanes and adjudicate contradictions instead of averaging them away.
---

# research

Shape: fan-out barrier

You are the ROOT ORCHESTRATOR for this run. Do not implement inline: your
role is to decompose an open question into independent investigation lanes,
dispatch them concurrently, hold a barrier until every lane returns,
reconcile what they found against each other, and adjudicate any
contradiction rather than picking the answer that reads cleanest. research
absorbs codebase cartography — what earlier tooling called explore, map, or
onboard — as one more investigation lane with the same shape and the same
`scout` deliverable: an exhaustive inventory with file-and-line pointers, not
a separate workflow.

research does not own falsifying a single already-stated claim under
attack — that is `verify`'s job, dispatched separately once research has
produced something concrete enough to falsify. It also does not decide what
to do with what it finds: a research run's output is an answer with
confidence levels, handed to `plan` or `implement`, never a change to the
repository itself.

## Required inputs

research fails closed. It requires a stated question or set of questions
scoped enough to partition — "how does X currently work," "which callers
depend on Y," "what does the target library's API guarantee" — each with a
boundary a lane can finish inside. A request that is really "go find out
everything interesting about this area" is not yet a partition; narrow it to
named questions before dispatch, the same way `fan-out` requires a
decomposition rather than inventing one from an unclear goal.

It also requires knowing what counts as a source in this context — the
repository, a named set of files, a running system, or an external
document — so every lane's claims can be pointed at something a reader can
check independently. A question with no admissible source is not
researchable; name what source would settle it and stop rather than
guessing.

## Lane plan

| Lane | Role | Tier | Access | Owns | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `cartography` (wave 0, when the question requires mapping unfamiliar code) | `scout` | fast | read_only | none | an exhaustive inventory of the declared surface, every entry with a file-and-line pointer, per `../../roles/scout.md` |
| `lane-<id>` (one per independent question, wave 0) | `analyst` | standard | read_only | none | a scoped synthesis answering exactly its question, every claim traced to a source pointer, per `../../roles/analyst.md` |
| `cross-check` (wave 1, depends on every wave-0 lane) | `analyst` | standard | read_only | none | every claim from every wave-0 lane reconciled against the others on the same subject; agreements and contradictions both named explicitly, with a confidence level per claim |
| `adjudicate` (wave 2, dispatched only when `cross-check` reports a contradiction) | `judge` | deep | read_only | none | a verdict naming which stored artifact settles each contradiction, or `unverified` naming the single check that would settle it |

A contradiction between two wave-0 lanes is itself a result, not noise to
resolve by preferring the more confident-sounding report. `cross-check`
names every disagreement it finds; it does not silently pick a side. Only
when a disagreement survives `cross-check`'s own reading of the evidence
does `adjudicate` run — most runs finish without it.

## Delegation contract

You dispatch at depth one; none of research's roles delegate further —
`scout`, `analyst`, and `judge` all have `canDelegate: false`. The rule
that Maximum delegation depth is two applies to research only insofar as
it never approaches it: research has no `mechanic` lane and nothing here
should ever reach depth two.

On a host that cannot dispatch parallel subagents, research degrades to a
sequential fresh-context role-pass: `cartography` and each `lane-<id>` run
one at a time in a fresh context, in any order since none depends on
another, then `cross-check` runs last in its own fresh context reading only
the stored deliverables, never the reasoning behind them. Record the
resolved scheduler in `run.json` per `../../references/hosts.md`; the
question set and the acceptance conditions do not change with the
scheduler.

## Quality gates

G2 is the gate research exists to enforce at the claim level: an unsourced
claim is not a result, in a synthesis lane or in cross-check's reconciliation
alike. G9 governs the reconciliation itself — N individually well-sourced
lanes are not a cross-checked finding-set, and the per-claim confidence
report is only complete once `cross-check` has run, never at the moment the
last wave-0 lane returns. G6 caps delegation depth as described above. G4
triggers a security pass on the integrated findings when the investigated
surface includes auth or authz, payments, secrets, deserialization, file
upload, or shell, SQL, or template construction, regardless of whether any
lane framed its question as a security question. Full definitions:
`../../references/gates.md`.

## Evidence and completion

Evidence, not assertions: every lane's claims carry a pointer into stored
evidence under `.orchestra/<run>/<nn>-research/evidence/` — a command's raw
output, a quoted file-and-line, or a named external source — and a `verified`
status with no evidence entry recorded against it is a failure of that lane,
not research being thorough on its behalf. `cross-check`'s reconciliation and
`adjudicate`'s verdict, when it runs, are the completion evidence for the
run as a whole.

## Hard stops

HARD STOP before every irreversible or outward-facing action; research
itself is read-only by construction and takes none, but a finding that
implies one — "this secret is exposed," "this dependency is
unmaintained" — is reported, not acted on. Widening a lane's declared scope
past what was dispatched and treating an assumption as a sourced claim are
stops in their own right, even mid-barrier. Record every stop request in
`stops.md` before making it. See `../../references/stops.md`.

## Deterministic outputs

A research run writes `run.json` (resolved host, capabilities, tier
mapping, dispatch waves, delegation depth), `baseline.md` (state before
dispatch), `decomposition.md` (the question set as dispatched), one
`lanes/<lane-id>.md` per lane holding its brief and normalized result
verbatim, `evidence/<nn>-<label>.txt` per stored artifact including
cross-check's reconciliation, `stops.md` for any stop request, and
`handoff.md` stating the answer with confidence per claim, what remains
unresolved, and the next dispatchable lane. `findings.md` and `verdicts.md`
are written only when a lane produced a finding or `adjudicate` ran. Full
layout: `../../references/run-ledger.md`.

## Failure and recovery

A wave-0 lane that returns `blocked` or `partial` breaks the barrier the
same way it does in `fan-out`: `cross-check` does not reconcile a question
that was never answered, and the gap is reported as open rather than
papered over with the lanes that did finish. Redispatch a fixed lane at
most three times (`reopenCount` in `run.json`); a fourth failure on the
same question is an escalation to the human, not another retry.

If `adjudicate` returns `unverified`, the disagreement stays open in
`handoff.md` naming the check that would settle it — research does not
force a resolution the evidence does not support, and a later run may pick
it up once that check becomes possible.
