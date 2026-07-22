---
name: foundry-agent-harness
description: Configure or revise a Lean, Standard, or Advanced Product Foundry delivery harness with a discovered, auditable agent roster, task state, ownership, delegation, and quality gates. Use after approved architecture and before PRD creation or implementation planning.
---

# Agent harness phase

Use `../../references/workflow.md` for phase state and participation, `../../references/platform-adapter.md` for questions, `../../references/policies.md` for delegation and authority limits, and the two schemas only when creating or validating their JSON artifacts.

## Required inputs

- Require current, approved architecture, delivery-risk constraints, and an explicit harness-level decision. Offer normalized `lean`, `standard`, and `advanced` options with consequences; recommend Standard only when proportionate.
- Run `find-skills` before creating a product-specific roster. If discovery is unavailable or fails, stop before roster creation. Provide installation and recovery guidance from `../../references/policies.md`; never fabricate a guessed roster.

## Deterministic outputs

1. Use `../../templates/docs/agent-roster.json` and `../../schemas/agent-roster.schema.json` to create `docs/agents/roster.json` from discovered capabilities.
2. Assign one owner to each shared-state area and document every agent's responsibility, inputs, outputs, required skills, tools, escalation path, and review evidence. Keep default delegation depth at two; justify any deeper delegation in the roster.
3. Use `../../templates/docs/task-state.json` and `../../schemas/task-state.schema.json` to create `docs/delivery/task-state.json`. Record input fingerprints, ownership, status, verification evidence, stale owners, partial tasks, conflicts, changed-input invalidation, and failed-verification reopening.
4. Write `docs/delivery/harness.md` with the selected level, scope, quality gates, release controls, recursive context-map ownership, recovery behavior, and escalation rules. Do not create live agents, deploy, purchase, or change external systems.

## Completion criteria

- Validate both JSON artifacts against their corresponding schemas and verify that documented skills/tools came from discovery.
- Verify single-writer ownership for shared state, explicit review evidence for delegated work, current input fingerprints, and a recovery path for partial, stale, conflicting, or failed work. Preserve verified tasks until a recorded input changes or re-verification fails.
- Fail closed on failed discovery, invalid schema, duplicate shared ownership, absent quality or recovery gates, stale architecture, or missing approval. Keep the phase `draft` or `in_review` until resolved.

## Invalidation rules

Produce `docs/agents/roster.json`, `docs/delivery/task-state.json`, and `docs/delivery/harness.md`. A changed architecture, harness level, delivery risk, discovered capability, input fingerprint, or failed verification marks affected roster entries and task graph work stale; reconcile before re-approval.

## Participation gate

Offer exactly `Interview me` and `Decide for me`, selected independently at the start of every phase; never inherit a prior selection. Ask one material question at a time. In recommendation mode, record the recommendation, rationale, evidence, assumptions, confidence, risks, revisit conditions, and user authority; never resolve high-consequence decisions without explicit approval.

## Approval gate

Mark artifacts approved only after explicit approval. Offer approve, request changes, or go back; never infer approval from silence. Approval unlocks the PRD.
