# carlomigueldy/skills

Carlo Miguel Dy's personal [Claude Code](https://claude.com/claude-code) plugin marketplace — a collection of agent skills, project templates, and workflows packaged as installable plugins.

## Install

This repo is a Claude Code plugin marketplace, but its skills are also
installable straight from the top-level `skills/` mirror on any agent that
speaks the emerging `skills/` convention — Codex CLI, OpenCode, and others.
Pick the row for your agent:

| Agent | Install | Notes |
| --- | --- | --- |
| Claude Code (marketplace) | `claude plugin marketplace add carlomigueldy/skills`<br>`claude plugin install saas-launch@carlomigueldy` | See caveat below — not yet published. |
| Codex CLI | `npx skills add carlomigueldy/skills` | See caveat below — not yet published. Manual fallback: copy `skills/*` into your project's `.agents/skills/` or into `~/.codex/skills/`. |
| OpenCode | `npx skills add carlomigueldy/skills` | See caveat below — not yet published. Manual fallback: copy `skills/*` into `~/.config/opencode/skills/` or your project's `.agents/skills/`. |
| Claude Cowork / Claude Desktop | Build a zip with `scripts/package-plugin.py` (see below) | No marketplace support in the desktop apps. |

> **Not yet published to GitHub.** This repo isn't pushed to GitHub yet, so
> every remote-install row above — the `claude plugin` commands AND the
> `npx skills add carlomigueldy/skills` commands — won't resolve until
> `carlomigueldy/skills` exists there. Use the manual fallbacks in the notes
> column, or the manual-upload path below, until then.

**Install all six skills together.** `saas-launch-blueprint`, `ignition`,
`flight-plan`, `wind-tunnel`, `countdown`, and `saas-scaffold` cross-reference
each other across the ideation → PRD → prototype → build-handoff → scaffold
flow — install and use them as a set, not individually.

**Templates are cloned at scaffold time, not vendored.** The
`saas-monorepo` and `agent-harness` project templates used by
`saas-scaffold` now live in a separate public repo,
[`carlomigueldy/templates`](https://github.com/carlomigueldy/templates), and
are cloned into `~/.cache/saas-launch/templates` on demand. Scaffolding
needs network access the first time (the cache is reused after that,
including offline); set `SAAS_LAUNCH_TEMPLATES_DIR` to point at a local
checkout instead if you'd rather work fully offline.

**`skills/` at the repo root is a generated mirror**, kept in sync with
`plugins/saas-launch/skills/` for agents that read a flat top-level `skills/`
directory (Codex CLI, OpenCode, the `npx skills add` installer). Edit the
skills under `plugins/saas-launch/skills/`, then run
`scripts/sync-skills.py` to regenerate the mirror — don't edit `skills/`
directly.

### Manual upload (Claude Cowork / Claude Desktop)

The desktop apps install a plugin from an uploaded zip rather than from the
marketplace. Build one with:

```bash
scripts/package-plugin.py                 # -> dist/saas-launch-<version>-cowork.zip
scripts/package-plugin.py --list          # preview contents and path rewrites
```

The zip is flat (`.claude-plugin/plugin.json` at the root, no wrapper
directory) because that is what the uploader expects. The uploader also
rejects paths containing ``<>:"|?*\[]`` or non-ASCII characters, so the
script rewrites those segments — `app/[locale]/` ships as `app/__locale__/`
— and bundles a `RESTORE-PATHS.md` and `restore-paths.sh` to reverse it.

**If a zip contains rewritten paths, run `bash restore-paths.sh` after
copying the template out.** Next.js matches dynamic routes on the literal
`[segment]` directory name; left as `__segment__`, every route 404s. This
only affects the manual-upload path — a marketplace install ships the
correct names.

## Plugins

| Plugin | Description | Skills |
| --- | --- | --- |
| [`saas-launch`](./plugins/saas-launch) | End-to-end SaaS ideation → PRD → prototype → build-handoff workflow, plus a deterministic pnpm + Turborepo SaaS monorepo project template | `saas-launch-blueprint`, `saas-scaffold` |

## Repo layout

```
skills/
├── .claude-plugin/
│   └── marketplace.json          # marketplace definition (lists all plugins)
├── plugins/
│   └── saas-launch/
│       ├── .claude-plugin/
│       │   └── plugin.json       # plugin manifest
│       ├── skills/
│       │   ├── saas-launch-blueprint/
│       │   │   └── SKILL.md
│       │   ├── ignition/
│       │   │   └── SKILL.md
│       │   ├── flight-plan/
│       │   │   └── SKILL.md
│       │   ├── wind-tunnel/
│       │   │   └── SKILL.md
│       │   ├── countdown/
│       │   │   └── SKILL.md
│       │   └── saas-scaffold/
│       │       └── SKILL.md
│       └── README.md
├── skills/                        # generated mirror of plugins/saas-launch/skills/
│   └── ...                       # for Codex CLI / OpenCode / `npx skills add` — synced by scripts/sync-skills.py, don't hand-edit
├── scripts/
│   ├── package-plugin.py         # zip a plugin for manual Cowork upload
│   └── sync-skills.py            # regenerate the top-level skills/ mirror
├── docs/
│   └── VERSIONING.md
└── README.md
```

## Versioning & releases

This repo follows [Conventional Commits](https://www.conventionalcommits.org/) and uses [release-please](https://github.com/googleapis/release-please) to automate versioning:

- Commits to `main` are analyzed by release-please, which opens (and keeps updated) a release PR per plugin.
- Merging a release PR bumps that plugin's `version` in its `plugin.json`, updates its `CHANGELOG.md`, and cuts a tag scoped to the plugin, e.g. `saas-launch--v0.1.0`.
- Each plugin under `plugins/<name>/` maintains its own `CHANGELOG.md`.

See [`docs/VERSIONING.md`](./docs/VERSIONING.md) for full details on the release process and tag format.

## Adding a new plugin

1. `mkdir -p plugins/<name>/.claude-plugin plugins/<name>/skills`
2. Add `plugins/<name>/.claude-plugin/plugin.json`
3. Add one or more skills under `plugins/<name>/skills/<skill-name>/SKILL.md`
4. Register the plugin in `.claude-plugin/marketplace.json`
5. Add the plugin to the release-please config and manifest so it gets versioned and released independently

## License

MIT
