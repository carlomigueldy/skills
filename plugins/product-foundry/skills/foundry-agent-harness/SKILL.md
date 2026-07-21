---
name: foundry-agent-harness
description: Choose Lean, Standard, or Advanced delivery controls and create a platform-neutral, auditable agent harness plan.
---

# Agent harness phase

Explain Lean, Standard, and Advanced trade-offs and obtain an explicit choice;
recommend Standard when proportionate. Do not create a roster before
`find-skills` succeeds. Record task state, quality gates, recursive context-map
ownership, delegation limits, specialist roles, and release controls in
`docs/agents/` and `docs/delivery/`, following `../../references/policies.md`.

## Required inputs

Approved architecture, delivery risk, and successful `find-skills` discovery.

## Deterministic outputs

`docs/agents/roster.json`, `docs/delivery/task-state.json`, and selected harness gates.

## Completion criteria

Harness level, ownership, quality gates, and recovery rules are approved; roster creation fails closed without `find-skills` installation/recovery guidance.

## Invalidation rules

Changed architecture, harness level, or discovered capabilities stales roster and task graph.

## Participation gate

At the start of every phase, selected independently at the start of every phase: `Interview me` or `Decide for me`; never inherit a previous selection. For `Decide for me`, record rationale, evidence, assumptions, confidence, risks, and revisit conditions.

## Approval gate

Offer approve, request changes, or go back; only approval unlocks the PRD.
