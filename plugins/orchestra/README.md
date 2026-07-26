# Orchestra

Host-agnostic multi-agent orchestration for any codebase in any stack. Every
one of Orchestra's 19 skills turns the executing agent into a root
orchestrator: it decomposes the goal into lanes, dispatches each lane to a
role at a capability tier, gates on evidence rather than assertions, and
integrates verified results. **It never implements inline.**

Orchestra ships one router skill, `orchestra`, and 18 flat, bare-named
workflow skills — `plan`, `design`, `spike`, `fan-out`, `implement`, `verify`,
`review`, `debug`, `triage`, `research`, `refactor`, `migrate`, `upgrade`,
`harden`, `perf`, `cover`, `document`, `ship`. They share a common contract
defined in `references/` (lanes, tiers, hosts, gates, findings, the run
ledger, hard stops), role briefs in `roles/`, JSON Schemas for lanes,
findings, verdicts, and runs in `schemas/`, and worked lane-plan fixtures in
`examples/lanes/`.

Invoke the router with `/orchestra` on Claude Code or `$orchestra` on Codex
CLI to classify a goal and chain the right workflow. Once you know which
workflow applies, invoke it directly: `/orchestra:<name>` on Claude Code
(e.g. `/orchestra:fan-out`), `$<name>` on Codex CLI (e.g. `$fan-out`).

## Workflows

Each workflow resolves one kind of not-knowing. Pick the row that matches
what's actually uncertain, not the row whose name sounds closest.

### Entry point

| Skill | Resolves |
| --- | --- |
| `orchestra` | Which of the other 18 apply — and in what order — is itself unknown until the goal is classified. Opens or resumes a run and dispatches one workflow at a time until the goal is actually finished. |

### Direction — before any code exists

| Skill | Resolves |
| --- | --- |
| `plan` | The interface is already settled (or doesn't matter yet); the order dependent work happens in is not. |
| `design` | The order is already settled (or doesn't matter yet); the interface's shape is not. |
| `spike` | Feasibility is unanswerable from any existing source; the fastest way to settle it is a small throwaway build. |
| `research` | What's true here is unknown — how something works, what depends on what, what a source guarantees — with no claim yet to attack. |

### Building — the target is already decided

| Skill | Resolves |
| --- | --- |
| `implement` | The change doesn't exist yet. Builds one feature through a fixed pipeline — failing test, execution evidence, falsification, integration, one gate run — the same sequence regardless of the feature. |
| `fan-out` | The partition is already decided; that's a required input, not something this workflow figures out. What's unproven is whether the already-split, independent lanes integrate safely into one gated whole — the raw barrier-and-integrate primitive other workflows cite rather than re-deriving. |

### Verification

| Skill | Resolves |
| --- | --- |
| `verify` | Whether one already-stated claim survives an attempt to falsify it, in a context that never saw the authoring work. |
| `review` | Whether an existing diff holds up against five standing lenses — correctness, security, performance, maintainability, test adequacy. |
| `harden` | What an attacker would find on a declared surface — no claim to falsify, no diff to score, only a boundary to break. |
| `cover` | Which code paths no test reaches, and whether a test written for one would actually catch a break — proven by deliberately breaking the code and confirming the new test fails, then passes again once the break is reverted. |

### Diagnosis

| Skill | Resolves |
| --- | --- |
| `debug` | One defect, cause unknown. Escalates through cheap reproduction, scoped analysis, and deep hypothesis work to pin the cause with a failing test — and stops there, handing the fix to `implement`. |
| `triage` | Many reported problems, ranking unknown. Sweeps the set, classifies and ranks it, and emits a routing table naming a sibling workflow per item — it fixes nothing itself. |
| `perf` | Whether the system is fast enough, and whether an attempted change actually moves the number — proven by repeated before/after rounds against one fixed harness, not by inspection. |

### Structural change

| Skill | Resolves |
| --- | --- |
| `refactor` | What undoing the change costs: nothing, because the external contract is unchanged and version-control history alone reverts it. |
| `migrate` | What undoing the change costs: a rollback plan of its own, because state or an on-disk format actually moved. |
| `upgrade` | What undoing the change costs: a reverted pin and a reinstall, because an external dependency's changelog — not internal intent — drove the request. |

### Closing out

| Skill | Resolves |
| --- | --- |
| `document` | Where finished work's documentation belongs is unknown. Discovers the project's own convention itself — or stops and asks, never inventing a path — and promotes a draft only once every code sample in it has executed clean. |
| `ship` | Whether every release precondition holds, and whether a human actually authorizes the one irreversible, outward-facing action — proving every precondition is only permission to ask, never permission to proceed. |

### Choosing between look-alikes

`plan`, `design`, and `spike` are commonly confused because they all precede
code. The discriminator is mechanical: interface settled, order open —
`plan`. Order settled or irrelevant, interface open — `design`. Neither is
answerable from a source, and building a small throwaway thing answers it
fastest — `spike`.

`refactor`, `migrate`, and `upgrade` are commonly confused because they all
change existing code without adding a feature. The mechanical test is what
undoing it costs: contract unchanged and version-control history alone
reverts it — `refactor`. State or an on-disk format moved, so rollback is
its own authored artifact — `migrate`. An external version drove the request
and a reverted pin plus a reinstall undoes it — `upgrade`, unless reverting
the pin isn't sufficient, which makes it `migrate` after all.

`verify`, `review`, and `harden` are commonly confused because they all check
work someone else did. `verify` executes to prove or falsify one
already-stated claim. `review` judges a diff through five standing lenses —
correctness, security, performance, maintainability, test adequacy — with no
single claim to falsify. `harden` attacks a surface the way an adversary
would; it needs neither a claim nor a diff, only a boundary to break. None
subsumes the others — a run that needs all three dispatches all three.

`debug` and `triage` are commonly confused because they both start from
"something is wrong." `debug` is one defect with an unknown cause, and it
explicitly does not fix what it finds — it stops at a pinned cause and a
failing test, and hands off to `implement`. `triage` is many reported
problems with an unknown ranking, and it fixes nothing itself either — its
product is a routing table, not a change to the terrain. A bundle of
unrelated symptoms sent to `debug` gets redirected to `triage`; a set of
exactly one sent to `triage` is ceremony with nothing to rank against.

`cover` and `verify` are commonly confused because they both break code to
prove a test is real — but on different tests. `cover` authors the tests a
surface is missing and mutation-tests those: deliberately break the code
each new test claims to cover, confirm the test fails, then confirm it
passes again once the break is reverted. `verify` reverse-checks the
already-written tests backing a stated claim, proving they'd actually fail
if the behavior they cover were removed. Neither one runs the other's tests.

`fan-out` and `implement` are commonly confused because they both build
already-decided work. `fan-out` consumes a partition that already exists and
dispatches whatever roles the decomposition calls for, whatever they are.
`implement` takes one feature and always runs the same
builder-prover-adversary-gate pipeline, regardless of what the feature is.
Shipping several independent features at once is a `fan-out` run with one
`implement` lane per feature, never a single wider `implement`.

## Roles and tiers

Every lane is assigned exactly one of 8 roles and exactly one of 3 tiers —
`deep`, `standard`, `fast`. A tier names reasoning depth, never a model, a
vendor, or a version: the mapping from tier to a host's actual setting is
resolved once at run start and recorded in `run.json`, so the same lane plan
runs unmodified on any host. See `references/tiers.md` for the full
escalation rules and `roles/<role>.md` for each role's brief.

| Role | Tier | Mode | Delegates |
| --- | --- | --- | --- |
| `scout` | fast | read_only | no |
| `analyst` | standard | read_only | no |
| `architect` | deep | read_only | no |
| `builder` | standard | write | to `mechanic` only |
| `prover` | standard | execute | no |
| `adversary` | standard | read_only | no |
| `judge` | deep | read_only | no |
| `mechanic` | fast | write | no — terminal |

`builder` is the only role that writes product code. `mechanic` is the only
role dispatchable at depth two, which is what makes the maximum delegation
depth of two mechanical rather than aspirational. `adversary` never runs in
the context that authored the work it examines — see Hosts below for what
happens when a host can't guarantee that.

## Hosts and degradation

Orchestra installs on Claude Code, Codex CLI, OpenCode, and Grok Build. Host
detection happens once, before any dispatch, by scanning environment variable
names only — never their values — and the result, along with the host's
capabilities and the tier mapping, is recorded in `run.json`. See
`references/hosts.md` for the exact detection order.

Delegation degrades by scheduler, never by outcome. A host that can dispatch
parallel subagents runs a wave of lanes concurrently; a host that can't runs
the same lanes as a sequential fresh-context role-pass, each one reading an
earlier lane's artifact and never its reasoning. The lane plan and the gates
never change — only how fast the scheduler gets through them. A host never
runs fewer lanes and never skips verification because it can't parallelize.

One capability cannot degrade: adversary isolation. When a host can't give
the `adversary` role a context that never saw the authoring work, the run
records `isolation: degraded` in `run.json` and the verdict is capped at
`unverified` — never `approve`.

## The run ledger

Every run writes to `.orchestra/`, gitignored via `.git/info/exclude` and
never packaged into a plugin or release artifact. `.orchestra/current` names
the active run; each run lives in `.orchestra/<UTC-timestamp>-<slug>/`
holding `run.json`, `baseline.md`, `decomposition.md`, `lanes/<lane-id>.md`,
`evidence/<nn>-<label>.txt`, `findings.md`, `verdicts.md`, `stops.md`, and
`handoff.md`.

The ledger is written as the run proceeds, which is what makes a run
resumable: re-read `run.json`, treat every lane not marked `verified` as
unfinished, and re-derive nothing from memory. `handoff.md` states the goal,
what's verified with pointers to evidence, what's open, and the next
dispatchable lane — enough for a different agent on a different host to pick
the run up. See `references/run-ledger.md` for the full layout.

## Quality gates

Gates are not advisory. A gate that can't be evaluated fails closed, and no
lane waives a gate that benefits from being waived. Full text in
`references/gates.md`.

| ID | Gate |
| --- | --- |
| G1 | Tests precede implementation. |
| G2 | Evidence, not assertions — an unstored claim is a failure. |
| G3 | Adversarial verification runs in a context that never saw the authoring work. |
| G4 | A security pass triggers automatically on auth, payments, secrets, deserialization, file upload, and shell/SQL/template construction. |
| G5 | No scope creep — a lane's diff is a subset of its declared paths. |
| G6 | Maximum delegation depth is two. |
| G7 | One writer per path, declared before dispatch. |
| G8 | Hard stop before every irreversible or outward-facing action. |
| G9 | N green lanes are not a green whole — the full repository gate runs once, after integration, and only that run counts. |

G9 is the gate most often skipped in practice and the one that matters most:
lane results are inputs to integration, never a substitute for it.

## Safety and portability

Orchestra runs autonomously inside the workspace — local, reversible work
proceeds without asking. It hard-stops before every irreversible or
outward-facing action (commits, pushes, pull requests, releases, deployments,
paid services, and the like) to request approval first; see
`references/stops.md` for the complete list and what a stop request must
state. Delegation degrades gracefully by host, as above, never by skipping a
lane or a gate.

Run `python3 scripts/validate_orchestra.py` to validate the packaged contract
before publishing.
