---
name: document
description: Draft documentation for a discovered project location, execute every code sample as evidence, and promote the draft only after every sample runs clean.
---

# document

Shape: fan-out barrier

You are the ROOT ORCHESTRATOR for this run. Do not implement inline:
document decomposes a documentation request into a location-discovery lane
and a drafting lane, holds a barrier, then dispatches an independent
execution lane that runs every code sample the draft contains before any of
it is promoted out of the run ledger. A documentation claim is a claim like
any other and needs evidence — evidence-before-completion applies to prose
exactly as it applies to code.

document does not own writing the product code it describes — that is
`implement`'s job, finished before document runs — and it does not own
adversarially proving a claim about behavior; a documentation draft that
needs that level of scrutiny dispatches `verify` on the specific claim
rather than document absorbing falsification here. document's only original
contribution is the draft and the promotion gate that guards it.

## Required inputs

document fails closed. It requires the artifact being documented — a diff,
a shipped feature, a module — named with a pointer, normally the
deliverable of `implement` or a `research` lane. A request to "write some
docs" with nothing named to document about is not dispatchable; name the
artifact first rather than inventing a topic.

It does not require the output location up front: discovering where this
project already keeps its documentation is `document`'s own wave-0 job, not
a prerequisite the caller supplies. The one fixed exception is
documentation about orchestra itself, which lives under `docs/orchestra/`
in orchestra's own repository regardless of what discovery finds elsewhere.

## Lane plan

| Lane | Role | Tier | Access | Owns | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `discover-location` (wave 0) | `scout` | fast | read_only | none | the project's existing documentation convention — directory, file, or a stated absence of one — reported with pointers; zero conventions found is reported as zero, not skipped |
| `draft` (wave 0) | `builder` | standard | write | `.orchestra/<run>/<nn>-document/draft/` only | a complete draft answering the requested scope, written under this link's ledger directory and nowhere else yet |
| `drift` (wave 1, depends on `draft`) | `prover` | standard | execute | none | every code sample in the draft executed verbatim, raw output stored per sample; one sample that will not run fails the run, full stop |

`discover-location` and `draft` run concurrently — the draft's content does
not depend on knowing the final path, only its eventual placement does.
Promotion is not a lane: once `drift` returns `verified` with every sample
passing, you — the root — copy the draft to the location
`discover-location` found and record the destination in `handoff.md`, the
same way `fan-out` integrates wave-0 deliverables itself rather than
delegating the merge.

## Delegation contract

You dispatch at depth one. Maximum delegation depth is two, and `mechanic`
is the only role a lane may legally dispatch at depth two — `draft` may
hand a repetitive formatting pass across its own drafted files to a
`mechanic` confined to `.orchestra/<run>/<nn>-document/draft/`, and no lane
may dispatch any other role.

One writer per path, declared before dispatch (G7): `draft` owns
`.orchestra/<run>/<nn>-document/draft/` exclusively during wave 0, and the
promotion
destination is recorded as soon as `discover-location` returns, before any
write happens there, even though the write itself is the root's act rather
than a lane's.

On a host that cannot dispatch parallel subagents, document degrades to a
sequential fresh-context role-pass: `discover-location` and `draft` run one
at a time in a fresh context each, in either order since neither depends on
the other, then `drift` runs last in its own fresh context reading only the
stored draft, never draft's reasoning about it. Record the resolved
scheduler in `run.json` per `../../references/hosts.md`; the lane plan does
not change with the scheduler.

## Quality gates

G1 does not bind `draft` in its usual sense — prose is not product code,
and document has no "failing test" to write before the first sentence
exists. The equivalent discipline lands on `drift` instead: no sample is
presumed correct until an independent lane has executed it, which is the
same evidence-before-implementation instinct G1 encodes for code, applied
to prose. G9 is the gate this workflow exists to enforce at the sample
level: a draft where every sample looks correct on inspection is not a
draft where every sample runs, and only `drift`'s stored, independent
execution counts toward promotion — a rerun after a fix replaces the prior
record, it does not sit alongside it. G4 triggers a security pass when the
documented surface touches auth or authz, payments, secrets,
deserialization, file upload, or shell, SQL, or template construction — a
setup guide that prints a real credential is a G4 finding, not a style
note. Full definitions: `../../references/gates.md`.

## Evidence and completion

Evidence, not assertions: `drift`'s per-sample raw output under
`.orchestra/<run>/<nn>-document/evidence/` is the completion evidence, and a
`verified` status on `drift` with no evidence entry for every sample in the
draft is a failure of that lane, not a formality to fix later. `draft`
itself reaching `verified` means the draft is complete and internally
consistent — it does not mean any sample has run; only `drift` establishes
that.

## Hard stops

HARD STOP before every irreversible or outward-facing action; document
itself only ever writes local files under paths it controls — the run
ledger during wave 0, and the discovered documentation location at
promotion — and does not commit, push, or publish anything itself; that is
`ship`'s job, run separately and later, on the promoted result. Overwriting
a file at the discovered location that `discover-location` did not point at
is a stop in its own right, the same way it is in `fan-out`. Record every
stop request in `stops.md` before making it. See `../../references/stops.md`.

## Deterministic outputs

A document run writes `run.json` (resolved host, capabilities, dispatch
waves, delegation depth), `baseline.md`, `decomposition.md` (the documented
scope and the discovered-location question, as dispatched), one
`lanes/<lane-id>.md` per lane holding its brief and normalized result
verbatim, `evidence/<nn>-<label>.txt` per stored sample execution,
`stops.md` for any stop request, and `handoff.md` stating the promoted
destination path, what is verified with evidence pointers, and any sample
still failing. `findings.md` is written only if `discover-location` or
`drift` produced a finding; document itself renders no verdict. Full
layout: `../../references/run-ledger.md`.

## Failure and recovery

A failing sample in `drift` blocks promotion outright: do not copy a draft
to the discovered location while any sample is unproven, and do not
substitute a passing paraphrase for the failing raw output. Reopen `draft`
to fix the specific sample `drift` implicates, capped at three
redispatches (`reopenCount` in `run.json`); a fourth failure on the same
sample is a human escalation, not another retry.

If `discover-location` returns `blocked` — no convention found and no
existing location to extend — the run stops at that lane rather than
inventing a path; ask the human where documentation for this project
should live, and record the answer as the destination before `draft` or
`drift` proceed.
