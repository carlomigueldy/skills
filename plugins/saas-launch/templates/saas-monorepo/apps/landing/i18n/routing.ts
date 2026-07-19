import { defineRouting } from "next-intl/routing";

// Locale set matches packages/locales (packages/locales/{en,tl,taglish}.json)
// — the single source of truth for translated strings shared across
// apps/landing and apps/mission-control.
export const routing = defineRouting({
  locales: ["en", "tl", "taglish"],
  defaultLocale: "{{PRIMARY_LOCALE}}",
});

export type AppLocale = (typeof routing.locales)[number];
