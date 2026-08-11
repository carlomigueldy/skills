# Herdcraft

Herdcraft is a Codex-only plugin for delivering features and products through
bounded autonomous agent teams managed in Herdr. It keeps product contracts,
ownership, verification evidence, incidents, model assignments, resource
usage, and teardown state in a restart-safe repository ledger.

## Requirements

- Codex with plugin support
- Herdr with its Codex integration configured and `HERDR_ENV=1`
- Git when concurrent writers need isolated worktrees
- The `herdr` and `find-skills` Codex skills installed in the target repository

Install the two externally maintained prerequisite skills repo-locally from
the target repository (do not add `-g`):

```bash
npx skills add ogulcancelik/herdr@herdr
npx skills add vercel-labs/skills@find-skills
```

Herdcraft does not vendor those independently versioned skills, install the
Herdr application, grant credentials, configure MCP servers, or authorize
deployments. Preflight stops if either required skill is unavailable; optional
capabilities are recorded as constraints instead of being assumed.

## Install

```bash
codex plugin marketplace add carlomigueldy/skills
codex plugin add herdcraft@carlomigueldy
```

Start a new Codex thread after installation, then invoke `$herdcraft` with a
feature, product, research, recovery, or release goal.

## Included surface

- `skills/herdcraft/`: orchestration policy, specialist roster, delivery
  profiles, task/team contracts, capability ledger, reporting, and teardown
- `scripts/init-run.py`: safely scaffold a durable run ledger in a Git repo
- `scripts/validate-run.py`: validate a run's minimum reconstructable state
- `scripts/summarize-run.py`: render a concise workflow summary from run state

The scripts use only the Python standard library. Run `--help` for their
arguments. The skill remains authoritative for decisions and safety gates;
the scripts only automate deterministic ledger operations.

Herdcraft complements the repository's `orchestra` plugin. Orchestra is a
host-agnostic workflow router; Herdcraft is the Codex-and-Herdr-specific
delivery control plane for team leads, worktrees, capability budgets,
integration, release evidence, and teardown.

## Codex-only scope

Version 1 intentionally ships only `.codex-plugin/plugin.json` and is listed
only in the Codex-native `.agents/plugins/marketplace.json`. It is not exposed
through the Claude marketplace, the repository pi package, or the generated
cross-agent `skills/` mirror.
