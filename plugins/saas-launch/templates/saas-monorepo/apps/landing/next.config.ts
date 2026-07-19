import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";
import { withSentryConfig } from "@sentry/nextjs";

// Points at the request-config module that resolves the active locale
// and loads its messages from @{{PRODUCT_SLUG}}/locales. See i18n/request.ts.
const withNextIntl = createNextIntlPlugin("./i18n/request.ts");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Workspace packages are consumed as TypeScript source, not pre-built —
  // Next.js needs to transpile them itself.
  transpilePackages: ["@{{PRODUCT_SLUG}}/ui", "@{{PRODUCT_SLUG}}/schemas", "@{{PRODUCT_SLUG}}/locales"],
};

export default withSentryConfig(withNextIntl(nextConfig), {
  silent: true,
  // Leave org/project unset here — filled in from CI/hosting env vars
  // (SENTRY_ORG, SENTRY_PROJECT) so the template stays product-agnostic.
});
