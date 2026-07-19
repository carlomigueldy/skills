import { FlatCompat } from "@eslint/eslintrc";
import base from "@{{PRODUCT_SLUG}}/config/eslint";

// next/core-web-vitals ships as an eslintrc-style config; FlatCompat bridges
// it into the flat config format the rest of the monorepo uses.
const compat = new FlatCompat({ baseDirectory: import.meta.dirname });

export default [...base, ...compat.extends("next/core-web-vitals")];
