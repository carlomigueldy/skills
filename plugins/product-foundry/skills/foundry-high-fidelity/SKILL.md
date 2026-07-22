---
name: foundry-high-fidelity
description: Create or revise a build-free, high-fidelity HTML reference for an approved MVP. Use when the approved PRD, low-fidelity flows, and brand direction must be expressed as responsive, accessible core interactions before go-to-market.
---

# High-fidelity prototype phase

Create the canonical visual reference at
`docs/prototypes/high-fidelity/index.html`. Read
`../../references/artifact-contract.md` for prototype constraints and
`../../references/workflow.md` for the shared phase gate.

## Required inputs

- Approved PRD and MVP boundaries.
- Approved low-fidelity journeys and state coverage.
- Approved brand direction and relevant architecture constraints.
- Availability of the `frontend-design` skill.

## Workflow

1. Start with the independent participation choice and one-question protocol in
   `../../references/workflow.md`.
2. Verify that `frontend-design` is available before designing. If it is not,
   fail closed and give the installation/recovery guidance in
   `../../references/policies.md`; do not substitute an ad-hoc design workflow.
3. Check that the PRD, flows, and brand thesis are approved and current. Return
   conflicting or stale input to its owning phase.
4. Adapt `../../templates/prototypes/high-fidelity/index.html` into the
   canonical prototype. Use plain HTML, vanilla JavaScript, and the Tailwind v4
   browser CDN only; do not add a package, framework, build step, or second
   canonical prototype.
5. Express the approved visual thesis with realistic fixtures and responsive
   desktop/mobile layouts. Implement every core journey and the loading, empty,
   validation, error, permission, success, and recovery states required by the
   PRD.
6. Make interactive controls keyboard-operable and provide visible focus,
   semantic structure, labels, and understandable feedback. Keep the prototype
   a product reference, not production code.

## Deterministic outputs

- `docs/prototypes/high-fidelity/index.html`, the current visual and interaction
  reference.

## Completion criteria

Complete this phase only after validating the prototype at desktop and mobile widths. Exercise every documented
journey and required non-happy-path state with keyboard and pointer input;
confirm that its copy, scope, and interactions agree with the approved PRD and
that no build dependency was introduced. Record gaps as blockers.

## Invalidation rules

A changed MVP boundary, requirement, flow, brand thesis, or
material architecture constraint stales affected screens and implementation
design references until reconciled and re-approved.

## Participation gate

Offer `Interview me` or `Decide for me`, selected independently at the start of every phase.
For `Decide for me`, record rationale, evidence, assumptions,
confidence, risks, and revisit conditions; never treat silence as approval.

## Approval gate

Move the artifact from `draft` to `in_review`, then offer approve, request
changes, or return to the owning upstream phase. Only approval unlocks
go-to-market.

## Handoff

Pass the approved prototype path, tested state coverage, accessibility gaps,
and links to its PRD requirements to `foundry-go-to-market`. Keep the prototype
as the canonical interaction reference for readiness and implementation.
