import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard")({
  component: DashboardRoute,
});

// Placeholder metrics — wire up to a Supabase view/RPC that aggregates
// tenant + subscription + payment state once the schema lands.
const METRIC_PLACEHOLDERS = [
  { label: "Active tenants", value: "—" },
  { label: "MRR", value: "—" },
  { label: "Pending manual payments", value: "—" },
  { label: "Suspended tenants", value: "—" },
] as const;

function DashboardRoute() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      {/* TODO(scaffold): replace with @{{PRODUCT_SLUG}}/ui's Card component. */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {METRIC_PLACEHOLDERS.map((metric) => (
          <div
            key={metric.label}
            className="rounded-lg border border-border p-4"
          >
            <p className="text-sm text-muted-foreground">{metric.label}</p>
            <p className="mt-2 text-2xl font-semibold">{metric.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
