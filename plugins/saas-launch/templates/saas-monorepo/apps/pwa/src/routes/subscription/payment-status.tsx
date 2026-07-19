import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

import { manualPaymentStatusEnum, type ManualPaymentStatus } from "@{{PRODUCT_SLUG}}/schemas";

export const Route = createFileRoute("/subscription/payment-status")({
  component: PaymentStatusPage,
});

const TONE_CLASS: Record<ManualPaymentStatus, string> = {
  pending: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
  approved: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  rejected: "bg-red-500/10 text-red-600 dark:text-red-400",
};

// TODO(scaffold): once the data layer lands, replace this static list with
// a single offline-aware TanStack Query read of the tenant's actual
// manual_payments row (see ../../lib/offline/queue.ts for the write side of
// that flow) and drop the "all three states" demo rendering below.
function PaymentStatusPage() {
  const { t } = useTranslation();
  const statuses = manualPaymentStatusEnum.options;

  return (
    <main className="mx-auto flex min-h-dvh max-w-sm flex-col justify-center gap-4 p-6">
      <h1 className="text-xl font-semibold">{t("payments.title")}</h1>
      <ul className="flex flex-col gap-2">
        {statuses.map((status) => (
          <li key={status} className={`rounded-md px-4 py-3 text-sm font-medium ${TONE_CLASS[status]}`}>
            {t(`payments.status.${status}`)}
          </li>
        ))}
      </ul>
    </main>
  );
}
