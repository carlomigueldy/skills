import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/payments")({
  component: PaymentsRoute,
});

function PaymentsRoute() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">Payments</h1>
      <p className="text-sm text-muted-foreground">
        Pending manual-payment review queue. TODO: load rows from Supabase
        (manual_payments table, status = &quot;pending&quot;) via
        @tanstack/react-query, then wire the verify / approve / reject
        actions to an RPC that updates payment + subscription state
        together.
      </p>
      {/* TODO(scaffold): replace with @{{PRODUCT_SLUG}}/ui's Table component and a
          Dialog for the verify/approve/reject action. Plain markup for now
          so this renders without shadcn imports. */}
      <div className="rounded-lg border border-border">
        <div className="grid grid-cols-[1fr_1fr_auto_auto] gap-4 border-b border-border p-4 text-sm font-medium text-muted-foreground">
          <span>Tenant</span>
          <span>Amount</span>
          <span>Submitted</span>
          <span>Review</span>
        </div>
        <div className="p-4 text-sm text-muted-foreground">
          No pending manual payments loaded yet — connect
          src/lib/supabase.ts.
        </div>
      </div>
      <div className="flex gap-2 text-sm">
        <button
          type="button"
          disabled
          className="rounded-md border border-border px-3 py-1.5 disabled:opacity-50"
        >
          Approve
        </button>
        <button
          type="button"
          disabled
          className="rounded-md border border-border px-3 py-1.5 disabled:opacity-50"
        >
          Reject
        </button>
      </div>
    </div>
  );
}
