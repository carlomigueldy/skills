# Shared workflow contract

All phases use the same state machine: `draft` -> `in_review` -> `approved`.
Only an approved phase unlocks its downstream phase. A changed upstream
decision marks downstream artifacts stale; each phase may also be invoked
directly to revise and re-approve its own area.

Ask one material question at a time. At the start of every phase independently
offer exactly `Interview me` and `Decide for me`; never carry a prior selection
into a new phase. Recommendation mode records the recommendation, rationale,
evidence, assumptions, confidence, risks, revisit conditions, and user authority. It may resolve
ordinary planning choices but never a high-consequence decision.

The normal order is intake, research, company strategy, MVP, low fidelity,
brand, architecture, agent harness, PRD, high fidelity, go to market,
readiness, then handoff. The foundry does not implement production code unless
the user explicitly starts the separate `implement-prd` session.
