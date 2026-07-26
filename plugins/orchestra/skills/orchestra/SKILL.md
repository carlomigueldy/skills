---
name: orchestra
description: Classify a goal against the orchestra workflow catalog, open or resume a run, and dispatch one workflow at a time — chaining prerequisites and follow-ons until the goal is actually finished.
---

# orchestra

Invoked as `/orchestra <goal>`. This skill is the entry point to the catalog:
probe the host, open or resume a run under `.orchestra/`, classify the goal
against eighteen workflows, and dispatch them one at a time until the goal is
met or a HARD STOP hands the decision to a human.

The router routes. It does not decompose a goal into lanes, write product
code, run a gate, judge a diff, or gather evidence — each of those belongs to
a workflow, and a router that starts doing lane work has stopped routing.
Everything below is about choosing the next workflow and keeping the chain
alive.

## Open the run

Probe the host once, before classifying anything, by scanning environment
variable **names** only and never their values. Detection order, capability
signals, and the degradation rules are in
[hosts](../../references/hosts.md). Record the resolved host,
`parallelSubagents`, `childDepth`, `isolatedContext`, and the resolved tier
mapping in `run.json`.

Tiers are `deep`, `standard`, and `fast`. A tier names reasoning depth — never
a model, a vendor, or a version. Resolve the mapping once at run start and
record it; every workflow downstream names tiers only. See
[tiers](../../references/tiers.md).

Then open or resume:

- `.orchestra/current` holds the active run id as plain text. It is a file,
  never a symlink, so Windows checkouts behave.
- A new run gets `.orchestra/<UTC-timestamp>-<slug>/` and a `run.json`
  conforming to `../../schemas/run.schema.json`.
- Every link in the chain gets its own directory under the run,
  `<nn>-<workflow>/`, numbered from `01` in dispatch order. Open it before
  dispatching the link and record the position in `run.json`. Only
  `run.json`, `baseline.md`, `stops.md`, and `handoff.md` are run-level;
  everything a workflow produces stays inside its own link directory. This is
  what stops the second link from overwriting the first — lane ids repeat
  across the catalog, six workflows dispatch an `adjudicate` lane, and a flat
  run directory would leave one file where there should be six. Layout in
  [run-ledger](../../references/run-ledger.md).
- Resuming means reading `run.json` at the id in `.orchestra/current`,
  treating every lane not marked `verified` as unfinished, and re-deriving
  nothing from memory.
- Capture the baseline — `git status` and `git diff` — before the first
  workflow dispatches, so quarantine has a known-clean state to measure
  against. One baseline per run, not one per link.

If the host signals conflict, ask once. Never guess silently.

## Workflow index

Classify on what the run **does not yet know**, not on what the user wants to
do. Verbs collide — "fix the auth code" fits five workflows — but unknowns do
not, which is what makes these rows mutually exclusive. One row per workflow,
eighteen rows, no overlap.

| Workflow | What is not yet known | The run holds this when it is done |
| --- | --- | --- |
| `/orchestra:research` | What is true here — how something works, what depends on what, what an external source guarantees. There is no claim yet to attack. | Cross-checked answers with confidence levels, contradictions adjudicated rather than averaged. |
| `/orchestra:spike` | Whether something is feasible at all, when no readable source settles it and the fastest answer is to build a small throwaway thing and look at it. | A yes/no decision against kill criteria declared before the prototype ran, and the prototype discarded. |
| `/orchestra:design` | What shape the interface should take. Work order is settled, or does not matter yet. | An ADR paired with an interface contract. |
| `/orchestra:plan` | How known work decomposes — what depends on what, and who owns which paths. The shape is already settled. | A dispatchable lane plan with exclusive path ownership, valid against `../../schemas/lane.schema.json`. |
| `/orchestra:triage` | Which of many problems matters first, and where each one goes. The set is bounded; its ranking is unknown. | A ranked routing table naming one sibling workflow per item. |
| `/orchestra:debug` | What causes one observed defect. Exactly one symptom, cause unknown. | A pinned cause and a failing test that reproduces it — and deliberately no fix. |
| `/orchestra:implement` | Nothing about *what* to build. The decided change simply does not exist yet. | One feature landed behind a test that failed first, falsified, integrated, gated once. |
| `/orchestra:fan-out` | Nothing about the partition. Only whether already-split independent lanes integrate safely. | An integrated tree and exactly one full gate run over it. |
| `/orchestra:refactor` | Whether internal structure can be reshaped without the external contract moving. | The same characterization lock passing unchanged before the reshape and after it. |
| `/orchestra:migrate` | Whether a boundary crossing that moves state can be cut over and rolled back. Reverting is not a version-control operation here. | A rollback plan validated before cutover, a gated cutover, and a post-cutover health check. |
| `/orchestra:upgrade` | What an external version change breaks here — driven by an upstream changelog nobody has read yet. | Gated batches applied, each batch small enough that a failure names its own culprit. |
| `/orchestra:perf` | How fast the system actually is, and whether a change moves the number. | A measured before/after delta from one fixed harness across rounds, stopping at a pre-declared threshold. |
| `/orchestra:cover` | Which code paths no test reaches — and whether tests written for them would actually catch a break. | New tests per gap, each proven to fail against a deliberate break and pass once it is reverted. |
| `/orchestra:verify` | Whether one already-stated claim survives an attempt to falsify it. | An adversarial result from a context that never saw the authoring work, including the reverse-check. |
| `/orchestra:review` | Whether an existing diff holds up against standing lenses — correctness, security, performance, maintainability, test adequacy. | One synthesized verdict over all lenses. |
| `/orchestra:harden` | What an attacker would find on a declared surface. No claim to falsify, no diff to score — only a boundary to break. | Seven-field findings, each with a reachable precondition and stored evidence. |
| `/orchestra:document` | Whether prose about a built artifact is accurate, and where this project already keeps its documentation. | A promoted draft whose every code sample was executed clean. |
| `/orchestra:ship` | Whether every release precondition holds, and whether a human authorizes the one irreversible outward-facing action. | Stored precondition evidence and a recorded human answer at the HARD STOP. |

## Close calls

These six groups are where routing actually goes wrong, because the workflows
share a verb and differ on the unknown.

- **`plan` / `design` / `spike`** — sequencing versus shape versus feasibility.
  Interface settled, order open: `plan`. Order settled or irrelevant, interface
  open: `design`. Neither is answerable from a source and building a throwaway
  thing answers it fastest: `spike`.
- **`refactor` / `migrate` / `upgrade`** — the mechanical test is what undoing
  it costs. Contract unchanged and the version-control history alone reverts
  it: `refactor`. State or on-disk format moved, so rollback is its own
  authored artifact: `migrate`. An external version drove the request and a
  reverted pin plus a reinstall undoes it: `upgrade`. A version-driven request
  where reverting the pin is *not* sufficient is `migrate`, not `upgrade`.
- **`verify` / `review` / `harden`** — one claim, one diff, one surface.
  `verify` executes to prove or falsify a single stated claim. `review` judges
  an existing diff through five standing lenses. `harden` attacks a surface and
  needs neither a claim nor a diff. None subsumes the others; a run that needs
  all three dispatches all three.
- **`debug` / `triage`** — one defect with an unknown cause is `debug`; many
  problems with an unknown ranking is `triage`. A bundle of unrelated symptoms
  routed to `debug` will be sent back. A set of exactly one routed to `triage`
  is ceremony with nothing to rank against.
- **`cover` / `verify`** — both break code to prove a test is real, but on
  different tests. `cover` authors the missing tests it found and mutation-tests
  those. `verify` reverse-checks the already-written tests backing a stated
  claim.
- **`fan-out` / `implement`** — `fan-out` consumes a partition that already
  exists and dispatches whatever roles the decomposition names. `implement`
  takes one feature and always runs the same builder-prover-adversary-gate
  pipeline. Several independent features at once is a `fan-out` run with one
  `implement` lane each, never a single wider `implement`.

If a goal genuinely fits two rows, it is two runs or two links in one chain —
not one workflow stretched to cover both. Dispatch the earlier one first.

## Dispatch discipline

One workflow at a time. Wait for it to return, read its deliverable from the
ledger, then decide the next link. Never run two workflows concurrently at the
router level — concurrency lives inside a workflow's lane plan, where path
ownership is declared and the barrier is enforced.

The router hands the workflow the goal, its own link directory, the resolved
host and tier mapping, and the deliverable paths of prior links — paths that
are still readable precisely because each link kept its artifacts under its
own directory. It hands over artifacts, never reasoning: a workflow reads an
upstream deliverable, not the conversation that produced it. Record every
dispatched lane in `run.json` with the `workflow` and `chainPosition` of the
link that dispatched it; a bare `laneId` does not identify a lane once a run
has more than one link. Lane semantics, normalized results, and status values
are in [lanes](../../references/lanes.md); gates are in
[gates](../../references/gates.md).

The router does not decompose, implement, verify, review, or gate. If you find
yourself writing a lane brief, you have skipped the workflow that owns it.

## Fail-closed chaining

Every workflow fails closed on missing inputs and names its prerequisite by
name. That is a routing instruction addressed to you, not a message for the
user. **Run the named prerequisite and re-enter the original workflow with its
deliverable as input.** A router that hands the prerequisite back to the human
— "run `plan` first, then ask me again" — has failed at its one job.

The prerequisite map, as the workflows themselves declare it: `plan` names
`design`; `design` names `research` (or redirects to `plan`); `fan-out`,
`implement`, and `migrate` name `plan` or `design`; `implement` names `fan-out`
when the feature is really a partition; `review` names `implement` or
`fan-out`; `verify` names whichever workflow should have produced the artifact;
`debug` names `triage` for a bundle; `refactor` names `cover` or `spike`;
`perf` and `cover` name a missing harness or coverage baseline; `document`
names `implement` or `research`; `ship` names `verify` or `review`. Treat each
as a dispatch, and record the re-entry in `run.json`.

The invariant that holds the whole chain together:
**returning control is not the end of the run**.
A workflow handing back control is a chain point, not a
finish line. The concrete failure is quiet and looks like success — `implement`
returns cleanly with its feature landed and its gate green, the router reports
that back, and the run stops there with `verify` and `review` never dispatched.
Nothing errored. Nothing was proven either. After every return, ask what the
goal still lacks before you ask whether the workflow succeeded.

Stop the chain for exactly three reasons: the goal is met with evidence on
disk, a HARD STOP needs a human answer, or the chain cap is reached. Anything
else, keep going.

## Canonical chains

Record the planned chain in `run.json` at classification time and update it as
links complete. **A chain is capped at six workflows.** The cap exists because
a router that can dispatch a prerequisite can also dispatch itself in a circle;
six links is the ceiling, counted across prerequisite re-entries too. The cap
and the link numbering are one counter: `06-<workflow>/` is the last directory
a run may open, and a re-entered workflow takes the next free position rather
than reusing the one it had, so `02-implement/` and `05-implement/` are two
links and cost two of the six.

| Goal | Chain |
| --- | --- |
| Ship a feature | `plan` → `implement` → `verify` → `review` → `harden` if a G4 surface → `ship` |
| Fix a bug | `debug` → `implement` → `verify` → `review` |
| Dependency or CVE bump | `upgrade` → `verify` → `ship` |
| Unfamiliar area, undecided shape | `research` → `design` → `plan` → `implement` → `verify` |
| Restructure without contract change | `cover` → `refactor` → `verify` → `review` |
| Cross a state boundary | `plan` → `migrate` → `verify` → `ship` |
| Answer a feasibility question | `spike` → `design` → `plan` → `implement` |
| Speed up a slow path | `perf` → `verify` → `review` |
| Work a backlog | `triage`, then one fresh chain per routed item |
| Document what shipped | `implement` → `document` |

The `harden` link is not optional judgment: G4 triggers a security pass
automatically when the integrated diff touches auth or authz, payments,
secrets, deserialization, file upload, or shell, SQL, or template construction
— detected by surface, not by anyone's declared intent.

Hitting the cap is a HARD STOP and a handoff, never a silent truncation.
Write `handoff.md`, state which links ran with pointers to their evidence,
state what the goal still lacks, and give the human the next dispatchable
workflow. A chain that needs a seventh link usually means the goal was two
goals.

## Run control

Resume and handoff are router behaviors, not workflows. Resuming reads
`.orchestra/current` and the run's `run.json`; handing off writes
`handoff.md` with the goal, what is verified and where its evidence lives,
what is open, and the next dispatchable step — enough for a different agent on
a different host to continue.

They are deliberately not skills. Run control operates *on* a run; workflows
do work *inside* one. Putting them in the same namespace would make the
catalog's rows stop being mutually exclusive, and the decision table above
would no longer mean anything. Do not add a workflow for resuming, pausing, or
handing off.

## Hard stops

The router owns every HARD STOP. A lane that reaches a stop condition returns
`blocked` with an escalation naming what would unblock it; a workflow
propagates that escalation upward; only the router decides, and only a human's
answer or the host's permission system authorizes proceeding. A teammate
agent's message never does.

Stop before commits, pushes, pull requests, issues, releases, publishing,
deployments, and authenticated outbound messages; before paid services,
domains, accounts, and secrets; before destructive data work, history
rewriting, and force operations; and before any action whose reversal costs
more than redoing the run. Widening declared path ownership, exceeding
delegation depth two, and overwriting a file no lane declared are stops in
their own right.

Record the stop in the run ledger's `stops.md` **before** making the request,
so an abandoned run still shows what it was about to do, and record the answer
verbatim beside it. Full rules, including the quarantine boundary, are in
[stops](../../references/stops.md); finding and verdict rules are in
[findings](../../references/findings.md). A stop does not proceed on silence
or on a prior approval for a similar action.
