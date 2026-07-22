---
name: foundry-low-fidelity
description: Create or revise the Product Foundry build-free low-fidelity HTML prototype for an approved MVP. Use when validating information architecture, journeys, responsive behavior, accessibility intent, and loading, empty, error, permission, success, or validation states before establishing brand direction.
---

# Low-fidelity prototype phase

Use `../../references/workflow.md` for phase state and participation, `../../references/platform-adapter.md` for questions, and `../../references/artifact-contract.md` for prototype constraints. Read `../../references/policies.md` only when resolving the required dependency.

## Required inputs

- Verify that `frontend-design` is available before creating or changing a prototype. If it is unavailable, stop; do not substitute another workflow. Give installation and recovery guidance from `../../references/policies.md`.
- Require current, approved MVP journeys, exclusions, and accessibility intent. Treat missing, draft, or stale inputs as blockers and identify the upstream phase to revise.

## Deterministic outputs

1. Start from `../../templates/prototypes/low-fidelity/index.html` and keep the canonical version at `docs/prototypes/low-fidelity/index.html`.
2. Use only plain HTML, vanilla JavaScript, and `@tailwindcss/browser@4`; require no package install or build step.
3. Map every approved journey and its applicable loading, empty, error, permission, success, and validation states. Keep the interface intentionally low fidelity so it tests structure and behavior, not brand styling.
4. Make all interactions keyboard operable, preserve visible focus, use semantic labels and live feedback where needed, and verify narrow and wide layouts.
5. Record journey-to-state coverage, checks performed, known gaps, and source input versions in `docs/prototypes/low-fidelity/coverage.md`.

## Completion criteria

- Open the HTML without a build step, exercise every documented state, and verify keyboard navigation and responsive layouts.
- On an uncovered required journey or state, missing dependency, inaccessible interaction, stale MVP input, or undocumented limitation, fail closed. Keep the phase `draft` or `in_review` until resolved.

## Invalidation rules

Produce `docs/prototypes/low-fidelity/index.html` and `docs/prototypes/low-fidelity/coverage.md`. A changed MVP journey, information architecture, exclusion, accessibility intent, or scope marks both artifacts stale and requires reconsidering downstream brand and high-fidelity work.

## Participation gate

Offer exactly `Interview me` and `Decide for me`, selected independently at the start of every phase; never inherit a prior selection. Ask one material question at a time. In recommendation mode, record the recommendation, rationale, evidence, assumptions, confidence, risks, revisit conditions, and user authority; do not resolve high-consequence decisions without explicit approval.

## Approval gate

Mark the artifacts approved only after explicit approval. Offer approve, request changes, or go back; never infer approval from silence. Approval unlocks brand direction.
