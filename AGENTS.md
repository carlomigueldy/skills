# Repository Agent Rules

This repository packages installable coding-agent plugins. `plugins/` contains each source package, `skills/` contains generated marketplace mirrors, `scripts/` contains validation and packaging tools, and `tests/` contains repository contracts. The portable operations harness is in `docs/agent-harness/`.

## Working rules

- Treat plugin packages as source and generated mirrors as outputs. Do not hand-edit generated files or paths marked by `skills/.generated`; use the owning generator and verify that regenerated output is current.
- Keep each change focused and preserve host compatibility. Follow [the lifecycle and modes](docs/agent-harness/README.md) for plugin maintenance, creation, refinement, testing, or red-team work.
- External writes require explicit authorization. This includes commits, pushes, pull requests, issues, releases, publishing, deployments, and authenticated messages. Never expose secrets or weaken repository policy.
- Git authorship and committer metadata must use an approved human identity. Agents must never change `user.name` or `user.email`, use an author override, or add generated-by, assisted-by, sign-off, or model attribution. Only the narrowly configured release automation exception may use a bot identity.
- Commit titles use Conventional Commits with a lowercase type: `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `revert`, `style`, or `test`. A lowercase scope and breaking-change syntax are optional.
- Verification is required in proportion to risk. Run focused tests while editing, then the applicable repository validation, generated-mirror check, packaging checks, and `git diff --check`. Report failures accurately; do not bypass hooks or required checks.

Use [roles](docs/agent-harness/roles.md) for ownership and delegation, [lifecycle](docs/agent-harness/lifecycle.md) for sequencing, [modes](docs/agent-harness/modes.md) for task boundaries, and [red-team](docs/agent-harness/red-team.md) for adversarial review and findings.
