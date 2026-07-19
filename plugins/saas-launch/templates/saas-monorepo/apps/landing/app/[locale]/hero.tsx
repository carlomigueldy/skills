"use client";

import { motion } from "motion/react";
import { useTranslations } from "next-intl";

// Placeholders live in string literals so JSX-child interpolation never
// mis-parses "{{TOKEN}}" as an object literal expression.
const PRODUCT_NAME = "{{PRODUCT_NAME}}";
const PRODUCT_DESCRIPTION = "{{PRODUCT_DESCRIPTION}}";

export function Hero() {
  // Falls back to the placeholder copy above until packages/locales ships
  // a `hero` namespace with `title` / `description` / `cta` keys.
  const t = useTranslations("hero");

  const title = t.has("title") ? t("title") : PRODUCT_NAME;
  const description = t.has("description")
    ? t("description")
    : PRODUCT_DESCRIPTION;
  const cta = t.has("cta") ? t("cta") : "Get started";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="flex flex-col items-center gap-6"
    >
      <h1 className="text-4xl font-semibold tracking-tight sm:text-6xl">
        {title}
      </h1>
      <p className="max-w-2xl text-balance text-lg text-muted-foreground">
        {description}
      </p>
      {/* TODO(scaffold): swap for the shadcn/ui Button once
          `pnpm dlx shadcn@latest add button` has run against @{{PRODUCT_SLUG}}/ui. */}
      <button
        type="button"
        className="rounded-md bg-foreground px-6 py-3 text-sm font-medium text-background transition-opacity hover:opacity-90"
      >
        {cta}
      </button>
    </motion.div>
  );
}
