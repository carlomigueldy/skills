# Changelog

All notable changes to the `saas-launch` plugin will be documented in this
file.

This project's releases are managed by
[release-please](https://github.com/googleapis/release-please) from this
point forward — entries below the `0.1.0` heading are generated
automatically from Conventional Commits on future releases; do not hand-edit
past this initial entry.

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
