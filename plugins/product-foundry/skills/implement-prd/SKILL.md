---
name: implement-prd
description: Implement or safely resume an approved product MVP from Product Foundry artifacts, a manifest, or explicit attached inputs.
---

# Implement approved PRD

Normalize inputs using the strict precedence and host behavior in
`../../references/platform-adapter.md`. Read explicit attachments before
repository defaults. Validate the manifest against
`../../schemas/implementation-manifest.schema.json`; report missing or
conflicting critical decisions before changing the repository.

Support `--fresh` and `--resume`. Auto-detect credible existing task state and
ask for confirmation rather than overwriting it. Before creating a roster, run
`find-skills`. If it is unavailable, fail closed: stop roster creation and give
installation and recovery guidance; never substitute a guessed roster. Record
ownership, skills, inputs, outputs, tools, and escalation criteria only after
successful discovery. Enforce the shared authority, quality, evidence, and single-writer
rules in `../../references/policies.md`. Keep task state in the schema at
`../../schemas/task-state.schema.json` and only mark work complete with current
documentation and verification evidence. On resume, reconcile stale ownership,
partial work, conflicts, changed input fingerprints, and failed verification;
preserve verified work until a recorded input changes or it fails re-verification.
