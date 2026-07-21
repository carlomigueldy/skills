# Versioning & releases

This repo uses [release-please](https://github.com/googleapis/release-please)
to automate versioning for each plugin independently, driven by
[Conventional Commits](https://www.conventionalcommits.org/) on `main`.

## How it works

1. Every commit merged to `main` is analyzed by the `release-please` GitHub
   Actions workflow (`.github/workflows/release.yml`).
2. release-please opens (and keeps up to date) one release pull request per
   package configured in `release-please-config.json`: currently
   `plugins/saas-launch` and `plugins/product-foundry`.
3. Merging a release PR:
   - Bumps the package's configured manifest version or versions via that
     package's `extra-files` config. Marketplace entries deliberately carry no
     version field, so package-local manifests remain the source of truth.
     (release-please rejects `../` paths in `extra-files`, so syncing a root
     file from a package is not possible.)
   - Uses release-please's `simple` release type for each package, which keeps
     its package-local `version.txt` and `CHANGELOG.md` as the primary release
     files; only additional host manifests need `extra-files` synchronization.
   - Appends a new entry to the package's `CHANGELOG.md`.
   - Cuts a tag scoped to the plugin, in the form `product-foundry--vX.Y.Z`.
4. `.release-please-manifest.json` tracks the last-released version per
   package; release-please reads and updates it directly — don't hand-edit it
   outside of a release PR merge.

## Configuration files

| File | Purpose |
| --- | --- |
| `release-please-config.json` | Declares each package, its release type, and any `extra-files` inside the package that also need their version bumped (e.g. `plugin.json`). Paths must stay within the package directory. |
| `.release-please-manifest.json` | Tracks the last-released version per package path. |
| `.github/workflows/release.yml` | Runs `googleapis/release-please-action` on every push to `main`. |
| `.github/workflows/validate.yml` | Runs JSON, Claude plugin, Product Foundry contract, validator, and package-layout checks on every push/PR. |

## Adding a new plugin to the release pipeline

When you add a new plugin under `plugins/<name>/` (see the root `README.md`'s
"Adding a new plugin" steps), also:

1. Add a `plugins/<name>` entry to `release-please-config.json`'s `packages`
   map, with its own `component` name.
2. Add a `plugins/<name>` entry to `.release-please-manifest.json` set to the
   current package version.
3. Add `.claude-plugin/plugin.json` and any additional host manifest, such as
   `.codex-plugin/plugin.json`, as package-local `extra-files` targets so
   release-please keeps them in sync.

## Tag format

Tags are scoped per plugin so multiple plugins can release independently
without colliding: `<plugin-name>--v<version>`, e.g. `saas-launch--v0.1.0`.
