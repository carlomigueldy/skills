---
name: saas-scaffold
description: >-
  Use when starting the Phase 4 build of a SaaS Launch Blueprint PRD, when
  scaffolding a new SaaS monorepo, or when the user asks to "scaffold the saas
  template" / "use my saas starter". Instantiates the pnpm + Turborepo SaaS
  monorepo template (Tailwind v4 + shadcn/ui, Next.js landing, Vite PWA, Vite
  mission-control, Supabase backend) from the shared templates repo into a
  target project directory instead of scaffolding a monorepo from scratch.
  Also instantiates the PRD's chosen agent-harness tier from the same repo's
  `agent-harness` overlays (AGENTS.md rulebook, init.sh, and the
  tier-appropriate hooks/agents/workflows) on top of the monorepo. Applies
  only when the PRD's Tech section records `Stack source: template`; fails
  fast on `Stack source: custom`.
---

# saas-scaffold

Scaffold a new SaaS product monorepo from the shared `saas-launch` templates
repo — never hand-build a monorepo structure, package.json graph, or UI
stack from memory when this skill applies. The template is maintained once,
in that repo, so every product scaffolded from it gets the same commands,
the same structure, and the same token file locations.

## When this applies

- Phase 4 ("build") of a SaaS Launch Blueprint PRD, immediately after the PRD
  and prototype phases are done and it's time to produce a real repo.
- Any request to scaffold a new SaaS monorepo, greenfield or otherwise.
- Literal requests to "scaffold the saas template" or "use my saas starter".

## 0. Precondition — template-path stacks only

Before touching the filesystem, read the PRD's Tech section. Its first line
is the `Stack source: template | custom` marker — check it before doing
anything else in this skill.

- **`custom`** — STOP. Do not copy the template, do not run any step below.
  This skill only instantiates the templates repo's `saas-monorepo`
  template; a custom stack has no template for it to scaffold. Report this
  to the founder and point them at the PRD's CUSTOM STACK SPEC (the Tech
  section's scaffold-sufficient stack description) and countdown's
  custom-path build branch, which builds from that spec directly instead of
  invoking this skill.
- **`template`** — proceed to §1.
- **Marker absent** — do not assume; confirm the stack source with the
  founder before proceeding.

## 1. Locate the template — resolve `TEMPLATE_ROOT`

The templates no longer ship inside the plugin — they live in a standalone
public repo, https://github.com/carlomigueldy/templates. Because resolution
is plain git plus the filesystem, it works identically whether this skill is
running under Claude Code, Codex CLI, or OpenCode. Resolve `TEMPLATE_ROOT`
once, then take every template path below relative to it:

```bash
if [ -n "${SAAS_LAUNCH_TEMPLATES_DIR:-}" ]; then
  TEMPLATE_ROOT="$SAAS_LAUNCH_TEMPLATES_DIR"
elif [ -d "$HOME/.cache/saas-launch/templates/.git" ]; then
  TEMPLATE_ROOT="$HOME/.cache/saas-launch/templates"
  git -C "$TEMPLATE_ROOT" pull --ff-only || true
else
  git clone --depth 1 https://github.com/carlomigueldy/templates \
    "$HOME/.cache/saas-launch/templates"
  TEMPLATE_ROOT="$HOME/.cache/saas-launch/templates"
fi
```

In order:

1. **`$SAAS_LAUNCH_TEMPLATES_DIR`** — if set, use it as-is. This is the
   override for a local checkout of the templates repo (development, or
   fully offline work).
2. **Cached clone** — if `~/.cache/saas-launch/templates` exists, use it,
   refreshing with a fast-forward pull first. The `|| true` is deliberate:
   a failed pull (offline, flaky network) is tolerated and the stale cache
   is acceptable — do not treat it as an error.
3. **Fresh clone** — otherwise, shallow-clone the repo into the cache
   location and use that.

The template then lives at `${TEMPLATE_ROOT}/saas-monorepo/` and the
harness overlays at `${TEMPLATE_ROOT}/agent-harness/`. Always resolve
template paths through `TEMPLATE_ROOT` — never hardcode a path relative to
the current project, and never assume the templates repo is checked out
anywhere the target project can see.

## 2. Read SCAFFOLD.md first — it is the source of truth

Before copying anything, read:

```
${TEMPLATE_ROOT}/saas-monorepo/SCAFFOLD.md
```

This skill is a pointer to that document, not a replacement for it.
`SCAFFOLD.md` owns the authoritative placeholder table, the vendored
shadcn/ui component list and how to verify it, the optional
add-more-components step, the token-wiring step, the verification
commands, and the surface-trimming rules. Follow it exactly as written. If
anything below appears to conflict with a newer `SCAFFOLD.md`,
`SCAFFOLD.md` wins — this skill may be stale relative to it.

Note also: the copied template includes a bundled `shadcn` agent skill at
`.claude/skills/shadcn/`, vendored verbatim from upstream shadcn/ui. It
travels with every scaffolded product and is available in that product's
own Claude Code sessions for adding, searching, fixing, or styling
components beyond the 14 already vendored — see §5 step 4.

## 3. Copy the template + harness overlays

```bash
mkdir -p path/to/new-product && cp -R "${TEMPLATE_ROOT}/saas-monorepo/." path/to/new-product/
cd path/to/new-product/
```

Then layer the PRD's chosen agent-harness tier on top, in order, from
`${TEMPLATE_ROOT}/agent-harness/` — tiers `1..N` are cumulative overlays,
so the loop must run every tier from 1 up to the chosen tier, not just
tier N alone:

```bash
for t in $(seq 1 "$TIER"); do
  cp -R "${TEMPLATE_ROOT}/agent-harness/tier-$t/." "path/to/new-product/"
done
chmod +x path/to/new-product/init.sh
```

`TIER` comes from the PRD's "Agent harness" section — **ask the founder if
it's absent, never guess it**. The overlays are cumulative and ordered on
purpose: a higher tier's `AGENTS.md` and `.claude/settings.json` are
authored as complete superset files and are meant to overwrite the
same-path file a lower tier just copied — that is not data loss, it's the
harness's designed replace-never-merge mechanic. Read
`${TEMPLATE_ROOT}/agent-harness/HARNESS.md` first; it is the
harness's source of truth the same way `SCAFFOLD.md` is the monorepo's —
if anything here conflicts with a newer `HARNESS.md`, `HARNESS.md` wins.

This deterministic overlay copy is template-path-only — it is what §0
gates on `Stack source: template`. A custom-stack PRD never reaches this
step; countdown's custom branch instantiates the same harness tier by
adaptation instead.

## 4. Substitute placeholders

Five placeholders appear across the template's root files and `packages/`:
`{{PRODUCT_NAME}}`, `{{PRODUCT_SLUG}}`, `{{PRODUCT_DESCRIPTION}}`,
`{{PRIMARY_LOCALE}}`, `{{CONTACT_EMAIL}}`. Get their values from the PRD (or
ask the user if any are missing — do not invent a slug or contact email).
Because the harness copy in §3 ran before this pass, the same five tokens
also resolve inside harness files (`AGENTS.md`, `claude-progress.md`,
`session-handoff.md`, `autonomous-loop.md`, etc.) — no separate
substitution step is needed for them.

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
2. Verify the vendored shadcn/ui setup rather than initializing it — per
   `SCAFFOLD.md` §3.4, `packages/ui/src/components/ui/` already ships the
   14 baseline components (`badge card button dialog dropdown-menu form
   input label select sheet skeleton sonner table tabs`) pre-generated at
   style `new-york-v4`, plus `packages/ui/src/lib/utils.ts` and
   `packages/ui/src/index.ts` re-exporting everything. There is no `shadcn
   init` or `shadcn add` step at scaffold time — confirm the files are
   present (`ls packages/ui/src/components/ui/`) and move on. If anything's
   missing, that's a bug in the template itself, not something to route
   around by running the CLI inside the product repo.
3. Confirm `packages/ui` tokens are wired into each app's global stylesheet
   as the first `@import` after `"tailwindcss"` — per `SCAFFOLD.md` §3.6,
   this should already be present in every app's scaffold-generated
   stylesheet; only re-wire by hand if a stylesheet was regenerated from
   scratch after copying the template.
4. **Optional**: if the PRD needs a component beyond the 14 vendored ones,
   add it with the bundled `shadcn` agent skill (vendored into every
   scaffolded project at `.claude/skills/shadcn/`) rather than improvising
   the CLI invocation from memory — see `SCAFFOLD.md` §3.5 for the exact
   steps, including converting the CLI's `@/...` imports to this package's
   relative-import convention before committing.
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

Also verify the harness layer copied in §3, tier ≥2 only for the first two
checks:

```bash
jq empty path/to/new-product/.claude/settings.json
jq empty path/to/new-product/feature_list.json
bash -n path/to/new-product/init.sh
```

Then confirm the harness's `.claude/` additions (`settings.json`,
`agents/`, at tier ≥3) sit **beside** the vendored `.claude/skills/shadcn/`
from the monorepo template without clobbering it — `ls
path/to/new-product/.claude/skills/shadcn/` should still show the vendored
skill untouched.

## 7. Surface trimming

Default is keep all three apps (`landing`, `pwa`, `mission-control`). Only
delete a surface — e.g. `apps/mission-control` — if the PRD's locked
distribution set explicitly excludes it. Follow `SCAFFOLD.md` §5 for the
trimming rules: dropping an app is a directory delete plus removing any
cross-app references and CI matrix entries; `packages/schemas`,
`packages/ui`, and `packages/config` are never trimmed. Re-run step 6's
verification after any trim.

## Non-negotiables

- On the `Stack source: template` path this skill scaffolds, the UI stack
  is **Tailwind v4 + shadcn/ui** on every production surface, full stop.
  Never substitute another CSS framework or component library, and never
  hand-roll design-system primitives that shadcn/ui already provides —
  that defeats the reason this template exists. Custom-stack PRDs are out
  of this skill's scope entirely — §0 stops them before this rule ever
  applies.
- Never skip `SCAFFOLD.md` and improvise the monorepo structure from
  training-data memory of pnpm/Turborepo conventions. This template's
  structure, file locations, and command sequence are deliberately fixed so
  every scaffolded product looks the same.
- Never vendor `node_modules/` or a `pnpm-lock.yaml` back into the
  template — those stay product-specific, per `SCAFFOLD.md` §6. (shadcn/ui
  component output is the one exception: it *is* vendored in the template,
  deliberately — see `SCAFFOLD.md` §3.4 and §6.)
