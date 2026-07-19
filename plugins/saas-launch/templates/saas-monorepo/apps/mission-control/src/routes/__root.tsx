import { createRootRoute, Link, Outlet } from "@tanstack/react-router";

// TODO(scaffold): swap this nav shell for @{{PRODUCT_SLUG}}/ui's shadcn/ui-derived
// AppShell / Sidebar components once `pnpm dlx shadcn@latest add ...` has
// run against @{{PRODUCT_SLUG}}/ui. Kept as plain markup so the skeleton renders and
// typechecks with zero shadcn imports.
export const Route = createRootRoute({
  component: RootLayout,
});

function RootLayout() {
  return (
    <div className="flex min-h-dvh">
      <nav className="w-56 shrink-0 border-r border-border p-4">
        <p className="mb-6 text-sm font-semibold">{"{{PRODUCT_NAME}}"}</p>
        <ul className="flex flex-col gap-2 text-sm">
          <li>
            <Link to="/dashboard" className="[&.active]:font-semibold">
              Dashboard
            </Link>
          </li>
          <li>
            <Link to="/tenants" className="[&.active]:font-semibold">
              Tenants
            </Link>
          </li>
          <li>
            <Link to="/payments" className="[&.active]:font-semibold">
              Payments
            </Link>
          </li>
          <li>
            <Link to="/audit-log" className="[&.active]:font-semibold">
              Audit log
            </Link>
          </li>
        </ul>
      </nav>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
}
