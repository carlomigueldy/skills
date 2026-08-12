# Capabilities and Delivery

Read this reference during preflight, before installing repo-local skills, and before assigning browser or observability tools.

## Contents

1. Start outside a repository
2. Choose the delivery level
3. Avoid overengineering
4. Discover and install repo-local skills
5. Load skills into child agents
6. Route tools by evidence need

## Start outside a repository

Resolve the operating root before creating run state or worktrees:

1. Run `git rev-parse --show-toplevel` from the requested CWD.
2. If it succeeds, use the returned root, even when CWD is a subdirectory.
3. If the request is research, analysis, or planning only, remain non-repository and do not create worktrees.
4. If the user identifies existing code elsewhere, locate the bounded candidate or request the exact path; do not scan or mutate broad unrelated directories.
5. If creating a new product, create an explicit child project directory and initialize Git there. Never initialize a home directory, workspace collection, or other broad parent as the repository. Create a minimal root-owned bootstrap commit before attempting any worktree or capability branch; an empty repository has no valid worktree base revision.
6. If existing unversioned code should become a repository, obtain approval before `git init` and inspect ignore/secrets risk first.
7. If Git is declined, use one writer, disable worktrees, record reduced isolation, and keep backups/diffs appropriate to the task.

Do not create `.herdcraft/` in an unrelated non-repository CWD merely to continue autonomously. In a repository, keep the root `.herdcraft/` entry in `.gitignore`.

## Choose the delivery level

Copy `assets/delivery-profile.yaml` and record constraints before team selection:

- `research-only`: evidence and recommendations; no product mutation.
- `prototype`: disposable learning artifact; never imply production readiness.
- `bounded-production`: smallest maintainable production change for known requirements.
- `critical`: security, money, sensitive data, migration, high availability, or irreversible risk requires deeper verification.

Choose the lowest level that honestly satisfies the delivery target and risk. Promote only when observed constraints require it.

## Avoid overengineering

Root and every lead must state:

- User outcome and deadline
- Existing stack and conventions to reuse
- Current users/load and credible near-term scale
- Security, privacy, compliance, data, and rollback constraints
- Weekly usage, time, agent, concurrency, skill-install, and retry budgets
- Chosen tradeoffs and explicitly deferred work
- Evidence that would promote the delivery level

Prefer the minimum sufficient architecture. Reject speculative services, abstractions, frameworks, configuration, generalization, scaling, and agents that do not change an acceptance or risk decision. Do not weaken security, correctness, accessibility, data integrity, or rollback merely to call work "simple."

At every decomposition, ask: can one bounded agent deliver this safely? Add a child only for independent ownership, specialization, parallelism, or independent verification.

## Discover and install repo-local skills

**REQUIRED SUB-SKILL:** Use `find-skills` when a concrete capability gap may be filled by an installable skill. Resolve its exact `SKILL.md` path in the lead contract, require the lead to read it completely before discovery, and record lead loading evidence in the capability ledger.

For each active team:

1. Inspect repository instructions and existing repo-local skills first.
2. Derive search queries from actual tasks and stack, not generic categories.
3. Check reputable/popular candidates, then use `npx skills find <query>` when needed.
4. Vet source reputation, install count, repository stars, pinned source/ref, license, SKILL.md, scripts, dependencies, and overlap with installed guidance.
5. Record candidates and accept/reject reasons in `assets/capability-ledger.yaml`.
6. Install only an accepted missing skill with `npx skills add <package>` from the team worktree. Never use `-g`; the user requested repository-level installation.
7. Inspect the resulting diff and installed instructions. Do not execute bundled scripts merely because installation succeeded.
8. Commit the capability change, then create child writer worktrees from that commit so every child sees the same pinned skills. If children already exist, reconcile the capability commit explicitly before dispatch.

Default to zero installs. Install only when the delivery profile permits it and the skill changes a concrete task or verification decision. Do not install overlapping skills for every agent.

If network access, trust, licensing, repository policy, or mutation authority blocks installation, record the candidate and continue with existing skills/general capability when safe; otherwise escalate.

## Load skills into child agents

Installation and loading are separate events. Add exact required skill names/paths and purpose to each task contract. Instruct the child to read every required SKILL.md completely before task actions and to report whether it loaded successfully.

Load the minimum task-relevant set. A lead must not dump its entire skill catalog into every child context. Root audits installed-skill changes and may inspect any child assignment; leads own normal loading and compliance within their team.

## Route tools by evidence need

Inventory configured tools before assigning them. A skill does not create an MCP connection or grant credentials.

| Tool | Primary use | Typical owner |
|---|---|---|
| Playwright MCP | Deterministic browser journeys and end-to-end acceptance | Quality lead/reviewer |
| Chrome DevTools MCP | DOM, console, network, accessibility, memory, and performance diagnosis | Investigator or quality lead |
| Sentry MCP | Existing issues, traces, releases, and post-deploy runtime evidence | Quality/platform lead, usually read-only |
| `agent-browser` | Fast browser smoke checks and lightweight automation | Builder or verifier |

Choose one primary tool for each evidence question. Use additional tools only when they answer a distinct uncertainty. Record tool, owner, purpose, target, authority, evidence path, result, and fallback.

Do not create Sentry projects, mutate monitoring, acquire credentials, or deploy merely because Sentry MCP is available. Do not let builder smoke checks self-certify the product gate.
