# saas-launch

End-to-end SaaS ideation → PRD → prototype → build-handoff workflow, plus a
deterministic pnpm + Turborepo SaaS monorepo project template.

## Skills

| Skill | Use it for |
| --- | --- |
| [`saas-launch-blueprint`](./skills/saas-launch-blueprint/SKILL.md) | Phases 1–3.5: target-market selection, scored product ideation, an interview-driven PRD, a high-fidelity HTML prototype, then a Phase 3.5 build fork — build it out now in this session (through delivery at GATE 4) or hand off a build prompt for a separate Claude Code session. |
| [`saas-scaffold`](./skills/saas-scaffold/SKILL.md) | Phase 4 (build): instantiates this plugin's bundled `saas-monorepo` project template into a target project directory, instead of scaffolding a monorepo from scratch. |

## Template

`templates/saas-monorepo/` is a pnpm + Turborepo monorepo skeleton: Tailwind
v4 + shadcn/ui as the non-negotiable UI stack, a Next.js landing app, a
Vite/React offline-first PWA, a Vite/React mission-control admin console,
and shared `packages/` for schemas, UI tokens, locales, and config — backed
by Supabase (auth, Postgres, RLS, storage). See
[`templates/saas-monorepo/SCAFFOLD.md`](./templates/saas-monorepo/SCAFFOLD.md)
for the full, authoritative instantiation sequence.

## Versioning

This plugin's releases are managed by
[release-please](https://github.com/googleapis/release-please); see the
[root `docs/VERSIONING.md`](../../docs/VERSIONING.md) for how that works
across this marketplace. See [`CHANGELOG.md`](./CHANGELOG.md) for this
plugin's release history.
