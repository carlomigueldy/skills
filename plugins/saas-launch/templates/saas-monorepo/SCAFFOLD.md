# SCAFFOLD.md — saas-monorepo template

This is the source of truth for turning this template into a real product
repo. It is deterministic on purpose: run the same commands, in the same
order, and every {{PRODUCT_NAME}}-style product ends up with the same
structure, the same config file locations, and the same verification gate.
If a step here is unclear or out of date, fix this file — don't improvise
around it.

## 1. What this template is

A pnpm + Turborepo monorepo skeleton for a multi-tenant SaaS product, built
around one non-negotiable UI stack (Tailwind v4 + shadcn/ui) and one
non-negotiable backend (Supabase: auth, Postgres, RLS, storage).

Layout:

```
.
├── apps/
│   ├── landing/            Next.js App Router marketing site (next-intl)
│   ├── pwa/                Mobile-first offline-capable PWA (Vite + React)
│   └── mission-control/    Admin console (Vite + React)
├── packages/
│   ├── config/              shared tsconfig + eslint flat config
│   ├── schemas/              zod schemas — single source of truth for domain types
│   ├── locales/              en / tl / taglish message catalogs
│   └── ui/                   design tokens + shadcn/ui component output
├── package.json
├── pnpm-workspace.yaml
├── turbo.json
├── .npmrc
└── .gitignore
```

This document (root files + `packages/`) is authored once, here, in the
plugin template. `apps/*` are scaffolded by their own generators but consume
`packages/*` the same way described below in every product.

## 2. Placeholder reference

Every occurrence of these tokens across the template must be substituted
before `pnpm install`. Do a literal find-and-replace — there is no build
step that resolves them for you.

| Placeholder             | Meaning                                              | Example                          |
|--------------------------|-------------------------------------------------------|-----------------------------------|
| `{{PRODUCT_NAME}}`       | Human-readable product name, used in UI copy & docs   | `Kabisa`                          |
| `{{PRODUCT_SLUG}}`       | Lowercase, hyphenated, used as npm scope + repo name  | `kabisa`                          |
| `{{PRODUCT_DESCRIPTION}}`| One-line description, used in root `package.json`    | `Inventory ops for sari-sari stores` |
| `{{PRIMARY_LOCALE}}`     | Default locale code, must be a key in `packages/locales` | `en`                          |
| `{{CONTACT_EMAIL}}`      | Support/owner contact, used in `package.json` author  | `hello@kabisa.app`               |

`{{PRODUCT_SLUG}}` becomes the workspace package scope: every internal
package is published as `@{{PRODUCT_SLUG}}/config`, `@{{PRODUCT_SLUG}}/schemas`,
`@{{PRODUCT_SLUG}}/locales`, `@{{PRODUCT_SLUG}}/ui`.

## 3. Step-by-step instantiation

### 3.1 Copy the template

```bash
cp -R plugins/saas-launch/templates/saas-monorepo/ path/to/new-product/
cd path/to/new-product/
```

### 3.2 Substitute placeholders

Run across the whole tree (root files + `packages/`; `apps/` generators do
their own substitution the same way):

```bash
grep -rl '{{PRODUCT_NAME}}\|{{PRODUCT_SLUG}}\|{{PRODUCT_DESCRIPTION}}\|{{PRIMARY_LOCALE}}\|{{CONTACT_EMAIL}}' . \
  --exclude-dir=node_modules \
  | xargs sed -i '' \
      -e 's/{{PRODUCT_NAME}}/Kabisa/g' \
      -e 's/{{PRODUCT_SLUG}}/kabisa/g' \
      -e 's/{{PRODUCT_DESCRIPTION}}/Inventory ops for sari-sari stores/g' \
      -e 's/{{PRIMARY_LOCALE}}/en/g' \
      -e 's/{{CONTACT_EMAIL}}/hello@kabisa.app/g'
```

(Drop the trailing `''` after `-i` on GNU sed / Linux.)

Verify nothing was missed:

```bash
grep -rn '{{PRODUCT_NAME}}\|{{PRODUCT_SLUG}}\|{{PRODUCT_DESCRIPTION}}\|{{PRIMARY_LOCALE}}\|{{CONTACT_EMAIL}}' . \
  --exclude-dir=node_modules --exclude-dir=.git
```

(Scoped to the five known placeholder tokens, not a bare `{{` — a bare
`{{` also matches unrelated `${{ }}` GitHub Actions expression syntax in
`.github/workflows/ci.yml` and would produce false-positive "leftovers".)

### 3.3 Install

```bash
pnpm install
```

This resolves the workspace graph (`pnpm-workspace.yaml`) and generates
`pnpm-lock.yaml` fresh for this product — see §6 for why the lockfile is
never part of the template itself.

### 3.4 shadcn/ui — verify the vendored setup, don't re-init

shadcn/ui components are **already vendored** in this template — they ship
pre-generated in `packages/ui/src/components/ui/`, so there is no `shadcn
init` or `shadcn add` step at scaffold time. Verify the vendored setup
instead of generating it:

```bash
ls packages/ui/src/components/ui/
cat packages/ui/components.json
```

You should see 14 components (`badge.tsx`, `button.tsx`, `card.tsx`,
`dialog.tsx`, `dropdown-menu.tsx`, `form.tsx`, `input.tsx`, `label.tsx`,
`select.tsx`, `sheet.tsx`, `skeleton.tsx`, `sonner.tsx`, `table.tsx`,
`tabs.tsx`) plus `packages/ui/src/lib/utils.ts` (the `cn()` helper) and
`packages/ui/src/index.ts` (re-exports all of the above). `style` in
`components.json` should read `new-york-v4` — that's the style this
template's `packages/ui/src/tokens.css` CSS-variable naming and
`--radius-*` calc convention was built to match. Each app
(`apps/landing`, `apps/pwa`, `apps/mission-control`) also has its own
`components.json` for `shadcn` CLI file-placement conventions if it ever
adds app-local components directly, but none of the 14 baseline components
are duplicated per-app — they're consumed from `packages/ui` via
`@{{PRODUCT_SLUG}}/ui`.

If any of the above is missing, the template itself is broken — fix
`templates/saas-monorepo` upstream in this plugin, don't route around it by
running `shadcn init` inside the product repo.

### 3.5 OPTIONAL — add more components

The 14 vendored components (§3.4) are the baseline. If the PRD needs a
component beyond that list, add it with the bundled `shadcn` agent skill
(vendored into every scaffolded project at `.claude/skills/shadcn/`) rather
than improvising the CLI invocation from memory — invoke it (or just ask
for the component by name; it's an agent skill, not a slash command) and
let it run the CLI against `packages/ui`'s existing `components.json`. It
already knows this project's aliases, `new-york-v4` style, and Tailwind v4
setup from that file. Equivalent manually:

```bash
cd packages/ui
pnpm dlx shadcn@latest add <component-name>
```

Same caveat as the original vendoring pass: this template's component
source uses relative imports (`../../lib/utils`, `./button`), not the
`@/...` aliases `components.json` declares — the CLI writes `@/...` by
default, so convert any newly-added component's imports to match the
existing relative-import convention in `packages/ui/src/components/ui/`
before committing it. Re-export the new component from
`packages/ui/src/index.ts` alongside the existing 14.

### 3.6 Wire `packages/ui` tokens into each app

In each app's global stylesheet (`apps/landing/app/globals.css`,
`apps/pwa/src/index.css`, `apps/mission-control/src/styles.css` — that's
the file `apps/mission-control/src/main.tsx` actually imports; there is no
`index.css` in that app), keep the app's own `@import "tailwindcss";` as
the first line, then import the shared tokens right after it:

```css
@import "tailwindcss";
@import "@{{PRODUCT_SLUG}}/ui/tokens.css";
```

`packages/ui/src/tokens.css` does not import `"tailwindcss"` itself — it's
meant to load after the app's own Tailwind import, not stand alone; see
the doc comment at the top of that file. Together these two lines are what
make `--background`, `--primary`, `--radius`, etc. — and therefore every
vendored shadcn/ui component — resolve to the shared design system in
`packages/ui/src/tokens.css`. This should already be wired in every app's
scaffold-generated stylesheet; §3.4's verification step covers confirming
it's present. It only needs doing by hand if an app's stylesheet was
regenerated from scratch after copying the template.

### 3.7 Generate real icon assets

`apps/landing/public/site.webmanifest` references `/icon-192.png` and
`/icon-512.png`, and `apps/pwa/vite.config.ts`'s PWA manifest references
`/pwa-192x192.png` and `/pwa-512x512.png` (see the `TODO(scaffold)` comment
there) — none of these raster files are vendored in the template. Generate
real ones per product (e.g. via `pnpm dlx pwa-asset-generator`) from the
product's actual logo before shipping; a missing icon fails Lighthouse's
PWA installability checks and shows a broken icon in OS install prompts.

## 4. Verification commands

Run after instantiation, and again after any structural change:

```bash
pnpm turbo run lint typecheck build
pnpm turbo run test
```

Both must exit 0 before the product repo's CI is trusted. CI (GitHub
Actions) runs the same two commands, plus Playwright — see
`.github/workflows/` in the app-level scaffolds.

## 5. Surface trimming rules

Not every product needs all three apps on day one. Trimming a surface must
not break `pnpm turbo run *` for what remains:

- **To drop `apps/pwa` or `apps/mission-control`:** delete the app
  directory. `pnpm-workspace.yaml` already globs `apps/*`, so no config
  edit is required there. Remove any cross-app references (e.g. a landing
  page link to the dropped app) and any CI job matrix entry naming it.
- **To drop `apps/landing`:** same as above; if the product is
  admin-tool-only or PWA-only with no public marketing site, this is safe
  to remove entirely.
- **Never trim `packages/schemas`.** It's the domain source of truth even
  for a single-surface product — keep it even if only one app consumes it.
- **`packages/locales`:** trim the locale *files* (e.g. drop `taglish.json`)
  if the product only ships `en`/`tl`, but keep the package and update
  `defaultLocale` / the `locales` map in `src/index.ts` to match — don't
  leave dangling imports.
- **`packages/ui` and `packages/config` are never trimmed** — every
  remaining app depends on both.
- After trimming, re-run §4's verification commands before committing.

## 6. What is intentionally NOT vendored, and why

- **`node_modules/`** — never committed. Installed fresh per product via
  `pnpm install` against each product's own `pnpm-lock.yaml`, so dependency
  resolution reflects that product's actual dependency graph, not whatever
  happened to be installed when this template was last touched.
- **shadcn/ui component output is now vendored, deliberately** —
  `packages/ui/src/components/ui/` ships the 14 baseline components
  (`badge`, `button`, `card`, `dialog`, `dropdown-menu`, `form`, `input`,
  `label`, `select`, `sheet`, `skeleton`, `sonner`, `table`, `tabs`)
  pre-generated against `new-york-v4` and this template's own
  `packages/ui/src/tokens.css` values (see §3.4). This reverses the
  template's earlier stance of generating components at scaffold time —
  vendoring removes an entire deterministic-but-flaky CLI step (network
  access, CLI version drift, preset changes) from every product's first
  hour, at the cost of needing an occasional manual re-vendor pass in this
  template when shadcn/ui ships upstream changes worth pulling in. Stays
  upgradeable the same way either way: `shadcn diff` / `shadcn add
  --overwrite`, run via the bundled `shadcn` agent skill (§3.5) or by hand.
- **`pnpm-lock.yaml`** — not part of the template. A lockfile encodes exact
  resolved versions for one dependency graph at one point in time; carrying
  one across unrelated products would either be meaningless (paths don't
  match) or actively wrong (pins versions that predate the product's own
  `pnpm install`). Each product generates its own at §3.3.
