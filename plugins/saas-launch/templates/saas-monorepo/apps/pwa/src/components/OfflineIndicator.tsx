import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { offlineQueue } from "../lib/offline/queue";

/**
 * Fixed bottom banner reflecting connectivity + write-queue state. Renders
 * nothing when online with an empty queue, so it never occupies layout
 * space in the common case.
 *
 * Actual flushing is owned by src/lib/offline/queue.ts (it attaches its own
 * 'online' / visibilitychange listeners on module load) — this component
 * only observes pending count via queue.subscribe(), it never calls
 * queue.flush() itself, to avoid two independent flush loops racing.
 */
export function OfflineIndicator() {
  const { t } = useTranslation();
  const [isOnline, setIsOnline] = useState<boolean>(() =>
    typeof navigator === "undefined" ? true : navigator.onLine,
  );
  const [pending, setPending] = useState(0);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    const unsubscribe = offlineQueue.subscribe(setPending);
    void offlineQueue.pendingCount().then(setPending);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
      unsubscribe();
    };
  }, []);

  if (isOnline && pending === 0) return null;

  const isSyncing = isOnline && pending > 0;

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed inset-x-0 bottom-0 z-50 flex items-center justify-center gap-2 border-t border-border bg-background/95 px-4 py-2 text-sm text-foreground shadow-[0_-1px_8px_rgba(0,0,0,0.06)] backdrop-blur"
    >
      <span
        aria-hidden="true"
        className={`h-2 w-2 shrink-0 rounded-full ${isOnline ? "bg-amber-500" : "bg-red-500"}`}
      />
      {!isOnline && <span>{t("offline.youAreOffline")}</span>}
      {isSyncing && <span>{t("offline.pendingSync", { count: pending })}</span>}
    </div>
  );
}
