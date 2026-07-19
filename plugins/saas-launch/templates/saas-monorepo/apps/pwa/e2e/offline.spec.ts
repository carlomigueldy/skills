import { expect, test } from "@playwright/test";

test.describe("offline-first behaviour", () => {
  test("shows the offline indicator when the network drops, hides it once restored", async ({
    page,
    context,
  }) => {
    await page.goto("/");
    await expect(page.getByRole("status")).toHaveCount(0);

    // Playwright's context.setOffline emulates a real network drop, which
    // makes the browser fire genuine 'offline'/'online' events and flips
    // navigator.onLine — the same signals src/lib/offline/queue.ts and
    // src/components/OfflineIndicator.tsx listen for in production.
    await context.setOffline(true);
    await expect(page.getByRole("status")).toBeVisible();
    await expect(page.getByText(/offline/i)).toBeVisible();

    await context.setOffline(false);
    await expect(page.getByRole("status")).toHaveCount(0);
  });

  test.skip("queues a mutation made while offline and syncs it once back online", async () => {
    // TODO(scaffold): wire once a real write flow exists (e.g. submitting a
    // manual-payment receipt from src/routes/subscription/payment-status.tsx
    // through src/lib/offline/queue.ts). Then:
    //   1. context.setOffline(true)
    //   2. submit the form; assert the pending-sync indicator appears and
    //      the mutation lands in IndexedDB (queue.pendingCount() === 1)
    //   3. context.setOffline(false); assert the queue flushes to 0 and the
    //      submitted row is visible again once refetched from Supabase.
  });
});
