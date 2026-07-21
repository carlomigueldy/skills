---
name: foundry-prd
description: Produce a deterministic, traceable PRD with stable requirements, acceptance criteria, evidence, assumptions, risks, and MVP boundaries.
---

# PRD phase

Write `docs/product/prd.md` as the coherent implementation contract. Give every
material requirement a stable identifier, priority, acceptance criteria, and
evidence or explicit assumption. Cover journeys, NFRs, domain model, design,
architecture, security, privacy, analytics, PMF, marketing, launch, support,
quality gates, releases, risks, and conditional roadmap. Index rather than
duplicate it via `../../references/artifact-contract.md`.

## Required inputs

Approved strategy, MVP, design, architecture, and harness decisions.

## Deterministic outputs

`docs/product/prd.md` with stable requirements and traceability.

## Completion criteria

Requirements, NFRs, risks, gates, and evidence/assumptions are complete and approved.

## Invalidation rules

Changed approved upstream decision stales affected requirements and all downstream references.

## Participation gate

At the start of every phase, selected independently at the start of every phase: `Interview me` or `Decide for me`; never inherit a previous selection. For `Decide for me`, record rationale, evidence, assumptions, confidence, risks, and revisit conditions.

## Approval gate

Offer approve, request changes, or go back; only approval unlocks high fidelity.
