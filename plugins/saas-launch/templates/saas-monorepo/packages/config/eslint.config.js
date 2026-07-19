// Shared ESLint flat config for the {{PRODUCT_NAME}} monorepo.
// Consuming apps/packages import this and spread it into their own eslint.config.js,
// then append framework-specific rules (e.g. next/core-web-vitals) on top.
//
// Example (apps/pwa/eslint.config.js):
//   import base from "@{{PRODUCT_SLUG}}/config/eslint";
//   export default [...base, { rules: { /* app overrides */ } }];

import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import prettier from "eslint-config-prettier";

/** @type {import("eslint").Linter.Config[]} */
export default [
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true }
      ],
      "@typescript-eslint/no-unused-vars": [
        "warn",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }
      ],
      "@typescript-eslint/consistent-type-imports": "warn"
    }
  },
  {
    ignores: [
      "**/dist/**",
      "**/build/**",
      "**/.next/**",
      "**/.turbo/**",
      "**/coverage/**",
      "**/node_modules/**"
    ]
  },
  // Keep last: disables stylistic rules that conflict with Prettier formatting.
  prettier
];
