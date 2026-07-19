import { hasLocale } from "next-intl";
import { getRequestConfig } from "next-intl/server";
import { routing } from "./routing";

// Assumes @{{PRODUCT_SLUG}}/locales exposes one JSON message file per locale via its
// package exports map (e.g. `@{{PRODUCT_SLUG}}/locales/en.json`, `@{{PRODUCT_SLUG}}/locales/tl.json`,
// `@{{PRODUCT_SLUG}}/locales/taglish.json`) — the shared single source of truth also
// consumed by apps/mission-control's react-i18next setup.
export default getRequestConfig(async ({ requestLocale }) => {
  const requested = await requestLocale;
  const locale = hasLocale(routing.locales, requested)
    ? requested
    : routing.defaultLocale;

  return {
    locale,
    messages: (await import(`@{{PRODUCT_SLUG}}/locales/${locale}.json`)).default,
  };
});
