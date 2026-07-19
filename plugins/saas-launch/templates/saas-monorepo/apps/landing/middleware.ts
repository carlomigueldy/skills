import createMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

export default createMiddleware(routing);

export const config = {
  // Skip API routes, Next.js internals, and files with an extension
  // (favicon.ico, site.webmanifest, etc).
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
