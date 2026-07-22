---
name: foundry-go-to-market
description: Create or revise a focused, measurable go-to-market plan. Use when approved product, brand, pricing, and founder constraints must become executable positioning, channel, launch, and learning decisions before readiness.
---

# Go-to-market phase

Create the selective execution plan at `docs/marketing/go-to-market.md`. Read
`../../references/workflow.md` for the shared approval model and
`../../references/policies.md` before any consequential external action.

## Required inputs

- Approved company strategy, ICP, product thesis, and MVP boundary.
- Approved brand direction, pricing constraints, and high-fidelity reference.
- Founder capacity, budget, sales capability, launch date, and existing assets.

## Workflow

1. Start with the independent participation choice and one-question protocol in
   `../../references/workflow.md`.
2. Check source artifacts for approval and freshness. Return an ICP, pricing,
   scope, or brand conflict to its owning phase; do not make downstream
   messaging compensate for it.
3. Define the positioning, category, audience, message hierarchy, offer, and
   proof requirements. Distinguish facts from assumptions and unsupported
   claims.
4. Select only channels that fit founder capacity and the launch hypothesis.
   For every chosen channel, specify its audience, asset, owner, cadence,
   cost/budget limit, CTA, attribution, learning metric, threshold, and stop or
   iterate rule. Record material rejected channels and why.
5. Draft the smallest necessary launch assets in the plan: landing-page message
   structure, lifecycle email, campaign brief, launch calendar, and any selected
   outbound, partnership, content, SEO, social, paid, or sales motion. Do not
   publish, buy, create accounts, or spend money without the explicit approval
   required by `../../references/policies.md`.

## Deterministic outputs

- `docs/marketing/go-to-market.md`, including positioning, selected channels,
  assets, attribution, experiments, budget, and launch schedule.

## Completion criteria

Complete this phase only after validating that every claim has evidence or an assumption label;
every selected channel has an owner, capacity fit, measurement method, and
learning threshold; pricing and CTA match the approved product; and the launch
calendar has no unapproved external commitment. Mark missing proof or owners as
blockers.

## Invalidation rules

A changed ICP, pricing, product thesis, brand direction, budget, capacity, or
launch constraint stales the affected message, asset, channel, and experiment.

## Participation gate

Offer `Interview me` or `Decide for me`, selected independently at the start of every phase.
For `Decide for me`, record rationale, evidence, assumptions,
confidence, risks, and revisit conditions; never treat silence as approval.

## Approval gate

Move the plan from `draft` to `in_review`, then offer approve, request changes,
or return to the owning upstream phase. Only approval unlocks readiness.

## Handoff

Pass the approved plan, selected-channel owners, launch dependencies,
measurement definitions, and unresolved blockers to `foundry-readiness`.
Treat this plan as a decision record; readiness verifies evidence and approvals
without duplicating it.
