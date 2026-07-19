# Release — {{PRODUCT_NAME}}

Task id prefix: `release-`. Covers taking a finished build to production: private repo + CI, Vercel deploy with the URL attached, Lighthouse ≥90 mobile, converting OWNER-TASKS.md into GitHub issues, and assembling the Launch Dossier's inputs.

## Precondition

The Build constraint's MUST-SHIP scope is met — customer-app core workflow + offline/sync, manual payment gating, Mission Control core. Check `feature_list.json`: every MUST-SHIP-tagged entry is `passing` with evidence before starting the steps below that assume a working product. Anything the cut order deferred (landing page, full E2E suite, promo/pitch videos, Launch Dossier) is handled in steps 9–10, not silently dropped.

## Steps

1. **Create a private GitHub repo** per the PRD's Repo & deployment section. Push the current state. Wire CI per the DEFAULT stack's CI/CD line: GitHub Actions running lint, typecheck, Vitest, Playwright.
2. **Link Vercel** to the repo per the DEFAULT stack's Hosting line — configure each surface (landing, PWA, Mission Control) per Vercel/Turborepo conventions. Wire env vars (Supabase, Sentry, analytics, LLM provider keys). A missing key is an owner-ledger item — flag it, don't silently stub the integration.
3. **Deploy to production.** Confirm the live URL loads for every surface in the locked distribution set.
4. **Attach the production URL** to the repo — the GitHub "About" field AND the README.
5. **Run Lighthouse (mobile) against production** for landing + PWA. Target ≥90. A score below 90 is a Definition of Done failure for the affected surface — fix it before marking the corresponding `release-` entry `passing`; don't ship a known regression because it's release day. (Per-feature Lighthouse checks already happened in `surface-build.md` step 10 for the landing page — this is the production confirmation, not the first check.)
6. **Confirm Sentry + analytics are live in production**, not just local dev — trigger a test event on the deployed app and confirm it lands in the dashboard.
7. **Convert OWNER-TASKS.md into GitHub issues** in the new repo — one issue per ledger item accumulated since Phase 1 (locale review, provider/account setup, domain purchase, prospect pitching, launch content, etc.), labeled by category.
8. **File an issue for anything the Build constraint deferred** and that isn't done yet (landing page, full E2E suite, promo/pitch videos, Launch Dossier itself) — deferred items convert to issues, they never silently vanish.
9. **Assemble Launch Dossier inputs**: pitch line, production URL, repo link, locked stack + distribution set, gate history, analytics links, open owner issues (from steps 7–8), promo video if rendered, the CTA CONTACT BLOCK. This playbook's job is to make sure every input exists and is correct — authoring the Dossier's HTML itself is a separate step per the PRD's Launch Dossier section.
10. **Verify**: production URL returns 200 for every surface, CI is green on the release commit, Lighthouse scores are recorded, GitHub issue count matches ledger item count.
11. **Definition of Done** (AGENTS.md) + `feature_list.json` update — `release-NN` entries split at a sensible granularity (e.g. `release-01` repo+CI, `release-02` Vercel deploy, `release-03` Lighthouse, `release-04` issue conversion, `release-05` Dossier inputs), each `passing` only with evidence attached (URLs, Lighthouse scores, issue links, CI run links).
