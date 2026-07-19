import i18n from "i18next";
import { initReactI18next } from "react-i18next";

// Assumes @{{PRODUCT_SLUG}}/locales exposes one JSON message file per locale via its
// package exports map (e.g. `@{{PRODUCT_SLUG}}/locales/en.json`) — the shared single
// source of truth also consumed by apps/landing's next-intl setup. Static
// (not dynamic) imports keep this module free of top-level await, which
// depends on a tsconfig target this app doesn't own.
import en from "@{{PRODUCT_SLUG}}/locales/en.json";
import tl from "@{{PRODUCT_SLUG}}/locales/tl.json";
import taglish from "@{{PRODUCT_SLUG}}/locales/taglish.json";

const resources = {
  en: { translation: en },
  tl: { translation: tl },
  taglish: { translation: taglish },
};

void i18n.use(initReactI18next).init({
  resources,
  lng: "{{PRIMARY_LOCALE}}",
  fallbackLng: "en",
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
