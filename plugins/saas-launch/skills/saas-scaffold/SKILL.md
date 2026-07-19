---
name: saas-scaffold
description: Use when starting the Phase 4 build of a SaaS Launch Blueprint PRD, when scaffolding a new SaaS monorepo, or when the user asks to "scaffold the saas template" / "use my saas starter". Instantiates the plugin's bundled pnpm + Turborepo SaaS monorepo template (Tailwind v4 + shadcn/ui, Next.js landing, Vite PWA, Vite mission-control, Supabase backend) into a target project directory instead of scaffolding a monorepo from scratch.
---

# saas-scaffold

Scaffold a new SaaS product monorepo from the `saas-launch` plugin's bundled
template — never hand-build a monorepo structure, package.json graph, or UI
stack from memory when this skill applies. The template is maintained once,
in this plugin, so every product scaffolded from it gets the same commands,
the same structure, and the same token file locations.

## When this applies

- Phase 4 ("build") of a SaaS Launch Blueprint PRD, immediately after the PRD
  and prototype phases are done and it's time to produce a real repo.
- Any request to scaffold a new SaaS monorepo, greenfield or otherwise.
- Literal requests to "scaffold the saas template" or "use my saas starter".

## 1. Locate the template

The template lives inside the installed plugin, at:

```
${CLAUDE_PLUGIN_ROOT}/templates/saas-monorepo/
```

`CLAUDE_PLUGIN_ROOT` is an environment variable that resolves to this
plugin's installation root at runtime. Plugins are cached after install
(`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`), so always
resolve the template path through this variable — never hardcode a path
relative to the current project, and never assume the plugin source repo is
checked out anywhere the target project can see.

## 2. Read SCAFFOLD.md first — it is the source of truth

Before copying anything, read:

```
${CLAUDE_PLUGIN_ROOT}/templates/saas-monorepo/SCAFFOLD.md
```

This skill is a pointer to that document, not a replacement for it.
`SCAFFOLD.md` owns the authoritative placeholder table, the exact shadcn/ui
init flags per app, the component add list, the token-wiring step, the
verification commands, and the surface-trimming rules. Follow it exactly as
written. If anything below appears to conflict with a newer `SCAFFOLD.md`,
`SCAFFOLD.md` wins — this skill may be stale relative to it.

## 3. Copy the template into the target project

```bash
cp -R "${CLAUDE_PLUGIN_ROOT}/templates/saas-monorepo/" path/to/new-product/
cd path/to/new-product/
```

## 4. Substitute placeholders

Five placeholders appear across the template's root files and `packages/`:
`{{PRODUCT_NAME}}`, `{{PRODUCT_SLUG}}`, `{{PRODUCT_DESCRIPTION}}`,
`{{PRIMARY_LOCALE}}`, `{{CONTACT_EMAIL}}`. Get their values from the PRD (or
ask the user if any are missing — do not invent a slug or contact email).

Find every file containing a placeholder, then replace in place:

```bash
grep -rl '{{PRODUCT_NAME}}\|{{PRODUCT_SLUG}}\|{{PRODUCT_DESCRIPTION}}\|{{PRIMARY_LOCALE}}\|{{CONTACT_EMAIL}}' . \
  --exclude-dir=node_modules \
  | xargs sed -i \
      -e 's/{{PRODUCT_NAME}}/<value>/g' \
      -e 's/{{PRODUCT_SLUG}}/<value>/g' \
      -e 's/{{PRODUCT_DESCRIPTION}}/<value>/g' \
      -e 's/{{PRIMARY_LOCALE}}/<value>/g' \
      -e 's/{{CONTACT_EMAIL}}/<value>/g'
```

(On macOS/BSD sed, `-i` needs a trailing `''` argument — `SCAFFOLD.md` §3.2
has both forms. Detect the platform rather than guessing.)

Then verify nothing was missed before moving on:

```bash
grep -rn '{{' . --exclude-dir=node_modules --exclude-dir=.git
```

Any remaining match is a bug — resolve it before running `pnpm install`.

## 5. Deterministic post-copy sequence

Run these in order, exactly as `SCAFFOLD.md` specifies:

1. `pnpm install` — resolves the workspace graph and generates a fresh
   `pnpm-lock.yaml` for this product.
2. Per production surface (`apps/landing`, `apps/pwa`,
   `apps/mission-control`), run `pnpm dlx shadcn@latest init` with the exact
   flags in `SCAFFOLD.md` §3.4 (`-t next`/`-t vite`, `-b base`,
   `--css-variables`, `--cwd <app dir>` — no `--filter`), pointed at that
   app's own global stylesheet. Record the `style` the CLI actually writes
   to each app's `components.json` per §3.4; don't assume it in advance.
3. Wire `packages/ui` tokens into each app's global stylesheet as the first
   `@import` line, per `SCAFFOLD.md` §3.6 — do this before adding
   components, so generated components pick up shared tokens from the start.
4. Run the fixed component add list from `SCAFFOLD.md` §3.5
   (`button card dialog form input label select table tabs toast badge
   dropdown-menu sheet skeleton sonner`) once per app that was just
   initialized.
5. Apply the PRD's design tokens (colors, radius, typography scale, etc.)
   into the `packages/ui/src/tokens.css` token file — this is the single
   place product-specific design tokens live. Do not duplicate tokens into
   individual app CSS files; every app imports from here.

## 6. Verify before reporting done

```bash
pnpm turbo run lint typecheck build
```

This must exit 0. If the PRD also specifies test coverage expectations,
follow with `pnpm turbo run test`. Do not report the scaffold as complete
until this passes — fix failures in the copied product repo, not by
skipping the check.

## 7. Surface trimming

Default is keep all three apps (`landing`, `pwa`, `mission-control`). Only
delete a surface — e.g. `apps/mission-control` — if the PRD's locked
distribution set explicitly excludes it. Follow `SCAFFOLD.md` §5 for the
trimming rules: dropping an app is a directory delete plus removing any
cross-app references and CI matrix entries; `packages/schemas`,
`packages/ui`, and `packages/config` are never trimmed. Re-run step 6's
verification after any trim.

## Non-negotiables

- The UI stack is **Tailwind v4 + shadcn/ui** on every production surface,
  full stop. Never substitute another CSS framework or component library,
  and never hand-roll design-system primitives that shadcn/ui already
  provides — that defeats the reason this template exists.
- Never skip `SCAFFOLD.md` and improvise the monorepo structure from
  training-data memory of pnpm/Turborepo conventions. This template's
  structure, file locations, and command sequence are deliberately fixed so
  every scaffolded product looks the same.
- Never vendor `node_modules/`, a `pnpm-lock.yaml`, or pre-generated shadcn
  component output back into the template — those stay product-specific,
  per `SCAFFOLD.md` §6.
