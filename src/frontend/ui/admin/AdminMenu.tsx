"use client";

import type { NavigationMenu } from "../products";
import { MenuLinks, type MenuLink } from "../shared/MenuLinks";

export const ADMIN_LINKS: MenuLink[] = [
  { page: "drivers", label: "Drivers" },
  { page: "requests", label: "Requests" },
  { page: "routes", label: "Routes" },
  { page: "stops", label: "Stops" },
  { page: "vehicles", label: "Vehicles" },
  { page: "accounting", label: "Accounting" },
  { page: "reports", label: "Reports" },
  { page: "profile", label: "Profile" },
];

export class AdminMenu implements NavigationMenu {
  render() {
    return <MenuLinks links={ADMIN_LINKS} />;
  }
}
