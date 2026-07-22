---
name: foundry-research
description: Investigate customer problems, market signals, alternatives, and competitors with traceable dated sources, confidence, and clearly labeled inferences. Use after approved intake, when validating or revising a product opportunity, or when evidence contradicts an existing strategy.
---

# Research phase

Build an evidence base for the problem, not a feature list. Read
`../../references/workflow.md` for state and approval behavior,
`../../references/policies.md` for delegation and external-action limits, and
`../../references/platform-adapter.md` and
`../../references/artifact-contract.md` before presenting choices or creating
artifacts.

## Required inputs

Require approved intake, a problem statement, and any supplied customer or
market evidence. For a direct revision, create a new draft but do not unlock
company strategy until the revised evidence synthesis is approved.

## Run the phase

1. Verify approved intake and identify the customer, problem, decision, and
   uncertainty each research activity must address. Reopen research when its
   upstream context has changed.
2. Offer exactly `Interview me` and `Decide for me` for this phase; do not
   inherit a prior choice. Ask one material question at a time using the
   platform adapter when options are needed.
3. Collect only decision-relevant customer, market, and alternative evidence.
   Record each source's URL or provenance, publication/access date, claim,
   confidence, limitations, and whether a conclusion is evidence or inference.
4. Synthesize support, contradictions, gaps, and the assumptions that still
   require validation. Avoid presenting competitor claims, market size, or
   customer behavior as facts without traceable support.
5. Write the evidence record, move it from `draft` to `in_review`, and offer
   approval, changes, or a return to intake. Do not infer approval from silence.

## Deterministic outputs

Write `docs/research/evidence.md` with the evidence ledger, synthesis, gaps,
and next validation questions. Consolidate small products instead of creating
empty supporting documents.

## Completion criteria

Trace every material claim to a source or label it as an inference, expose
contradictions and gaps, and prepare a reviewable synthesis.

## Invalidation rules

A changed target
customer, problem, decision criteria, or materially contradictory evidence
makes the synthesis and affected strategy/MVP decisions stale; preserve raw
sources and reassess their relevance rather than deleting them.

## Participation gate

Offer `Interview me` and `Decide for me`, selected independently at the start of every phase; do not inherit a prior choice. In recommendation mode, record
rationale, evidence, assumptions, confidence, risks, revisit conditions, and
user authority. Do not resolve high-consequence decisions for the user.

## Approval gate

Require explicit approval before unlocking company strategy. Offer approval,
changes, or a return to intake; never infer approval from silence.

## Safety and delegation

Perform desk research and synthesis locally when possible. Require explicit
approval before outreach, interviews, paid data, account creation, scraping
that may breach terms, or commitments. Delegate bounded collection with a clear
question and source requirements; keep one canonical writer, record any
escalation, and independently review delegated claims before adoption.
