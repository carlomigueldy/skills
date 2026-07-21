---
name: product-foundry
description: Run a resumable, approval-gated product discovery and handoff session for a new or evolving product idea.
---

# Product Foundry

Create or resume a product state under `docs/`, then run exactly one approved
phase at a time. Use the normalized interaction and approval model in
`../../references/workflow.md`, the safety and delegation rules in
`../../references/policies.md`, and the generated-artifact rules in
`../../references/artifact-contract.md`.

Route in this order: `foundry-intake`, `foundry-research`,
`foundry-company-strategy`, `foundry-mvp`, `foundry-low-fidelity`,
`foundry-brand`, `foundry-architecture`, `foundry-agent-harness`,
`foundry-prd`, `foundry-high-fidelity`, `foundry-go-to-market`,
`foundry-readiness`, and `foundry-handoff`. Do not skip a gate. On an approved
handoff, recommend a fresh `$implement-prd` session with the generated
implementation manifest attached.
