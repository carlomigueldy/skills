/**
 * react-i18next setup for the PWA. Message catalogs are never hand-rolled
 * here — they come from @{{PRODUCT_SLUG}}/locales, the single source of
 * truth shared with apps/mission-control (react-i18next) and apps/landing
 * (next-intl).
 */
import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

import { defaultLocale, locales } from "@{{PRODUCT_SLUG}}/locales";

const resources = Object.fromEntries(
  Object.entries(locales).map(([code, messages]) => [code, { translation: messages }]),
);

void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: defaultLocale,
    lng: defaultLocale,
    interpolation: {
      escapeValue: false, // React already escapes output
    },
    detection: {
      order: ["localStorage", "navigator"],
      caches: ["localStorage"],
    },
  });

export default i18n;
