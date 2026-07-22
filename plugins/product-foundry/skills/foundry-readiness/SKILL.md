---
name: foundry-readiness
description: Reconcile and verify product, design, delivery, launch, safety, and release evidence before implementation handoff. Use when approved Foundry artifacts must be checked for conflicts, staleness, missing gates, and unresolved blockers.
---

# Readiness phase

Create a fail-closed readiness record at `docs/handoffs/readiness.md`. Read
`../../references/policies.md` for completion and external-action limits,
`../../references/workflow.md` for phase state, and
`../../references/artifact-contract.md` for canonical artifact paths.

## Required inputs

- Approved PRD, prototypes, architecture, harness, and go-to-market plan.
- Their verification evidence, owners, dependencies, and release constraints.
- Open decisions, blockers, task state, and changed-input information.

## Workflow

1. Start with the independent participation choice and one-question protocol in
   `../../references/workflow.md`.
2. Inventory required canonical artifacts. Check their readable paths, approval
   state, current input, owner, and verification evidence before treating any
   downstream conclusion as valid.
3. Reconcile requirements against prototype flows/states, design references,
   architecture decisions, delivery/harness constraints, marketing promises,
   release conditions, and risks. Record each conflict once with its source,
   impact, owner, and resolution or revisit condition.
4. Verify the declared quality, privacy/security, accessibility, operational,
   analytics, launch, and release gates using available evidence. Do not imply a
   deployment, legal acceptance, paid action, or other external result that has
   not been explicitly approved and evidenced.
5. Classify missing, failed, stale, or partial work as blockers. Reopen the
   responsible artifact or task rather than waiving a critical gate.

## Deterministic outputs

- `docs/handoffs/readiness.md`, listing artifact status, verified gates,
  reconciliations, evidence, blockers, owners, and required follow-up.

## Completion criteria

Complete this phase only after validating that the record distinguishes verified evidence from claims;
every required input is approved and current; every gate has a result and
evidence reference; and every unresolved item has a severity, owner, and
revisit condition. Fail closed on a critical conflict, stale dependency,
incomplete required state, absent evidence, or unapproved external action.

## Invalidation rules

Any changed approved artifact, changed input fingerprint, failed verification, stale owner,
or partial task reopens readiness and the affected gate.

## Participation gate

Offer `Interview me` or `Decide for me`, selected independently at the start of every phase.
For `Decide for me`, record rationale, evidence, assumptions,
confidence, risks, and revisit conditions; never treat silence as approval.

## Approval gate

Move readiness from `draft` to `in_review`, then offer approve, request changes,
or return to the responsible phase. Only approval unlocks handoff.

## Handoff

Pass the approved readiness record, canonical artifact inventory, gate evidence,
open blockers, and changed-input status to `foundry-handoff`. Do not create the
implementation manifest here; the handoff phase is its sole author.
