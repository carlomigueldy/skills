# saas-launch

End-to-end SaaS ideation → PRD → prototype → build-handoff workflow, plus a
deterministic pnpm + Turborepo SaaS monorepo project template.

## Skills

| Skill | Use it for |
| --- | --- |
| [`saas-launch-blueprint`](./skills/saas-launch-blueprint/SKILL.md) | Phases 1–3.5: target-market selection, scored product ideation, an interview-driven PRD, a high-fidelity HTML prototype, then a Phase 3.5 build fork — build it out now in this session (through delivery at GATE 4) or hand off a build prompt for a separate Claude Code session. |
| [`ignition`](./skills/ignition/SKILL.md) | Phase 1: target-market selection. |
| [`flight-plan`](./skills/flight-plan/SKILL.md) | Phase 2: scored product ideation. |
| [`wind-tunnel`](./skills/wind-tunnel/SKILL.md) | Phase 3: interview-driven PRD and high-fidelity HTML prototype. |
| [`countdown`](./skills/countdown/SKILL.md) | Phase 3.5: build fork — build it out now or hand off a build prompt. |
| [`saas-scaffold`](./skills/saas-scaffold/SKILL.md) | Phase 4 (build): instantiates the `saas-monorepo` project template into a target project directory, instead of scaffolding a monorepo from scratch. |

Install all six together — they cross-reference each other across the
ideation → PRD → prototype → build-handoff → scaffold flow.

## Install

| Agent | Install | Notes |
| --- | --- | --- |
| Claude Code (marketplace) | `claude plugin marketplace add carlomigueldy/skills`<br>`claude plugin install saas-launch@carlomigueldy` | Not yet published — see the root [README](../../README.md#install). |
| Codex CLI | `npx skills add carlomigueldy/skills` | Manual: copy `skills/*` into your project's `.agents/skills/` or into `~/.codex/skills/`. |
| OpenCode | `npx skills add carlomigueldy/skills` | Manual: copy `skills/*` into `~/.config/opencode/skills/` or your project's `.agents/skills/`. |
| Claude Cowork / Claude Desktop | Build a zip with `scripts/package-plugin.py` (see the [root README](../../README.md#manual-upload-claude-cowork--claude-desktop)) | No marketplace support in the desktop apps. |

## Template

The `saas-monorepo` and `agent-harness` project templates used by
`saas-scaffold` now live in a separate public repo,
[`carlomigueldy/templates`](https://github.com/carlomigueldy/templates), and
are no longer bundled in this plugin. `saas-scaffold` clones them at scaffold
time into `~/.cache/saas-launch/templates` (network needed the first time;
the cache is reused, including offline, after that). Set
`SAAS_LAUNCH_TEMPLATES_DIR` to point at a local checkout of that repo instead
if you'd rather work fully offline.

`saas-monorepo` is a pnpm + Turborepo monorepo skeleton: Tailwind v4 +
shadcn/ui as the non-negotiable UI stack, a Next.js landing app, a
Vite/React offline-first PWA, a Vite/React mission-control admin console,
and shared `packages/` for schemas, UI tokens, locales, and config — backed
by Supabase (auth, Postgres, RLS, storage). See
`saas-monorepo/SCAFFOLD.md` in the templates repo for the full, authoritative
instantiation sequence.

## Versioning

This plugin's releases are managed by
[release-please](https://github.com/googleapis/release-please); see the
[root `docs/VERSIONING.md`](../../docs/VERSIONING.md) for how that works
across this marketplace. See [`CHANGELOG.md`](./CHANGELOG.md) for this
plugin's release history.
