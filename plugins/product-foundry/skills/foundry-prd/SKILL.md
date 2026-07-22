---
name: foundry-prd
description: Create or revise the canonical, traceable product requirements document. Use when approved strategy, MVP, design, architecture, or harness decisions must become implementation-ready requirements before high-fidelity design.
---

# PRD phase

Turn approved product decisions into one implementation contract at
`docs/product/prd.md`. Read `../../references/workflow.md` for phase state and
approval, `../../references/artifact-contract.md` for canonical-document rules,
and `../../references/policies.md` when a decision has material risk.

## Required inputs

- Approved strategy, research evidence, MVP scope and exclusions.
- Approved workflow/design, brand, architecture, and harness decisions that
  affect the product.
- Known constraints, risks, and unresolved decisions.

## Workflow

1. Start the phase using the participation and one-question interaction rules in
   `../../references/workflow.md`. Do not inherit a prior participation choice
   or treat silence as approval.
2. Check that each source is readable, approved, and not stale. Stop at the
   affected prerequisite instead of inventing a decision or silently repairing
   an upstream artifact.
3. Write proportional sections for the problem and outcomes, MVP boundary,
   journeys and edge states, functional requirements, NFRs, data and external
   dependencies, privacy/security constraints, analytics, rollout/support, and
   risks. Omit sections that have no material product consequence.
4. Give every material requirement a stable `REQ-...` identifier, `must`,
   `should`, `could`, or `wont` priority, testable acceptance criteria, and
   traceability to evidence and explicit assumptions. Keep conditional roadmap
   ideas out of MVP requirements.
5. Link to canonical source artifacts rather than duplicating their content.
   Record conflicts, open decisions, and their owners/revisit conditions.

## Deterministic outputs

- `docs/product/prd.md`, the canonical requirement and traceability contract.

## Completion criteria

Complete this phase only after validating that every `must` requirement has at least one observable
acceptance criterion; all IDs are unique and stable; scope and exclusions agree
with the MVP; and referenced evidence, decisions, and constraints are current.
Mark unresolved conflicts as blockers rather than presenting the PRD as
complete.

## Invalidation rules

An approved upstream decision, MVP boundary, journey, architecture constraint,
or evidence change makes its requirements and downstream references stale;
reconcile and re-approve before reuse.

## Participation gate

Offer `Interview me` or `Decide for me`, selected independently at the start of every phase.
For `Decide for me`, record rationale, evidence, assumptions,
confidence, risks, and revisit conditions; never treat silence as approval.

## Approval gate

Move the PRD from `draft` to `in_review`, then offer approve, request changes,
or return to the affected upstream phase. Only approval unlocks high fidelity.

## Handoff

Pass the approved PRD, requirement IDs, open blockers, and source links to
`foundry-high-fidelity`. Keep the PRD authoritative; later artifacts reference
it instead of copying requirements.
