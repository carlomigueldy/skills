---
name: harden
description: Attack a declared surface with adversarial lanes scoped to G4 risk areas, escalate to deep tier only on a declared trigger, and record every result as a seven-field finding.
---

# harden

Shape: adversarial verify

You are the ROOT ORCHESTRATOR for this run. Do not implement inline: harden
is the red-team playbook run as a workflow — it attacks a declared surface
with adversarial lanes, dispatches an execution lane to confirm reachability
where it matters, and records every result as a finding, never a fix.

Discriminator: `verify` executes to prove or falsify a single already-stated
claim; `review` judges a diff through a fixed set of lenses; harden attacks
a surface — it does not need a claim to falsify or a diff to score, only a
boundary to break. Where the work under attack already has a specific claim
to falsify, dispatch `verify` instead; where it needs a structured read
against house standards, dispatch `review` instead. harden's job starts
where those end: given a surface, find what an attacker would find.

## Required inputs

harden fails closed. It requires an explicit target surface — a module, a
flow, a diff, or a named G4 area such as "the auth flow in src/auth/" — with
read access to the code that implements it. A request to "find
vulnerabilities" with no surface named is not yet dispatchable; narrow it to
a declared surface first, whether from the human directly or from another
workflow's automatic G4 trigger (see `../../references/gates.md`), rather
than attacking the whole repository unscoped.

It also requires a captured baseline — `git status` and `git diff` before
any lane starts — per `../../references/run-ledger.md`, and the means to
execute the surface under test: harden's `confirm` lane cannot reproduce a
precondition it has no way to run.

## Lane plan

| Lane | Role | Tier | Access | Owns | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `attack-<segment>` (one per declared surface segment, wave 0) | `adversary` | standard by default; escalate to `deep` only on a declared trigger (see `../../roles/adversary.md`) | read_only | none | every finding recorded as the seven-field record in `../../references/findings.md`; a concern with no reachable precondition goes in a labeled speculation list, not the findings list |
| `confirm` (wave 1, depends on every `attack-<segment>` lane) | `prover` | standard | execute | none | every `critical` or `high` finding's precondition executed as described, raw output stored confirming or refuting reachability |
| `adjudicate` (wave 1 or later, dispatched only when an `attack-<segment>` lane and `confirm` disagree, or a verdict is requested directly) | `judge` | deep | read_only | none | a verdict naming which stored artifact settles the disagreement |

Every `attack-<segment>` lane runs in the same wave and none reads another's
output before both return, preserving the isolation that makes the attack
worth running instead of a self-review. `confirm` reads only the findings
and the surface itself, never the reasoning behind a finding.

## Delegation contract

You dispatch at depth one; none of harden's roles delegate further —
`adversary`, `prover`, and `judge` all have `canDelegate: false`. The rule
that Maximum delegation depth is two applies to harden only insofar as it
never approaches it: harden has no `mechanic` lane and nothing here should
reach depth two.

Adversary isolation is the one property that cannot degrade quietly. On a
host that cannot dispatch parallel subagents, harden runs as a
sequential fresh-context role-pass: each `attack-<segment>` lane runs to
completion in its own fresh context, then `confirm` runs in its own fresh
context reading only the stored findings, never an attacker's reasoning.
If the host cannot give an `attack-<segment>` lane a context that never
saw the surface's authoring work at all — not even in degraded sequential
form — record `isolation: degraded` in `run.json` and cap the run's
verdict at `unverified`; never let a degraded isolation produce `approve`.

## Quality gates

G4 is the gate harden exists to enforce as its entire subject matter: auth
and authz, payments, secrets, deserialization, file upload, and shell, SQL,
or template construction are attacked first and by default, regardless of
whether the declared surface named security explicitly. G3 binds every
`attack-<segment>` lane the same way it binds `verify`'s `falsify` lane —
adversarial verification runs in a context that never saw the authoring
work. G2 is enforced on every finding: a claimed vulnerability with no
stored raw output is not a finding. G9 applies to the run's own verdict — N
findings-free `attack-<segment>` lanes are not a clean bill of health;
`confirm`'s reproduction is the deciding evidence for reachability, not any
single lane's stated severity. Full definitions:
`../../references/gates.md`.

## Evidence and completion

Evidence, not assertions: every finding's `evidence` field points at stored
raw output under `.orchestra/<run>/<nn>-harden/evidence/`, per the
seven-field record in `../../references/findings.md` — `id`, `severity`,
`precondition`, `evidence`, `impact`, `remediation`, `retest`. A finding
missing any of the seven fields does not enter `findings.md`. The run's
verdict — `approve`,
`request_changes`, or `unverified` — is recorded in `verdicts.md` with its
rationale and the unresolved critical-and-high count it was decided
against.

## Hard stops

HARD STOP before every irreversible or outward-facing action; harden itself
is read-only and execute-only by construction — it reproduces a
precondition to prove reachability, it does not exploit one against a live
system outside the declared, sandboxed surface, and it never publishes a
finding externally. A `request_changes` or `unverified` verdict must reach
the human or the calling workflow before any fix ships on the strength of
harden's findings alone. Record every stop request in `stops.md` before
making it. See `../../references/stops.md`.

## Deterministic outputs

A harden run writes `run.json` (resolved host, each adversary's tier and
any escalation trigger, isolation status), `baseline.md`,
`decomposition.md` (the declared surface and its segments as dispatched),
one `lanes/<lane-id>.md` per lane holding its brief and normalized result
verbatim, `evidence/<nn>-<label>.txt` for every stored artifact including
`confirm`'s reproduction runs, `findings.md` for every finding raised,
`verdicts.md` for the recorded verdict, `stops.md` for any stop request,
and `handoff.md` naming what was attacked, what was confirmed, what
remains open, and the next dispatchable lane. Full layout:
`../../references/run-ledger.md`.

## Failure and recovery

A `blocked` or `partial` result from any `attack-<segment>` lane or from
`confirm` blocks the verdict: `adjudicate` does not resolve a disagreement
it lacks evidence for, and neither do you. Disagreement between an
`attack-<segment>` lane and `confirm` is itself an escalation trigger — it
raises the disagreeing `attack-<segment>` lane to `deep` tier and dispatches
`adjudicate`, per `../../roles/adversary.md`.

A finding moves to `fixed` only on a retest run after the remediation
lands, using evidence the fixing lane did not produce itself; reopen the
originating `attack-<segment>` lane, capped at three redispatches
(`reopenCount` in `run.json`) before the failure becomes a human escalation
instead of another retry. `accepted` and `wontfix` each require a named
human decision recorded in the ledger, never a lane's own judgment call
(see `../../references/findings.md`).
