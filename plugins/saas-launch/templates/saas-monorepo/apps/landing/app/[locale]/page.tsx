import { setRequestLocale } from "next-intl/server";
import { Hero } from "./hero";

// Placeholders are kept as plain string literals (never spliced directly
// into JSX children) — "{{TOKEN}}" inside `{ }` would parse as an object
// literal, not text, and fail typecheck.
const CONTACT_EMAIL = "{{CONTACT_EMAIL}}";

export default async function LandingPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <main className="mx-auto flex min-h-dvh max-w-5xl flex-col items-center justify-center gap-6 px-6 py-24 text-center">
      <Hero />
      <footer className="mt-16 text-sm text-muted-foreground">
        <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>
      </footer>
    </main>
  );
}
