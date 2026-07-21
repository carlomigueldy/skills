---
name: foundry-architecture
description: Select a proportionate technical architecture and record explicit decisions for core platform, operations, privacy, and security concerns.
---

# Architecture phase

Interview stack constraints. Recommend a pnpm monorepo, compatible Turborepo,
Docker/Compose, and modular monolith only when they fit; record deviations as
ADRs. Decide boundaries, data, auth, APIs, validation, storage, jobs, billing,
analytics, observability, backups, recovery, secrets, privacy, and deployment
in `docs/architecture/`. Apply high-consequence safety limits from
`../../references/policies.md`.

## Required inputs

Approved MVP, design constraints, company constraints, and deployment requirements.

## Deterministic outputs

`docs/architecture/architecture.md` and ADRs for every meaningful deviation.

## Completion criteria

Core platform, operations, privacy, security, and recovery decisions are explicit and approved.

## Invalidation rules

Changed product constraints or ADRs stales harness, PRD, implementation order, and high fidelity where affected.

## Participation gate

At the start of every phase, selected independently at the start of every phase: `Interview me` or `Decide for me`; never inherit a previous selection. For `Decide for me`, record rationale, evidence, assumptions, confidence, risks, and revisit conditions.

## Approval gate

Offer approve, request changes, or go back; only approval unlocks the agent harness.
