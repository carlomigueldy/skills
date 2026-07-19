# Service worker notes

There is no hand-written `sw.ts` in this directory on purpose.
`vite-plugin-pwa` is configured in `../../vite.config.ts` with
`strategies: "generateSW"`, which means Workbox generates the entire
service worker (precache manifest + the `runtimeCaching` rules declared
there) at build time. The output lands in `dist/sw.js` — never edit
generated output, edit the `VitePWA({...})` config in `vite.config.ts`
instead.

## What's already wired

- **App-shell precaching** — every built asset is precached; `navigateFallback: "/index.html"`
  makes deep links work offline once the shell has been cached once.
- **`NetworkFirst` for Supabase** — requests to `/rest/v1/*` and `/auth/v1/*`
  try the network first (5s timeout) and fall back to the last cached
  response, so read screens still render something offline.
- **Writes are not cached by the service worker.** Offline *writes* go
  through `../lib/offline/queue.ts` instead (an explicit IndexedDB queue,
  flushed on reconnect) — a service worker cache is the wrong tool for
  mutations that need to preserve ordering and get a real round trip to
  Supabase once back online.

## When you'd switch to `injectManifest`

Reach for the `injectManifest` strategy (a hand-written `src/sw/service-worker.ts`
that `vite-plugin-pwa` injects the precache manifest into) only if you need
service-worker logic `generateSW`'s config can't express, e.g.:

- **Background Sync API** integration (auto-retrying the offline write
  queue from the service worker itself, even if the tab is closed).
- Web Push notification handling.
- Custom cache invalidation logic beyond Workbox's built-in strategies.

If/when that happens: add `src/sw/service-worker.ts`, change
`strategies: "injectManifest"` + `srcDir: "src/sw"` + `filename: "service-worker.ts"`
in the `VitePWA({...})` options, and call `precacheAndRoute(self.__WB_MANIFEST)`
at the top of the new file. Until then, keep using `generateSW` — it's less
code to maintain and covers everything this app currently needs.
