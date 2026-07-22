---
name: foundry-handoff
description: Package approved Foundry artifacts into a validated implementation manifest and concise context maps. Use when readiness is approved and a fresh or resume MVP implementation session needs current scope, order, gates, and blockers.
---

# Handoff phase

Generate the implementation index, not a second source of truth. Read
`../../references/artifact-contract.md`,
`../../references/platform-adapter.md`, and
`../../schemas/implementation-manifest.schema.json` before creating the
handoff package.

## Required inputs

- Approved `docs/handoffs/readiness.md` and its gate evidence.
- Approved canonical product, design, architecture, marketing, harness, and
  delivery artifacts.
- Current task state, unresolved decisions/blockers, and input fingerprints.

## Workflow

1. Start with the independent participation choice and one-question protocol in
   `../../references/workflow.md`. Confirm that readiness is approved and that
   no critical gate has reopened.
2. Inventory canonical inputs and verify their paths, approval states,
   fingerprints, and conflicts. Preserve unresolved items; do not erase them to
   make a manifest appear ready.
3. Start from `../../templates/docs/implementation-manifest.json` and produce
   `docs/implementation-manifest.json`. Index artifacts rather than duplicate
   their content. Include requirement IDs and traceability, MVP scope and
   exclusions, design and architecture references, quality gates, required
   skills, harness/environment constraints, implementation order, completion
   criteria, state, blockers, reconciliation, and changed-input invalidation.
4. Copy the concise templates in `../../templates/docs/` to repository-root
   `AGENTS.md` and `CLAUDE.md` only when those maps are part of the requested
   handoff. Tailor links to canonical docs without overwriting credible existing
   repository guidance; reconcile or request direction on a conflict.
5. Validate the manifest against
   `../../schemas/implementation-manifest.schema.json`. Then cross-check that
   every indexed path exists, every requirement is present in the PRD, task IDs
   and statuses match task state, and no approved/stale status conflicts with
   readiness evidence.

## Deterministic outputs

- Validated `docs/implementation-manifest.json`.
- Concise repository-root `AGENTS.md` and `CLAUDE.md` context maps when created
  or reconciled for the requested handoff.

## Completion criteria

Complete this phase only after validation. Fail closed if schema validation fails, an indexed artifact is unreadable, a
required fingerprint is absent, readiness conflicts with the manifest, or a
critical blocker remains. Record validation results and reconciliation state in
the manifest or its indexed readiness evidence; never claim implementation has
started merely because the package is valid.

## Invalidation rules

A changed approved artifact or
fingerprint, a newly detected conflict, or a failed verification reopens
handoff and affected implementation tasks.

## Participation gate

Offer `Interview me` or `Decide for me`, selected independently at the start of every phase.
For `Decide for me`, record rationale, evidence, assumptions,
confidence, risks, and revisit conditions; never treat silence as approval.

## Approval gate

Move the package from `draft` to `in_review`, then offer approve, request
changes, or return to the responsible phase. Approval permits, but does not
start, a separate implementation session.

## Handoff

Recommend a fresh `$implement-prd` session with the validated manifest attached
or explicitly selected. Follow the fresh/resume precedence in
`../../references/platform-adapter.md`; do not silently overwrite credible
implementation state.
