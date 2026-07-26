---
name: upgrade
description: Read the upstream changelog, classify each dependency's risk, batch upgrades so a failing batch names its own culprit, and apply them one gated batch at a time.
---

# upgrade

Shape: staged escalation

You are the ROOT ORCHESTRATOR for this run. Do not implement inline: upgrade
is driven by an external changelog, not by internal intent — the upstream
release notes for every dependency in scope are a required input, read before
any batching decision, never guessed at from memory of what a major version
"usually" breaks. Three named stages carry the run: changelog acquisition and
risk classification, batch construction, and batch application, one gated
batch at a time.

The whole point of batching is that a failure names its own culprit: one
dependency per batch where the changelog marks it high-risk, and dependencies
grouped into a shared batch only where their independence from every other
member was actually checked, not assumed for convenience. A batch large
enough that a failure can't be pinned to a specific dependency has defeated
the workflow, no matter how much faster it felt to build.

upgrade does not decide whether to adopt a new dependency at all — that's
`plan` or `design`'s job, upstream of this workflow. It does not perform an
internally-motivated restructuring with no external version behind it —
that's `refactor`, and if there is no changelog to read because there is no
new version to move to, stop and name `refactor` instead. It does not cross a
boundary where old state needs a declared rollback plan rather than a version
pin reverted — that's `migrate`; the distinguishing test is whether reverting
the dependency pin and reinstalling is sufficient to undo the change. If it
is not — if data or on-disk format moved — name `migrate` even though a
version number drove the request.

## Required inputs

upgrade fails closed. It requires the upstream changelog or release notes for
every in-scope dependency between its current and target version. If a
changelog cannot be obtained for a dependency — unpublished, a private
registry with no notes, network access unavailable — that dependency is
excluded from the run and named as blocked; upgrade does not guess at its
breaking changes from a version-number pattern or from memory.

It also requires the dependency manifest and lockfile in scope, and either
explicit target versions or an explicit "latest" instruction per dependency.
"Upgrade everything" with no scope and no reachable changelog is not
actionable — stop and name what's missing: a package list, registry access,
or a version ceiling.

upgrade also requires a captured baseline — `git status` and `git diff` —
before any lane starts. See `../../references/run-ledger.md`.

## Lane plan

Stage 1 classifies risk from changelogs; Stage 2 constructs batches from that
classification; Stage 3 applies batches one at a time, each gated
individually so a failure is attributable before the next batch starts.

| Lane | Role | Tier | Stage | Access | Owns | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| `changelog-sweep` | `scout` | fast | 1 — changelog acquisition and risk classification | read_only | none | the changelog or release notes fetched for every in-scope dependency, a pointer per dependency, and an explicit list of any dependency no changelog could be obtained for |
| `risk-classification` | `analyst` | standard | 1 — changelog acquisition and risk classification | read_only | none | every dependency with a changelog classified high-risk (breaking changes, a major bump, or a G4 surface) or low-risk, each classification traced to the changelog line that justifies it |
| `batch-construction` | `analyst` | standard | 2 — batch construction | read_only | none | every high-risk dependency assigned its own single-dependency batch; every low-risk dependency assigned to a shared batch only where independence from every other member was checked and named explicitly |
| `batch-apply-<n>` (one lane per batch, dispatched one batch at a time in ascending batch order) | `builder` | standard | 3 — batch application | write | the manifest/lockfile entries and any compat-shim code for that batch's dependencies only | the batch's version bump(s) applied; any changelog-flagged breaking behavior pinned by a test — red on the new version, green on the old — before the bump lands; diff confined to declared paths |
| `batch-gate-<n>` (one per batch, depends on its `batch-apply-<n>`) | `prover` | standard | 3 — batch application | execute | none | the full repository gate run once for this batch alone, raw output stored; a failure here implicates this batch's dependency or dependencies and no other |

Promote Stage 1 to Stage 2 once every in-scope dependency is either
classified or explicitly excluded as changelog-unobtainable — never promote a
dependency with no changelog into a batch by default. Promote Stage 2 to
Stage 3 once every batch's independence has actually been checked; a batch
whose independence was not checked is dissolved into single-dependency
batches rather than promoted as grouped — fail closed toward smaller batches,
since attribution is the entire point. Within Stage 3, promote from
`batch-apply-N`/`batch-gate-N` to batch N+1 only when batch N's gate is
`verified`; a failing gate stops the run there, and the culprit is batch N —
by construction, one dependency if it was high-risk.

## Delegation contract

You dispatch at depth one. Maximum delegation depth is two, and `mechanic` is
the only role a lane may legally dispatch at depth two — a `batch-apply-<n>`
lane with a repetitive post-bump fixup already specified, such as a renamed
API applied uniformly across call sites, may hand it to a `mechanic` confined
to that batch's own declared paths (see `../../roles/mechanic.md`); no lane
may dispatch any other role.

One writer per path, declared before dispatch (G7): every batch's declared
paths are disjoint from every other batch's, checked before Stage 3 starts,
which is what makes attributing a failure to one batch meaningful.

On a host that cannot dispatch parallel subagents, upgrade degrades to a
sequential fresh-context role-pass: Stage 1 and Stage 2's lanes run one at a
time in a fresh context each, and Stage 3's batches — already sequential by
design — are unaffected in order, only in scheduler. A later lane reads an
earlier lane's stored deliverable, never its reasoning. Record the resolved
scheduler in `run.json` per `../../references/hosts.md`.

## Quality gates

G1 applies to each `batch-apply-<n>` lane in its changelog-adapted form:
where the changelog names a specific breaking behavior the codebase relies
on, a test pinning current behavior is written and run red against the new
version before the bump lands, then green after — tests still precede the
change that matters, even though the change itself is a version bump rather
than new logic. G2 binds every stage: a classification with no changelog
pointer, or a batch gate with no stored raw output, is a failure of that
lane. G4 triggers automatically when a dependency touches auth or authz,
payments, secrets, deserialization, file upload, or shell, SQL, or template
construction — classify these high-risk regardless of what the changelog
itself emphasizes. G5 and G7 bind each batch's declared paths mechanically.
G6 caps delegation depth as above. Full definitions:
`../../references/gates.md`.

G9 is deliberately layered here: only the gate run after the final batch
integrates is the completion evidence that counts. Every earlier
`batch-gate-<n>` run is diagnostic — stored, load-bearing for attribution,
but never itself asserted as the finish line. N green batch gates plus one
final green gate is the whole a caller should trust; N green batch gates
alone is not.

## Evidence and completion

Evidence, not assertions: every lane's `verified` status requires at least
one evidence entry pointing at stored raw output under
`.orchestra/<run>/<nn>-upgrade/evidence/`, in dispatch order, un-collapsed —
the failing batch's gate run has to be distinguishable from the passing runs
before it, which means every batch's gate output is stored even when it
passed.

## Hard stops

HARD STOP before every irreversible or outward-facing action, and never take
one inside a lane: a lane that reaches a stop condition returns `blocked`
with an escalation, and you own the decision. Widening a `batch-apply-<n>`
lane's declared paths, applying two batches concurrently once either has
started, and exceeding delegation depth two are stops in their own right.
Record every stop request in `stops.md` before making it. See
`../../references/stops.md`.

## Deterministic outputs

An upgrade run writes `run.json` (resolved host, dispatch waves, the batch
plan and each batch's gate result in dispatch order), `baseline.md` (the
pre-dispatch `git status` and `git diff`), `decomposition.md` (the
changelog-derived risk classification and batch composition as dispatched,
not a later summary), `lanes/<lane-id>.md` per lane holding its brief and
normalized result verbatim, `evidence/<nn>-<label>.txt` for every changelog
fetch and every batch's gate run, `stops.md` for any stop request, and
`handoff.md` naming either the exact batch and dependency that stopped the
run or full completion with a pointer to the final gate's evidence.
`findings.md` and `verdicts.md` are written only if a lane produced them.
Full layout: `../../references/run-ledger.md`.

## Failure and recovery

A failing `batch-gate-<n>` stops the run at batch N — do not proceed to batch
N+1, and do not retry with a broader batch to push through faster; widening
the batch destroys the attribution the workflow exists to provide. Fix scoped
to the implicated dependency, redispatch capped at three times
(`reopenCount` in `run.json`). If even a single-dependency batch's failure
cannot be attributed to one specific breaking change — a transitive
dependency conflict, most commonly — that is below the workflow's atom size
and is a human escalation rather than a further split.

A fourth failure on the same batch is itself an escalation to the human, not
another retry.
