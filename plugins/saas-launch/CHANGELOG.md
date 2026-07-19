# Changelog

All notable changes to the `saas-launch` plugin will be documented in this
file.

This project's releases are managed by
[release-please](https://github.com/googleapis/release-please) from this
point forward — entries below the `0.1.0` heading are generated
automatically from Conventional Commits on future releases; do not hand-edit
past this initial entry.

## [0.4.1](https://github.com/carlomigueldy/skills/compare/saas-launch--v0.4.0...saas-launch--v0.4.1) (2026-07-19)


### Bug Fixes

* **saas-launch:** reference bundled saas-monorepo template in PRD scaffold guidance ([#13](https://github.com/carlomigueldy/skills/issues/13)) ([0e0670a](https://github.com/carlomigueldy/skills/commit/0e0670a65eb23ac03fb622df65f61a297fcce7af))
* **saas-launch:** require per-option descriptions in every AskUserQuestion call ([#10](https://github.com/carlomigueldy/skills/issues/10)) ([7b60997](https://github.com/carlomigueldy/skills/commit/7b60997ccc239340c9d46e819d77d3517d058b1d))

## [0.4.0](https://github.com/carlomigueldy/skills/compare/saas-launch--v0.3.0...saas-launch--v0.4.0) (2026-07-19)


### Features

* **saas-launch:** always-asked CTA contact collection, video CTA ending, and app footer attribution ([#6](https://github.com/carlomigueldy/skills/issues/6)) ([e49438d](https://github.com/carlomigueldy/skills/commit/e49438df92af0d6b27e9a4274a2bfce2f3e96b0e))
* **saas-launch:** require PWA install prompt in PRD guidance and quality bar ([#8](https://github.com/carlomigueldy/skills/issues/8)) ([8aa2758](https://github.com/carlomigueldy/skills/commit/8aa2758633dd18c1e46f320c1e8625ed789ce979))


### Bug Fixes

* **saas-launch:** shorten plugin description to meet 500-char limit ([#9](https://github.com/carlomigueldy/skills/issues/9)) ([219301d](https://github.com/carlomigueldy/skills/commit/219301d9e39dfa3d308218119183a800f20a9d90))

## [0.3.0](https://github.com/carlomigueldy/skills/compare/saas-launch--v0.2.0...saas-launch--v0.3.0) (2026-07-19)


### Features

* **saas-launch:** four-tier deterministic agent-harness template + Phase 2 harness interview ([#5](https://github.com/carlomigueldy/skills/issues/5)) ([8b088d9](https://github.com/carlomigueldy/skills/commit/8b088d9f2873ce7b88623ed313849420dcfbe5c2))
* **saas-launch:** vendor shadcn/ui into template and bundle shadcn agent skill ([8fdf761](https://github.com/carlomigueldy/skills/commit/8fdf7611b4908b6cc05de7934e32ce4cc6772056))

## [0.2.0](https://github.com/carlomigueldy/skills/compare/saas-launch--v0.1.0...saas-launch--v0.2.0) (2026-07-19)


### Features

* **saas-launch:** vendor shadcn/ui into template and bundle shadcn agent skill ([8fdf761](https://github.com/carlomigueldy/skills/commit/8fdf7611b4908b6cc05de7934e32ce4cc6772056))

## 0.1.0 (2026-07-19)

Initial release.

### Added

- Migrated the `saas-launch-blueprint` skill from Claude Desktop into this
  plugin (end-to-end SaaS ideation → PRD → prototype → build-handoff
  workflow).
- New `saas-scaffold` skill: instantiates the plugin's bundled
  `saas-monorepo` project template for the Phase 4 build step, instead of
  scaffolding a SaaS monorepo from scratch.
- Bundled `saas-monorepo` project template: pnpm + Turborepo monorepo with
  Tailwind v4 + shadcn/ui as the non-negotiable UI stack, a Next.js landing
  app, a Vite/React offline-first PWA, a Vite/React mission-control admin
  console, and shared `packages/` for schemas, UI tokens, locales, and
  config — backed by Supabase (auth, Postgres, RLS, storage).
