---
name: foundry-mvp
description: Define the smallest testable MVP that can evaluate an approved customer and business hypothesis, including exclusions, journeys, risks, experiments, and success thresholds. Use after company strategy, when narrowing a product scope, or when an MVP experiment must be revised.
---

# MVP phase

Specify the minimum experiment that can change a decision; do not turn a
roadmap into an MVP. Read `../../references/workflow.md` for state and approval
behavior, `../../references/policies.md` before consequential actions, and
`../../references/platform-adapter.md` and
`../../references/artifact-contract.md` before presenting choices or creating
artifacts.

## Required inputs

Require approved company strategy, relevant research evidence, and the customer
problem hypothesis. For a direct revision, create a new draft but do not unlock
low-fidelity work until the revised MVP is approved.

## Run the phase

1. Verify approved strategy and evidence. State the customer, hypothesis,
   decision to change, constraints, and unresolved assumptions before proposing
   scope.
2. Offer exactly `Interview me` and `Decide for me` for this phase; do not
   inherit a prior choice. Ask one material question at a time and use stable
   platform-adapter options when choices are presented.
3. Define the smallest end-to-end journey, required states and edge cases,
   explicit exclusions, riskiest assumptions, and dependencies. Move every
   nonessential idea to a conditional roadmap rather than silently retaining it.
4. Define validation method, participant or data boundary, duration, success
   and stop thresholds, instrumentation needs, and the decision each outcome
   will trigger. Label threshold rationale and uncertainty.
5. Write the scope, move it from `draft` to `in_review`, and offer approval,
   changes, or a return to strategy. Do not infer approval from silence.

## Deterministic outputs

Write `docs/product/mvp.md` with scope, exclusions, journeys and states,
experiment design, thresholds, dependencies, and conditional roadmap.
Consolidate small products instead of creating empty companion files.

## Completion criteria

Define a smallest testable scope with explicit exclusions, measurable decision
thresholds, and an experiment outcome that can change the next decision.

## Invalidation rules

A changed
hypothesis, target customer, success signal, experiment boundary, or exclusion
marks affected prototypes, PRD requirements, and delivery plans stale; retain
the prior version as history and reassess downstream dependencies.

## Participation gate

Offer `Interview me` and `Decide for me`, selected independently at the start of every phase; do not inherit a prior choice. In recommendation mode, record
rationale, evidence, assumptions, confidence, risks, revisit conditions, and
user authority. Do not resolve high-consequence decisions for the user.

## Approval gate

Require explicit approval before unlocking low-fidelity work. Offer approval,
changes, or a return to strategy; never infer approval from silence.

## Safety and delegation

Keep planning separate from production implementation. Require explicit
approval before recruiting or contacting participants, collecting sensitive
data, paid tools, accounts, production deployment, or irreversible actions.
Delegate bounded analysis under the shared policy, retain one canonical writer,
record escalations, and review delegated work before it changes scope.
