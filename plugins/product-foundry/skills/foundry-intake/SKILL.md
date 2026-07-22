---
name: foundry-intake
description: Elicit and record a product founder's goals, constraints, capabilities, decision authority, and assumptions as the approval-gated starting point of Product Foundry. Use when starting discovery, revising intake after a material change, or structuring an idea before research.
---

# Intake phase

Establish the decision context before researching or defining a solution. Read
`../../references/workflow.md` for state and approval behavior,
`../../references/platform-adapter.md` before presenting choices, and
`../../references/policies.md` before consequential actions.

## Required inputs

Require the founder's available context and any prior approved Foundry
artifacts. For a direct revision, create a new draft but do not unlock research
until the revised intake is approved.

## Run the phase

1. Inspect prior approved Foundry artifacts and identify changed or missing
   context. Do not treat a draft or `in_review` artifact as approved input.
2. Offer exactly `Interview me` and `Decide for me` for this phase; do not
   inherit the previous phase's choice. Ask one material question at a time.
3. Capture the problem or opportunity, intended customer, desired outcome,
   founder capabilities, runway, constraints, decision authority, and known
   assumptions. Distinguish facts, preferences, and unknowns.
4. In recommendation mode, record the recommendation, rationale, evidence,
   assumptions, confidence, risks, revisit conditions, and user authority. Do
   not resolve high-consequence decisions for the user.
5. Write the canonical intake record, review it with the founder, and move it
   from `draft` to `in_review`. Offer approval, changes, or a return to an
   earlier decision; never infer approval from silence.

## Deterministic outputs

Write `docs/company/intake.md`, containing the decision context, labeled
assumptions, open questions, and decision record. Consolidate into the existing
document for a small product; do not create placeholder artifacts.

## Completion criteria

Record every material intake answer, distinguish facts from unknowns, and
prepare a reviewable intake summary.

## Invalidation rules

Changing goals, customer, constraints, capabilities, runway, or decision
authority marks affected research and all downstream decisions stale; retain
unchanged evidence but reopen its synthesis.

## Participation gate

Offer `Interview me` and `Decide for me`, selected independently at the start of every phase; do not inherit a prior choice. In recommendation mode, record
rationale, evidence, assumptions, confidence, risks, revisit conditions, and
user authority. Do not resolve high-consequence decisions for the user.

## Approval gate

Require an explicit approval of the intake summary before unlocking research.
Offer approval, changes, or a return to an earlier decision; never infer
approval from silence.

## Safety and delegation

Keep interviews and document synthesis local unless the user authorizes an
external action. Require explicit approval for outreach, paid research,
accounts, legal commitments, or irreversible work. Delegate only bounded
mechanical collection under the shared policy, keep one writer for canonical
state, and review delegated output before recording it as evidence.
