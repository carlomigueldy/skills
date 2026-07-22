---
name: foundry-brand
description: Define or revise a product-specific visual thesis, voice, token system, component conventions, and rejected directions after approved MVP and low-fidelity flows. Use before technical architecture or high-fidelity prototype work when design decisions need evidence-backed, accessible direction.
---

# Brand phase

Use `../../references/workflow.md` for phase state and participation, `../../references/platform-adapter.md` for questions, and `../../references/artifact-contract.md` for canonical documentation.

## Required inputs

- Require current, approved MVP scope, low-fidelity flows, audience definition, and research evidence. Stop on missing, draft, contradictory, or stale inputs; name the upstream artifact that needs revision.

## Deterministic outputs

1. Write `docs/design/brand.md` around the approved audience, product promise, and MVP context; do not choose decorative trends without a product reason.
2. Specify the visual thesis, narrative, voice and tone, accessibility intent, token values and semantic roles, typography, spacing, imagery, motion, and component conventions.
3. Tie each material decision to evidence or an explicit assumption. Record rejected directions, their trade-offs, and the condition that would justify revisiting them.
4. Make tokens and component rules usable by the high-fidelity and implementation phases without duplicating their artifacts.

## Completion criteria

- Check that the thesis, voice, tokens, and conventions do not contradict the MVP, audience, or low-fidelity interaction model; identify any intentional tension and its rationale.
- Check that the accessibility intent covers readable contrast, hierarchy, interaction feedback, and reduced-motion or equivalent accommodations where motion is proposed.
- Fail closed on unresolved contradictions, untraceable material choices, stale inputs, or missing rejected-direction rationale. Keep the phase `draft` or `in_review` until resolved.

## Invalidation rules

Produce `docs/design/brand.md`. A changed audience, MVP, low-fidelity interaction model, research conclusion, or approved visual thesis marks the brand artifact stale and requires revisiting affected high-fidelity, messaging, and architecture decisions.

## Participation gate

Offer exactly `Interview me` and `Decide for me`, selected independently at the start of every phase; never inherit a prior selection. Ask one material question at a time. In recommendation mode, record the recommendation, rationale, evidence, assumptions, confidence, risks, revisit conditions, and user authority; never make a high-consequence choice without explicit approval.

## Approval gate

Mark the artifact approved only after explicit approval. Offer approve, request changes, or go back; never infer approval from silence. Approval unlocks architecture.
