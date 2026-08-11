# Versioning & releases

This repo uses [release-please](https://github.com/googleapis/release-please)
to automate versioning for each plugin independently, driven by
[Conventional Commits](https://www.conventionalcommits.org/) on `main`.

## How it works

1. Every commit merged to `main` is analyzed by the `release-please` GitHub
   Actions workflow (`.github/workflows/release.yml`).
2. release-please opens (and keeps up to date) one release pull request per
   package configured in `release-please-config.json`: currently
   `plugins/saas-launch`, `plugins/product-foundry`, `plugins/orchestra`, and
   `plugins/herdcraft`.
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
| `.github/workflows/validate.yml` | Runs JSON, Claude plugin, Product Foundry contract, Orchestra contract, validator, and package-layout checks on every push/PR. |
| `package.json` | Root pi package manifest (`pi.skills`) plus repository tooling. Not release-managed. |

## The root `package.json` is not release-managed

The repository-root `package.json` carries the pi package manifest and the
commitlint/husky tooling. It is `private`, pinned at `0.0.0`, and has no
entry in `release-please-config.json` or `.release-please-manifest.json`.
Nothing versions it, and no `package.json` in this repository is ever
listed in an `extra-files` array.

## Adding a new plugin to the release pipeline

When you add a new plugin under `plugins/<name>/` (see the root `README.md`'s
"Adding a new plugin" steps), also:

1. Add a `plugins/<name>` entry to `release-please-config.json`'s `packages`
   map, with its own `component` name.
2. Add a `plugins/<name>` entry to `.release-please-manifest.json` set to the
   current package version.
3. Add every host manifest the plugin actually ships as a package-local
   `extra-files` target so release-please keeps them in sync. A Codex-only
   plugin lists `.codex-plugin/plugin.json` and does not invent a Claude
   manifest solely for versioning.
4. Do **not** give the plugin its own `package.json`. pi discovers a plugin
   package by convention, and a per-plugin `package.json` would add a fourth
   version to keep in lockstep through release-please's special-cased
   `package.json` updater.

## Tag format

Tags are scoped per plugin so multiple plugins can release independently
without colliding: `<plugin-name>--v<version>`, e.g. `saas-launch--v0.1.0`.
