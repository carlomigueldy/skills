---
name: foundry-handoff
description: Generate the validated implementation manifest and concise context maps for a fresh, platform-neutral MVP implementation session.
---

# Handoff phase

Generate `docs/implementation-manifest.json` from canonical approved artifacts
without duplicating their content. Validate it against
`../../schemas/implementation-manifest.schema.json`; include artifact status,
MVP boundaries, blockers, design/architecture references, gates, skills,
harness, environment constraints, implementation order, completion criteria,
and platform-neutral state. Create concise `AGENTS.md` and `CLAUDE.md` maps
from `../../templates/docs/` and recommend a fresh `$implement-prd` session.

## Required inputs

Approved readiness evidence, canonical docs, task state, and unresolved blockers.

## Deterministic outputs

Validated `docs/implementation-manifest.json` plus concise `AGENTS.md` and `CLAUDE.md` maps.

## Completion criteria

The manifest indexes approved inputs, ordering, blockers, fingerprints, and reconciliation state without duplicating source truth.

## Invalidation rules

Changed approved artifact, input fingerprint, conflict, or failed verification reopens handoff.

## Participation gate

At the start of every phase, selected independently at the start of every phase: `Interview me` or `Decide for me`; never inherit a previous selection. For `Decide for me`, record rationale, evidence, assumptions, confidence, risks, and revisit conditions.

## Approval gate

Offer approve, request changes, or go back; approval permits a separate fresh or resume implementation session.
