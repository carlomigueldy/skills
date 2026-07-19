# Versioning & releases

This repo uses [release-please](https://github.com/googleapis/release-please)
to automate versioning for each plugin independently, driven by
[Conventional Commits](https://www.conventionalcommits.org/) on `main`.

## How it works

1. Every commit merged to `main` is analyzed by the `release-please` GitHub
   Actions workflow (`.github/workflows/release.yml`).
2. release-please opens (and keeps up to date) one release pull request per
   package configured in `release-please-config.json`. Today that's a single
   package: `plugins/saas-launch`.
3. Merging a release PR:
   - Bumps the package's version in `plugins/saas-launch/.claude-plugin/plugin.json`.
   - Updates the matching entry in the root `.claude-plugin/marketplace.json`
     (`plugins[0].version`) via the `extra-files` config, so the two never
     drift out of sync.
   - Appends a new entry to `plugins/saas-launch/CHANGELOG.md`.
   - Cuts a tag scoped to the plugin, in the form `saas-launch--vX.Y.Z`.
4. `.release-please-manifest.json` tracks the last-released version per
   package; release-please reads and updates it directly — don't hand-edit it
   outside of a release PR merge.

## Configuration files

| File | Purpose |
| --- | --- |
| `release-please-config.json` | Declares each package, its release type, and any `extra-files` that also need their version bumped (e.g. `marketplace.json`). |
| `.release-please-manifest.json` | Tracks the last-released version per package path. |
| `.github/workflows/release.yml` | Runs `googleapis/release-please-action` on every push to `main`. |
| `.github/workflows/validate.yml` | Runs `claude plugin validate` and a JSON sanity pass on every push/PR. |

## Adding a new plugin to the release pipeline

When you add a new plugin under `plugins/<name>/` (see the root `README.md`'s
"Adding a new plugin" steps), also:

1. Add a `plugins/<name>` entry to `release-please-config.json`'s `packages`
   map, with its own `component` name.
2. Add a `plugins/<name>` entry to `.release-please-manifest.json` set to
   that plugin's current `version` in `plugin.json`.
3. If the plugin's version is duplicated anywhere else (e.g. `marketplace.json`),
   add it as an `extra-files` target so release-please keeps it in sync.

## Tag format

Tags are scoped per plugin so multiple plugins can release independently
without colliding: `<plugin-name>--v<version>`, e.g. `saas-launch--v0.1.0`.
