---
name: foundry-high-fidelity
description: Create a build-free high-fidelity HTML prototype that expresses the approved visual thesis and complete core interactions.
---

# High-fidelity prototype phase

First verify `frontend-design` is available; otherwise fail closed with
installation and recovery guidance from `../../references/policies.md`. Build the
canonical reference at `docs/prototypes/high-fidelity/` from
`../../templates/prototypes/high-fidelity/index.html`, using only plain HTML,
vanilla JavaScript, and the Tailwind v4 browser CDN. Include realistic fixtures,
responsive desktop/mobile layouts, accessible interaction, and non-happy-path
states; validate against `../../references/artifact-contract.md` before its
approval gate.

## Required inputs

Approved MVP, low-fidelity workflow, brand thesis, and `frontend-design` availability.

## Deterministic outputs

`docs/prototypes/high-fidelity/index.html` with realistic, responsive state coverage.

## Completion criteria

The build-free visual reference covers core interactions, accessibility, and all required states and is approved.

## Invalidation rules

Changed MVP, flow, or brand thesis stales this prototype and implementation design references.

## Participation gate

At the start of every phase, selected independently at the start of every phase: `Interview me` or `Decide for me`; never inherit a previous selection. For `Decide for me`, record rationale, evidence, assumptions, confidence, risks, and revisit conditions.

## Approval gate

Offer approve, request changes, or go back; only approval unlocks go-to-market.
