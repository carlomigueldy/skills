---
name: foundry-readiness
description: Verify PRD, prototype, architecture, marketing, safety, quality gates, release plan, and unresolved decisions before handoff.
---

# Readiness phase

Fail closed on missing critical decisions, stale dependencies, incomplete state
coverage, absent evidence, or unapproved external actions. Reconcile product,
design, architecture, marketing, delivery, release, and risk artifacts; record
verification evidence in `docs/handoffs/`. Apply completion rules in
`../../references/policies.md` before approval.

## Required inputs

Approved PRD, prototypes, architecture, harness, marketing plan, and verification evidence.

## Deterministic outputs

`docs/handoffs/readiness.md` listing gates, blockers, reconciliations, and evidence.

## Completion criteria

Critical conflicts are resolved or blocked explicitly; required gates are verified and approved.

## Invalidation rules

Changed approved artifact, failed check, stale owner, or partial task reopens readiness.

## Participation gate

At the start of every phase, selected independently at the start of every phase: `Interview me` or `Decide for me`; never inherit a previous selection. For `Decide for me`, record rationale, evidence, assumptions, confidence, risks, and revisit conditions.

## Approval gate

Offer approve, request changes, or go back; only approval unlocks handoff.
