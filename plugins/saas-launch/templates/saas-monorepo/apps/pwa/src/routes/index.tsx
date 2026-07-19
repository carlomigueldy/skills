import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

export const Route = createFileRoute("/")({
  component: HomePage,
});

function HomePage() {
  const { t } = useTranslation();

  return (
    <main className="mx-auto flex min-h-dvh max-w-lg flex-col justify-center gap-4 p-6">
      <h1 className="text-2xl font-semibold">{t("common.appName")}</h1>
      <p className="text-muted-foreground">{t("common.loading")}</p>
      {/* TODO(scaffold): replace with the real dashboard, sourced from
          @{{PRODUCT_SLUG}}/schemas types and an offline-aware TanStack Query hook. */}
    </main>
  );
}
