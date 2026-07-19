import { getRequestConfig } from "next-intl/server";
import { routing } from "./routing";

// Assumes @{{PRODUCT_SLUG}}/locales exposes one JSON message file per locale via its
// package exports map (e.g. `@{{PRODUCT_SLUG}}/locales/en.json`, `@{{PRODUCT_SLUG}}/locales/tl.json`,
// `@{{PRODUCT_SLUG}}/locales/taglish.json`) — the shared single source of truth also
// consumed by apps/mission-control's react-i18next setup.
//
// Per-locale loader map (not a dynamic template-literal import): webpack must
// be able to statically analyze each import specifier, and @{{PRODUCT_SLUG}}/locales'
// package.json `exports` field only declares these three literal subpaths
// (no wildcard), so `import(`.../${locale}.json`)` fails to resolve at build time.
// Not explicitly typed: each locale's JSON module import carries its own
// literal structural type, which next-intl's `messages` field (typed as
// AbstractIntlMessages) accepts directly.
const messageLoaders = {
  en: () => import("@{{PRODUCT_SLUG}}/locales/en.json"),
  tl: () => import("@{{PRODUCT_SLUG}}/locales/tl.json"),
  taglish: () => import("@{{PRODUCT_SLUG}}/locales/taglish.json"),
} satisfies Record<(typeof routing.locales)[number], () => Promise<unknown>>;

export default getRequestConfig(async ({ requestLocale }) => {
  const requested = await requestLocale;
  const locale = (routing.locales as readonly string[]).includes(
    requested as string,
  )
    ? (requested as (typeof routing.locales)[number])
    : routing.defaultLocale;

  return {
    locale,
    messages: (await messageLoaders[locale]()).default,
  };
});
