# carlomigueldy/skills

Carlo Miguel Dy's personal [Claude Code](https://claude.com/claude-code) plugin marketplace — a collection of agent skills, project templates, and workflows packaged as installable plugins.

## Install

> **Not yet published.** This repo isn't pushed to GitHub yet, so the
> commands below won't resolve until `carlomigueldy/skills` exists there.
> Once it's pushed, add this marketplace to Claude Code, then install a
> plugin from it:

```bash
claude plugin marketplace add carlomigueldy/skills
claude plugin install saas-launch@carlomigueldy
```

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
│       │   └── saas-scaffold/
│       │       └── SKILL.md
│       └── README.md
├── scripts/
│   └── package-plugin.py         # zip a plugin for manual Cowork upload
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
