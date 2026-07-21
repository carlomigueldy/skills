---
name: foundry-low-fidelity
description: Create a build-free low-fidelity HTML prototype that validates information architecture, flows, states, and responsiveness.
---

# Low-fidelity prototype phase

First verify `frontend-design` is available; otherwise fail closed with
installation and recovery guidance from `../../references/policies.md`. Create the canonical prototype under
`docs/prototypes/low-fidelity/` from
`../../templates/prototypes/low-fidelity/index.html`. It must remain plain
HTML, vanilla JavaScript, and Tailwind v4 browser CDN with keyboard-accessible,
responsive loading, empty, error, permission, success, and validation states.
Follow `../../references/artifact-contract.md` and gate the result.

## Required inputs

Approved MVP journeys, exclusions, and accessibility intent; `frontend-design` must be available.

## Deterministic outputs

`docs/prototypes/low-fidelity/index.html` plus documented workflow/state coverage.

## Completion criteria

The build-free responsive prototype covers every required interaction state and is approved.

## Invalidation rules

Changed MVP journey, information architecture, or scope stales this prototype and high fidelity.

## Participation gate

At the start of every phase, selected independently at the start of every phase: `Interview me` or `Decide for me`; never inherit a previous selection. For `Decide for me`, record rationale, evidence, assumptions, confidence, risks, and revisit conditions.

## Approval gate

Offer approve, request changes, or go back; only approval unlocks brand direction.
