import { defineConfig, mergeConfig } from "vitest/config";
import viteConfig from "./vite.config";

// Reuses vite.config.ts (aliases, plugins) and layers Vitest-only settings
// on top, so tests run against the same module resolution as `vite dev`.
export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: "jsdom",
      globals: true,
      // fake-indexeddb/auto polyfills window.indexedDB so idb-keyval (used by
      // src/lib/offline/queue.ts and the TanStack Query IDB persister) works
      // under jsdom without a real browser.
      setupFiles: ["./src/test/setup.ts"],
      include: ["src/**/*.test.{ts,tsx}"],
      css: false,
    },
  }),
);
