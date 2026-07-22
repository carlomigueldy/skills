# carlomigueldy/skills

Carlo Miguel Dy's personal agent skills marketplace — Claude Code plugins,
Codex-compatible packages, Grok Build orchestration kits, project templates,
and workflows.

## Install

This repo is a Claude Code plugin marketplace, but its skills are also
installable straight from the top-level `skills/` mirror on any agent that
speaks the emerging `skills/` convention — Codex CLI, OpenCode, and others.
Grok Build uses a separate install path (see [Grok Build setup](#grok-build-setup)).
Pick the row for your agent:

| Agent | Install | Notes |
| --- | --- | --- |
| Claude Code (marketplace) | `claude plugin marketplace add carlomigueldy/skills`<br>`claude plugin install saas-launch@carlomigueldy` | See caveat below — not yet published. |
| Codex CLI | `codex plugin marketplace add carlomigueldy/skills` (reads `.claude-plugin/marketplace.json` and installs `saas-launch` from `plugins/saas-launch/.claude-plugin/plugin.json`), or `npx skills add carlomigueldy/skills` for skills only | See caveat below — not yet published. Manual fallback: copy `skills/*` into your project's `.agents/skills/` or into `~/.codex/skills/`. |
| OpenCode | `npx skills add carlomigueldy/skills` | See caveat below — not yet published. Manual fallback: copy `skills/*` into `~/.config/opencode/skills/` or your project's `.agents/skills/`. |
| Claude Cowork / Claude Desktop | Build a zip with `scripts/package-plugin.py` (see below) | No marketplace support in the desktop apps. |
| **Grok Build** | `python3 scripts/install-grok-build.py` | Copies `ultracode`, `ship-feature` workflow, personas, and roles into `~/.grok/`. See [Grok Build setup](#grok-build-setup). |

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
scripts/package-plugin.py product-foundry # -> dist/product-foundry-<version>-cowork.zip
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

## Grok Build setup

[`plugins/grok-build`](./plugins/grok-build) packages the multi-agent
orchestration kit used with [Grok Build](https://grok.com): the `/ultracode`
skill, the `ship-feature` Rhai workflow, and tiered personas/roles
(architect · sweeper · implementer · reviewer).

### 1. Install Grok Build

Install the Grok CLI and authenticate (API key or `grok login`). Confirm the
binary is on your `PATH` and that `~/.grok/` exists after first launch.

### 2. Install this package into `~/.grok/`

From a clone of this repo:

```bash
git clone https://github.com/carlomigueldy/skills.git
cd skills
python3 scripts/install-grok-build.py          # → ~/.grok/
# python3 scripts/install-grok-build.py --target .grok   # project-local
# python3 scripts/install-grok-build.py --dry-run
```

The installer copies:

| Source | Destination |
| --- | --- |
| `plugins/grok-build/skills/ultracode/` | `~/.grok/skills/ultracode/` |
| `plugins/grok-build/workflows/ship-feature.rhai` | `~/.grok/workflows/ship-feature.rhai` |
| `plugins/grok-build/personas/*.toml` | `~/.grok/personas/` |
| `plugins/grok-build/roles/*.toml` | `~/.grok/roles/` |

Restart the Grok TUI (or open a new session) so discovery reloads.

### 3. Run the orchestration pipelines

```text
/ultracode Add retry + backoff to the payment client
/ultracode --skip-plan Fix the null deref in auth middleware

/workflow ship-feature target="Add retry to the payment client"
```

`/ultracode` is an interactive pure-orchestrator skill (plan gate, parallel
sweeps, implement, verify, adversarial review, fix loops).
`/workflow ship-feature` is the deterministic Rhai harness for the same tier
ladder. Both expect Grok Build subagents (`plan`, `explore`,
`general-purpose`) and native model `grok-4.5` effort/capability tiering —
see [`plugins/grok-build/README.md`](./plugins/grok-build/README.md).

## Plugins

| Plugin | Description | Skills |
| --- | --- | --- |
| [`saas-launch`](./plugins/saas-launch) | End-to-end SaaS ideation → PRD → prototype → build-handoff workflow, plus a deterministic pnpm + Turborepo SaaS monorepo project template | `saas-launch-blueprint`, `saas-scaffold` |
| [`product-foundry`](./plugins/product-foundry) | Cross-platform, approval-gated product discovery → prototype → PRD → go-to-market → implementation-handoff workflow | `product-foundry`, `implement-prd` |
| [`grok-build`](./plugins/grok-build) | Grok Build multi-agent orchestration kit (skill + Rhai workflow + personas/roles) | `ultracode` |

Product Foundry keeps one package-local `skills/` tree shared by its native
Claude and Codex manifests, so it does not need a second top-level mirror. The
older `saas-launch` plugin continues to use the repository's generated
top-level `skills/` mirror for Codex CLI, OpenCode, and `npx skills add`.
`grok-build` is installed into Grok's user/project config via
`scripts/install-grok-build.py` rather than the flat `skills/` mirror.

## Repo layout

```
skills/
├── .claude-plugin/
│   └── marketplace.json          # marketplace definition (lists all plugins; Codex CLI reads this too)
├── plugins/
│   ├── saas-launch/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/             # canonical source for generated mirror
│   ├── product-foundry/
│   │   ├── .claude-plugin/plugin.json # Claude manifest
│   │   ├── .codex-plugin/plugin.json  # Codex manifest
│   │   ├── skills/
│   │   │   ├── product-foundry/SKILL.md
│   │   │   ├── implement-prd/SKILL.md
│   │   │   └── foundry-*/SKILL.md
│   │   └── README.md
│   └── grok-build/
│       ├── .claude-plugin/plugin.json
│       ├── skills/ultracode/
│       ├── workflows/ship-feature.rhai
│       ├── personas/            # architect, sweeper, implementer, reviewer
│       ├── roles/
│       ├── scripts/install.py   # → ~/.grok/
│       └── README.md
├── skills/                        # generated mirror of plugins/saas-launch/skills/
│   └── ...                       # for Codex CLI / OpenCode / `npx skills add` — synced by scripts/sync-skills.py, don't hand-edit
├── scripts/
│   ├── package-plugin.py         # zip a plugin for manual Cowork upload
│   ├── sync-skills.py            # regenerate the top-level skills/ mirror
│   └── install-grok-build.py     # install grok-build into ~/.grok/
├── docs/
│   └── VERSIONING.md
└── README.md
```

## Versioning & releases

This repo follows [Conventional Commits](https://www.conventionalcommits.org/) and uses [release-please](https://github.com/googleapis/release-please) to automate versioning:

- Commits to `main` are analyzed by release-please, which opens (and keeps updated) a release PR per plugin.
- Merging a release PR bumps the package's configured manifest version(s), updates its `CHANGELOG.md`, and cuts a tag scoped to the plugin, e.g. `product-foundry--v0.1.0`.
- Each plugin under `plugins/<name>/` maintains its own `CHANGELOG.md`.

See [`docs/VERSIONING.md`](./docs/VERSIONING.md) for full details on the release process and tag format.

## Adding a new plugin

1. `mkdir -p plugins/<name>/.claude-plugin plugins/<name>/skills`
2. Add the Claude manifest and, when the plugin has native Codex metadata, a `.codex-plugin/plugin.json` with the same semantic version.
3. Add one or more skills under `plugins/<name>/skills/<skill-name>/SKILL.md`
4. Register the plugin in `.claude-plugin/marketplace.json`
5. Add the plugin to the release-please config and manifest so it gets versioned and released independently

## License

MIT
