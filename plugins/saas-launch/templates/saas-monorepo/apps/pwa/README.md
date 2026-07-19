# pwa

{{PRODUCT_NAME}} mobile-first, offline-first customer PWA. Vite + React +
TypeScript, Tailwind v4 + shadcn/ui, TanStack Router (file-based routes,
`src/routeTree.gen.ts` is generated — don't hand-edit it) + TanStack Query
(persisted to IndexedDB), Zustand, react-hook-form + zod, react-i18next.

See `../../SCAFFOLD.md` at the repo root for the full instantiation flow
(placeholder substitution, verifying the vendored shadcn/ui setup). The
baseline shadcn/ui components ship pre-generated in `packages/ui` — see
`../../packages/ui/README.md` — so there's no per-app `shadcn init` here;
`src/index.css` already imports the shared tokens from
`@{{PRODUCT_SLUG}}/ui/tokens.css` per SCAFFOLD.md §3.6.

## Commands

```bash
pnpm --filter pwa dev          # http://localhost:5173
pnpm --filter pwa build
pnpm --filter pwa test         # Vitest — includes src/lib/offline/queue.test.ts
pnpm --filter pwa test:e2e     # Playwright — needs `pnpm dev` reachable + `supabase start`
```

## Offline-first write path

`src/lib/offline/queue.ts` is the single place mutations go through when a
write might happen offline: `enqueue()` appends to an IndexedDB-backed FIFO
queue, and the module auto-flushes to Supabase on the `online` event and on
tab-visibility change (`flush()` is also safe to call manually, e.g. from a
"sync now" affordance). `src/components/OfflineIndicator.tsx` renders the
current connectivity + pending-count state; it observes the queue via
`queue.subscribe()` but never calls `flush()` itself, so there's exactly one
flush loop. See `src/sw/README.md` for how this relates to (and is
deliberately separate from) the generated service worker.
