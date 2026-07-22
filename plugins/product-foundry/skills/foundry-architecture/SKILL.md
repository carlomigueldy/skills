---
name: foundry-architecture
description: Select or revise a proportionate technical architecture and durable ADRs for an approved Product Foundry MVP. Use when resolving system boundaries, data, security, privacy, operations, deployment, or recovery decisions before defining the delivery harness and PRD.
---

# Architecture phase

Use `../../references/workflow.md` for phase state and participation, `../../references/platform-adapter.md` for questions, `../../references/artifact-contract.md` for canonical documentation, and `../../references/policies.md` for authority limits.

## Required inputs

- Require current, approved MVP and brand direction plus company, design, security, privacy, and deployment constraints. Stop on missing, draft, conflicting, or stale inputs; route the decision to the owning upstream phase.

## Deterministic outputs

1. Assess a pnpm monorepo, compatible Turborepo, Docker/Compose, and modular-monolith baseline against the constraints; adopt it only when proportionate.
2. Write `docs/architecture/architecture.md` with system boundaries, domain ownership, data lifecycle, authN/authZ, APIs, validation, storage, asynchronous jobs, billing, analytics, observability, secrets, deployment, backups, recovery, privacy, and security controls that apply to the MVP.
3. Create `docs/architecture/adr-<number>.md` for every material, durable decision or baseline deviation. State context, options, decision, consequences, risks, owner, evidence or assumptions, and revisit conditions.
4. Distinguish decided constraints, open questions, and deferred work. Do not design production implementation or authorize deployment, paid services, accounts, domains, secrets, destructive data work, legal acceptance, or irreversible actions.

## Completion criteria

- Check that every MVP capability has an owning boundary and that data handling, authentication, authorization, failure behavior, observability, backup, and recovery decisions are explicit where applicable.
- Reconcile architecture decisions with brand-driven accessibility needs, company constraints, and deployment environment. Flag unresolved conflicts rather than choosing silently.
- Fail closed on missing critical decisions, stale input, unresolved security/privacy risk, absent recovery path where data is retained, or unapproved high-consequence action. Keep the phase `draft` or `in_review` until resolved.

## Invalidation rules

Produce `docs/architecture/architecture.md` and the required `docs/architecture/adr-<number>.md` records. A changed product, design, company, security, privacy, deployment constraint, or ADR marks affected architecture artifacts stale and requires revisiting the harness, PRD, implementation order, and affected high-fidelity work.

## Participation gate

Offer exactly `Interview me` and `Decide for me`, selected independently at the start of every phase; never inherit a prior selection. Ask one material question at a time. In recommendation mode, record the recommendation, rationale, evidence, assumptions, confidence, risks, revisit conditions, and user authority. Obtain explicit approval for high-consequence choices and any external action.

## Approval gate

Mark artifacts approved only after explicit approval. Offer approve, request changes, or go back; never infer approval from silence. Approval unlocks the agent harness.
