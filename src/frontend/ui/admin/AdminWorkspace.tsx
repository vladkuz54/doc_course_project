"use client";

import type { Workspace } from "../products";
import { useHash } from "../shared/useHash";
import { AccountingPage } from "./AccountingPage";
import { ADMIN_LINKS } from "./AdminMenu";
import { DriversPage } from "./DriversPage";
import { ReportsPage } from "./ReportsPage";
import { RequestsPage } from "./RequestsPage";
import { RoutesPage } from "./RoutesPage";
import { StopsPage } from "./StopsPage";
import { VehiclesPage } from "./VehiclesPage";

export class AdminWorkspace implements Workspace {
  render() {
    return <AdminScreens />;
  }
}

function AdminScreens() {
  const hash = useHash();
  if (hash === "requests") return <RequestsPage />;
  if (hash === "routes") return <RoutesPage />;
  if (hash === "stops") return <StopsPage />;
  if (hash === "accounting") return <AccountingPage />;
  if (hash === "reports") return <ReportsPage />;

  const screen =
    ADMIN_LINKS.find((link) => link.page === hash) ?? ADMIN_LINKS[0];

  if (screen.page === "drivers") return <DriversPage />;
  if (screen.page === "vehicles") return <VehiclesPage />;

  return <h1>{screen.label}</h1>;
}
