import { createRootRoute, Outlet } from "@tanstack/react-router";

import { OfflineIndicator } from "../components/OfflineIndicator";

export const Route = createRootRoute({
  component: RootComponent,
});

function RootComponent() {
  return (
    <>
      <Outlet />
      <OfflineIndicator />
    </>
  );
}
