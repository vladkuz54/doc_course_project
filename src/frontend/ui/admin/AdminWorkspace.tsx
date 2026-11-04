"use client";

import type { Workspace } from "../products";
import { useHash } from "../shared/useHash";
import { ADMIN_LINKS } from "./AdminMenu";

export class AdminWorkspace implements Workspace {
  render() {
    return <AdminScreens />;
  }
}

function AdminScreens() {
  const hash = useHash();
  const screen =
    ADMIN_LINKS.find((link) => link.page === hash) ?? ADMIN_LINKS[0];

  return <h1>{screen.label}</h1>;
}
