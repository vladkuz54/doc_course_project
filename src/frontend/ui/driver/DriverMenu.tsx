"use client";

import type { NavigationMenu } from "../products";
import { MenuLinks, type MenuLink } from "../shared/MenuLinks";

const LINKS: MenuLink[] = [
  { page: "routes", label: "Routes" },
  { page: "profile", label: "Profile" },
];

export class DriverMenu implements NavigationMenu {
  render() {
    return <MenuLinks links={LINKS} />;
  }
}
