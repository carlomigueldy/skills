import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import { tanstackRouter } from "@tanstack/router-plugin/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

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
    // file-based routes in src/routes on every dev/build run.
    tanstackRouter({
      target: "react",
      autoCodeSplitting: true,
    }),
    react(),
    tailwindcss(),
  ],
  server: {
    port: 5174,
  },
});
