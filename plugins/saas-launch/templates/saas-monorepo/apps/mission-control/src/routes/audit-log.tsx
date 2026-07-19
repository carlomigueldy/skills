import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/audit-log")({
  component: AuditLogRoute,
});

function AuditLogRoute() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">Audit log</h1>
      <p className="text-sm text-muted-foreground">
        Append-only record of admin actions (payment verify/approve/reject,
        tenant lifecycle changes, subscription edits). TODO: load rows from
        Supabase (audit_log table) via @tanstack/react-query, newest first,
        with actor + target + diff columns.
      </p>
      {/* TODO(scaffold): replace with @{{PRODUCT_SLUG}}/ui's Table component. */}
      <div className="rounded-lg border border-border">
        <div className="grid grid-cols-[auto_1fr_1fr_1fr] gap-4 border-b border-border p-4 text-sm font-medium text-muted-foreground">
          <span>Time</span>
          <span>Actor</span>
          <span>Action</span>
          <span>Target</span>
        </div>
        <div className="p-4 text-sm text-muted-foreground">
          No audit events loaded yet — connect src/lib/supabase.ts.
        </div>
      </div>
    </div>
  );
}
