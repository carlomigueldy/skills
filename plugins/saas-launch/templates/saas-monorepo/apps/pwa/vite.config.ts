import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import { tanstackRouter } from "@tanstack/router-plugin/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  resolve: {
    // Matches the "@/*" path in tsconfig.json — required for local
    // components.json-driven `shadcn add` runs targeting this app directly
    // (baseline components live in @{{PRODUCT_SLUG}}/ui; see SCAFFOLD.md §3.5).
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  plugins: [
    // Must come before react() — generates src/routeTree.gen.ts from the
    // file-based routes in src/routes on every dev/build run. Same setup as
    // apps/mission-control's vite.config.ts; keep both in sync.
    tanstackRouter({
      target: "react",
      autoCodeSplitting: true,
    }),
    react(),
    tailwindcss(),
    VitePWA({
      registerType: "autoUpdate",
      // generateSW: workbox builds the service worker for us from the rules
      // below. See src/sw/README.md before switching to injectManifest.
      strategies: "generateSW",
      includeAssets: ["icon.svg", "robots.txt"],
      manifest: {
        name: "{{PRODUCT_NAME}}",
        short_name: "{{PRODUCT_NAME}}",
        description: "{{PRODUCT_DESCRIPTION}}",
        start_url: "/",
        scope: "/",
        display: "standalone",
        orientation: "portrait",
        background_color: "#ffffff", // manifest requires a literal; keep in sync with @{{PRODUCT_SLUG}}/ui tokens.css --background
        theme_color: "#09090b", // TODO: sync with @{{PRODUCT_SLUG}}/ui tokens.css --primary once the PRD palette lands
        icons: [
          { src: "/icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any" },
          // TODO(scaffold): generate real raster icons (e.g. via `pnpm dlx pwa-asset-generator`)
          // before shipping — iOS/Android install prompts need PNGs, an SVG-only
          // manifest is not enough for every platform.
          { src: "/pwa-192x192.png", sizes: "192x192", type: "image/png" },
          { src: "/pwa-512x512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
        ],
      },
      workbox: {
        navigateFallback: "/index.html",
        // Never let the app shell go stale silently, but keep API reads
        // available offline from the last successful response.
        runtimeCaching: [
          {
            urlPattern: ({ url }) =>
              url.pathname.startsWith("/rest/v1") || url.pathname.startsWith("/auth/v1"),
            handler: "NetworkFirst",
            options: {
              cacheName: "supabase-api-cache",
              networkTimeoutSeconds: 5,
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],
      },
      devOptions: {
        // Keep the SW disabled in `vite dev` — enable per-session via the
        // VITE_PWA_DEV_SW env var when you need to debug offline behaviour
        // against the dev server instead of a production build.
        enabled: false,
      },
    }),
  ],
  server: {
    port: 5173,
  },
});
