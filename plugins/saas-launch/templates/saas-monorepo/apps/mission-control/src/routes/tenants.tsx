import { createFileRoute } from "@tanstack/react-router";
import type { TenantStatus } from "@{{PRODUCT_SLUG}}/schemas";

export const Route = createFileRoute("/tenants")({
  component: TenantsRoute,
});

const LIFECYCLE_ACTIONS: { label: string; targetStatus: TenantStatus }[] = [
  { label: "Activate", targetStatus: "active" },
  { label: "Suspend", targetStatus: "suspended" },
  { label: "Soft ban", targetStatus: "soft_banned" },
  { label: "Ban", targetStatus: "banned" },
  { label: "Cancel", targetStatus: "cancelled" },
];

function TenantsRoute() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">Tenants</h1>
      <p className="text-sm text-muted-foreground">
        Tenant directory + lifecycle actions. TODO: load rows from Supabase
        (tenants table) via @tanstack/react-query and enforce lifecycle
        transitions through an RPC that also updates RLS-visible status
        flags.
      </p>
      {/* TODO(scaffold): replace with @{{PRODUCT_SLUG}}/ui's Table + DropdownMenu
          components. Kept as a plain div grid so this renders without any
          shadcn imports. */}
      <div className="rounded-lg border border-border">
        <div className="grid grid-cols-[1fr_auto_auto] gap-4 border-b border-border p-4 text-sm font-medium text-muted-foreground">
          <span>Tenant</span>
          <span>Status</span>
          <span>Actions</span>
        </div>
        <div className="p-4 text-sm text-muted-foreground">
          No tenants loaded yet — connect src/lib/supabase.ts.
        </div>
      </div>
      <div className="flex gap-2 text-sm">
        {LIFECYCLE_ACTIONS.map((action) => (
          <button
            key={action.targetStatus}
            type="button"
            disabled
            className="rounded-md border border-border px-3 py-1.5 disabled:opacity-50"
          >
            {action.label}
          </button>
        ))}
      </div>
    </div>
  );
}
