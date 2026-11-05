"use client";

import type { Workspace } from "../products";
import { useHash } from "../shared/useHash";
import { ADMIN_LINKS } from "./AdminMenu";
import { DriversPage } from "./DriversPage";
import { RequestsPage } from "./RequestsPage";

export class AdminWorkspace implements Workspace {
  render() {
    return <AdminScreens />;
  }
}

function AdminScreens() {
  const hash = useHash();
  if (hash === "requests") return <RequestsPage />;

  const screen =
    ADMIN_LINKS.find((link) => link.page === hash) ?? ADMIN_LINKS[0];

  if (screen.page === "drivers") return <DriversPage />;

  return <h1>{screen.label}</h1>;
}
