# Operation Modes

Declare exactly one primary mode before work begins. Authorization boundaries in `AGENTS.md` always apply.

## maintain

Preserve behavior while repairing drift or compatibility. Establish a baseline, make the smallest repair, and verify existing consumers and generated outputs.

## create

Atomically add the complete plugin surface: manifests, skills, marketplace registration, version and release configuration, tests, packaging, and documentation. Partial registration is a failure, not an intermediate deliverable.

## refine

Reproduce the limitation, change the smallest interface that resolves it, add regression coverage, and preserve host compatibility and existing contracts.

## test

Perform read-only validation and report evidence. Fixes require a separately authorized maintain or refine assignment; test mode alone grants no write authority.

## red-team

Adversarially test prompt and policy overrides, host fallbacks, malformed or missing resources, manifest/version drift, unsafe packaged paths, secrets, stale mirrors, governance bypasses, and fail-open checks. Follow the finding format and approval gate in [red-team.md](red-team.md).
