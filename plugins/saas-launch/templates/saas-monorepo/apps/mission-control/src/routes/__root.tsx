import { createRootRoute, Link, Outlet } from "@tanstack/react-router";

// TODO: @{{PRODUCT_SLUG}}/ui ships the shadcn/ui primitives (Button, Sheet,
// DropdownMenu, ...) but no composite AppShell/Sidebar — that's a
// product-specific composition, not a baseline component. Build it out of
// the vendored Sheet + DropdownMenu once this app needs a collapsible or
// mobile nav; plain markup is intentional here until then.
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
