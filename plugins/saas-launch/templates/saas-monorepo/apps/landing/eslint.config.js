import { FlatCompat } from "@eslint/eslintrc";
import base from "@{{PRODUCT_SLUG}}/config/eslint";

// next/core-web-vitals ships as an eslintrc-style config; FlatCompat bridges
// it into the flat config format the rest of the monorepo uses.
const compat = new FlatCompat({ baseDirectory: import.meta.dirname });

export default [
  ...base,
  ...compat.extends("next/core-web-vitals"),
  // next/core-web-vitals is bridged in via FlatCompat, which doesn't forward
  // parserOptions.project/type info to typed rules — so the shared base's
  // typed @typescript-eslint/consistent-type-imports rule crashes ESLint
  // fatally on every file in this app without it. Disable it here.
  { rules: { "@typescript-eslint/consistent-type-imports": "off" } },
  {
    // next-env.d.ts is Next.js-managed boilerplate ("this file is regenerated
    // by `next dev` / `next build`. Do not edit it by hand") that always uses
    // triple-slash references — that's how Next wires up its own and
    // typed-routes' ambient types. Only next build can change this file.
    files: ["next-env.d.ts"],
    rules: { "@typescript-eslint/triple-slash-reference": "off" },
  },
];
