# Surface Build — {{PRODUCT_NAME}}

Generic playbook for building or extending ANY UI surface — landing page (`landing-`), PWA customer app (`pwa-`), Mission Control (`mission-control-`), or any additional surface the PRD's distribution interview locked in (its own PRD-assigned prefix). `payment-lifecycle.md` and `tenant-lifecycle.md` cover their domains' UI too — use those instead when the feature is specifically a payment or tenant-status flow; use this playbook for everything else, and for the shared shell (nav, layout, error boundaries) either domain-specific playbook builds on top of.

Precondition: design direction settled from the PRD's Design system spec + Design Bar interview, and the frontend-design skill loaded — a HARD REQUIREMENT, no frontend task starts without it (Claude crew mapping: `surface-builder`).

## Steps

1. **Read the PRD section for this surface + feature** — the relevant Product/user-story bullet, the Design system spec (tokens, type scale, color story, motion language), and the Production quality bar checklist. Don't start building from memory of an earlier feature's spec.
2. **Confirm design tokens are wired** before writing surface-specific code — `tokens.css` / Tailwind v4 `@theme` values match the PRD's locked direction. If this is the first feature touching a fresh surface, this is where the PRD's DETERMINISTIC SCAFFOLD (shadcn init + component-add list) gets exercised — don't hand-roll what shadcn already ships.
3. **Build FROM shadcn/ui components** — never hand-rolled UI, never a from-scratch component library. Customize only through shadcn's intended layers: CSS variables/tokens, Tailwind v4 `@theme`, component variants.
4. **Implement all required states** for anything that loads data or can fail:
   - `loading`, `error`, `empty` — every surface, no exceptions.
   - `offline` / `pending-sync` — PWA specifically, per the offline-first requirement (cached shell, queued writes, clear indicator). Landing and Mission Control don't need offline handling but still need the first three.
5. **Wire every form** through react-hook-form + zod, using the shared schema package — no ad hoc form state, no unvalidated inputs.
6. **Responsive check** — mobile, tablet, desktop breakpoints per the Production quality bar.
7. **Accessibility basics** — labels, focus order, visible focus state, contrast, keyboard navigation.
8. **i18n** — strings routed through the locale files (react-i18next / next-i18next), never hardcoded, even if the Tagalog/Taglish copy is a placeholder pending the owner-ledger review.
9. **Verify via Playwright** — the MCP tool if the agent has one, otherwise the project's own Playwright test run — exercising the actual user-visible flow across the states built in step 4. Capture the run output/screenshot as evidence.
10. **Landing page specifically**: run Lighthouse mobile now, not deferred to `release.md` — catch a regression per-feature instead of discovering it at release time. Target ≥90; below that is a Definition of Done failure for this feature.
11. **Definition of Done** (AGENTS.md — the last, flagged-most-important section) — every item satisfied, not partially, before marking `passing`. At tier-3+, only `qa-verifier` makes the final `passing` call; hand off with evidence attached and let it confirm.
12. **Update `feature_list.json`** for the surface-prefixed entry: `verification` names what proved it (e.g. "Playwright: full submit→loading→success walkthrough, offline queue drains on reconnect"), `evidence` is the actual run output/artifact reference, `notes` carries anything the reviewer needs.
