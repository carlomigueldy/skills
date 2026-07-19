/**
 * @{{PRODUCT_SLUG}}/locales
 *
 * Shared message catalogs. next-intl (apps/landing) and react-i18next
 * (apps/pwa, apps/mission-control) both read from here — never duplicate
 * or hand-roll translation strings locally in an app.
 */
import en from "./en.json";
import tl from "./tl.json";
import taglish from "./taglish.json";

export const locales = { en, tl, taglish } as const;

export type LocaleCode = keyof typeof locales;

export const localeCodes = Object.keys(locales) as LocaleCode[];

/** Locale the product ships with by default; override per-user/tenant at runtime. */
export const defaultLocale: LocaleCode = "{{PRIMARY_LOCALE}}" as LocaleCode;

export type Messages = (typeof locales)[LocaleCode];

export { en, tl, taglish };
