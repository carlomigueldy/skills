---
name: migrate
description: Cross a state or contract boundary through gated stages — assess, author and validate a rollback plan, cut over, and confirm health — hard-stopping at every stage boundary because rollback here is not git revert.
---

# migrate

Shape: staged escalation

You are the ROOT ORCHESTRATOR for this run. Do not implement inline: migrate
crosses a boundary with a cutover — a schema change, a data move, a platform
or protocol switch — through named stages of increasing consequence:
boundary assessment, a rollback plan authored and validated, the cutover
itself, and a post-cutover health check. Each stage promotes to the next only
on a stated condition, and the boundary between stages is a HARD STOP in its
own right, not just the end of the run.

State plainly what makes migrate different from a plain restructuring:
rollback is not `git revert` here. Data or state has already moved by the
time a problem is discovered, so the rollback plan is its own declared
artifact, written and validated before the cutover stage ever runs — not
improvised afterward. migrate does not decide whether the contract should
change at all — that's `plan` or `design`'s job, upstream of this workflow.
migrate does not perform a revertable in-place restructuring either — that's
`refactor`, and if the boundary this request describes turns out to be
revertable by the version-control history alone, with no state moved, stop
and name `refactor` instead; migrate's stage-gate ceremony is wasted overhead
on a change git could already undo. migrate also does not provide the
adversarial proof that a completed cutover holds under attack — that's
`verify`, dispatched as the workflow that follows a successful cutover, not
reimplemented here.

## Required inputs

migrate fails closed. It requires the boundary named explicitly: what state
or contract moves, from which shape to which, and every consumer on either
side. It requires access to a representative copy of the state — a staging
snapshot, a seeded fixture — to validate the rollback plan against; without
one, the rollback cannot be proven before cutover, and migrate stops rather
than proceeding on an unvalidated plan.

If the change turns out not to move any state — reverting it would just be
`git revert` — stop and name `refactor`. If the request is "adopt this new
system" with the target contract still undecided, stop and name `plan` or
`design` and return once the target shape is fixed.

migrate also requires a captured baseline — `git status` and `git diff` —
before any lane starts. See `../../references/run-ledger.md`.

## Lane plan

Four named stages, each gated behind the promotion condition stated after the
table. Stage 3 dispatches only after a human authorizes it at a HARD STOP,
regardless of how clean Stages 1 and 2 were.

| Lane | Role | Tier | Stage | Access | Owns | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| `boundary-sweep` | `scout` | fast | 1 — boundary assessment | read_only | none | every read/write path, consumer, and external contract crossing the declared boundary, each with a pointer, plus an explicit count |
| `boundary-synthesis` | `analyst` | standard | 1 — boundary assessment | read_only | none | the swept inventory resolved into one scoped description of what moves from the old shape to the new and what depends on each side |
| `rollback-plan` | `analyst` | standard | 2 — rollback plan authored and validated | read_only | none | a named, ordered procedure restoring pre-migration state or contract — explicitly not `git revert` — naming every step and the tool or script it runs |
| `rollback-validate` | `prover` | standard | 2 — rollback plan authored and validated | execute | none | the rollback procedure executed against a representative copy of the state, never the production boundary itself, with raw output proving prior state is restored |
| `cutover` | `builder` | standard | 3 — cutover, HARD STOP before dispatch | write | the migration script(s) and compat shim(s) declared for this boundary | the boundary crossing applied exactly as assessed, raw output stored (row counts, tool logs), diff confined to declared paths |
| `cutover-health` | `prover` | standard | 4 — cutover health check | execute | none | a go/no-go smoke check against the new boundary with raw output; `verified` is go, anything else is no-go and names the validated rollback as the next action |

Promote Stage 1 to Stage 2 only when `boundary-synthesis` is `verified`
complete, not `partial` — writing a rollback plan against an unknown scope is
unsafe. Promote Stage 2 to Stage 3 only when `rollback-validate` is
`verified` with stored evidence that reversal actually works; this promotion
is itself a HARD STOP — cutover does not dispatch on a written-but-unproven
rollback plan, and the human's authorization is what releases it, not a
clean Stage 2 result on its own. Promote Stage 3 to Stage 4 only when
`cutover` itself is `verified`. Stage 4's outcome is the run's decision
point: go means stop and recommend `verify` next for adversarial confirmation
that the cutover holds; no-go triggers the validated rollback, itself gated
behind a fresh HARD STOP (see Failure and recovery).

## Delegation contract

You dispatch at depth one. Maximum delegation depth is two, and `mechanic` is
the only role a lane may legally dispatch at depth two — `cutover` may hand a
`mechanic` a repetitive, already-specified edit confined to its own declared
paths (see `../../roles/mechanic.md`); no lane may dispatch any other role.

One writer per path, declared before dispatch (G7): `cutover` is migrate's
only write lane in the normal path, and its declared paths are exactly the
migration scripts and shims named in the assessment, nothing wider.

On a host that cannot dispatch parallel subagents, migrate degrades to a
sequential fresh-context role-pass: the same four stages, in the same order,
run one lane at a time in a fresh context each — never fewer stages, never
merged. A later lane reads an earlier stage's stored artifact — the rollback
plan document, the assessment synthesis — never the reasoning that produced
it. Record the resolved scheduler in `run.json` per
`../../references/hosts.md`.

## Quality gates

G8 is the gate this workflow leans on hardest: every stage boundary is a HARD
STOP, not just the run's end. G1 applies to `cutover` where it writes code —
a pre-migration integrity check, captured before the crossing, stands in for
the "failing test" that must exist before the change lands. G2 binds every
stage's evidence, most critically `rollback-validate`'s proof that reversal
works — a rollback plan with no dry-run output is a document, not a validated
plan. G4 triggers automatically when the boundary touches auth or authz,
payments, secrets, deserialization, file upload, or shell, SQL, or template
construction; boundary crossings touch these surfaces often enough that this
check is not optional. G5 and G7 bind `cutover`'s declared paths mechanically.
G6 caps delegation depth as above. Full definitions:
`../../references/gates.md`.

G9 applies after `cutover`, but note what it does and does not prove: the
full-repository gate confirms the code integrates, not that the data
migrated correctly — that's `cutover-health`'s job, backed by
`rollback-validate`'s prior proof that a wrong result is recoverable. Do not
read a green G9 run as cutover success on its own.

## Evidence and completion

Evidence, not assertions: every stage's `verified` status requires at least
one evidence entry pointing at stored raw output under
`.orchestra/<run>/<nn>-migrate/evidence/`. `rollback-validate`'s dry-run
output and `cutover-health`'s go/no-go check are the two entries this run
cannot complete without — a `verified` status on either with no evidence
entry is a failure of that lane, not a formality to fix later.

## Hard stops

HARD STOP before every irreversible or outward-facing action, and never take
one inside a lane: a lane that reaches a stop condition returns `blocked`
with an escalation, and you own the decision. Every stage boundary in this
workflow is a stop in its own right — Stage 1 to 2, Stage 2 to 3, and the
no-go path from Stage 4 into the rollback all require a fresh answer, never a
prior approval carried forward from an earlier boundary. Widening `cutover`'s
declared paths, exceeding delegation depth two, and executing the rollback
without a fresh authorization are stops as well. Record every stop request in
`stops.md` before making it. See `../../references/stops.md`.

## Deterministic outputs

A migrate run writes `run.json` (resolved host, dispatch waves, which stage
boundary each stop request gated), `baseline.md` (the pre-dispatch `git
status` and `git diff`), `decomposition.md` (the four-stage plan as
dispatched, including each promotion decision), `lanes/<lane-id>.md` per lane
holding its brief and normalized result verbatim, `evidence/<nn>-<label>.txt`
for every stored artifact including the rollback dry run and the cutover
health check, `stops.md` with one entry per stage boundary at minimum, and
`handoff.md` stating whether the cutover succeeded, whether rollback fired,
and whether `verify` is the recommended next dispatch. `findings.md` and
`verdicts.md` are written only if a lane produced them. Full layout:
`../../references/run-ledger.md`.

## Failure and recovery

A `blocked` or `partial` result at any stage stops promotion — do not carry
an incomplete assessment into a rollback plan, and do not carry an unproven
rollback plan into cutover. If `cutover-health` reports no-go, execute the
validated rollback from Stage 2 rather than attempting a live forward-fix; a
forward patch applied mid-cutover is exactly the failure mode this workflow
exists to prevent, because it substitutes improvisation for the plan that was
proven safe in advance. Executing that rollback is itself a fresh HARD STOP,
even though the plan was authorized earlier — circumstances at execution time
may differ from when the plan was validated.

Redispatch a fixed stage at most three times (`reopenCount` in `run.json`); a
fourth failure on the same stage is a human escalation, not another retry.
After a rollback executes, the run has failed: return to a human decision on
whether to re-attempt from Stage 1 or abandon, rather than immediately
retrying the cutover.
