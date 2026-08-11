# Workflow report

## Outcome

- Run ID/status: `<values>`
- Shipped scope: `<summary>`
- Integration revision: `<sha-or-none>`
- Deployment: `<status-or-not-requested>`

## Topology and models

- Teams activated: `<count and names>`
- Agents spawned: `<total; root/leads/workers>`
- Dispatch waves/peak concurrency: `<observed values or unavailable>`
- Model assignments: `<model, effort, specialist, task, count>`
- Fallbacks/roster overrides: `<details or none>`
- Retries/failures/cancellations: `<counts>`

## Delivery evidence

- Included/rejected commits and artifacts: `<details>`
- Task/integration/product/operational gates: `<commands and observed outcomes>`
- Independent verification: `<result>`
- Incidents: `<actual incidents and disposition, or none>`

## Delivery profile and capabilities

- Delivery level/constraints: `<profile and binding limits>`
- Tradeoffs/deferred work: `<decisions>`
- Agent/skill/tool budgets versus actuals: `<comparison>`
- Repo-local skills installed: `<name, source/ref, commit, loaded-by agents, or none>`
- Skills rejected and reasons: `<details or none>`
- Tool assignments and evidence: `<Playwright/Chrome DevTools/Sentry/agent-browser/other>`
- Missing capabilities or connections: `<constraints or none>`

## Retirement

- Retired agents/panes/worktrees/processes/listeners: `<inventory>`
- Retained resources and reasons: `<inventory or none>`
- Retirement failures: `<details or none>`
- Final absence verification: `<evidence>`

## Usage telemetry

- Token availability: `<available|partial|unavailable>`
- Token source: `<provider/tool-or-none>`
- Prompt/completion/total tokens: `<observed numbers or null>`
- Agents missing token data: `<count/list>`
- Context availability/source: `<available|partial|unavailable; source>`
- Per-agent context usage: `<observed values or []>`
- Limitation: `<exact reason or none>`

Never estimate unavailable usage. Use `null`, not `0`.

## Residual risk

- Assumptions: `[]`
- Residual risks: `[]`
- Skipped/unavailable checks: `[]`
- Outstanding human gates: `[]`
- Rollback target: `<value-or-not-applicable>`
