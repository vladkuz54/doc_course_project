"use client";

import type { NavigationMenu } from "../products";
import { MenuLinks, type MenuLink } from "../shared/MenuLinks";
import {
  NotificationsPopover,
  type RelatedEntity,
} from "../shared/NotificationsPopover";

const LINKS: MenuLink[] = [
  { page: "routes", label: "Маршрути" },
  { page: "profile", label: "Профіль" },
];

const OPEN_PAGES: Record<RelatedEntity, string | null> = {
  drivers: "profile",
  driver_requests: "profile",
  routes: "routes",
  vehicles: null,
};

function openPage(entity: RelatedEntity) {
  return OPEN_PAGES[entity];
}

export class DriverMenu implements NavigationMenu {
  render() {
    return (
      <>
        <MenuLinks links={LINKS} />
        <NotificationsPopover openPage={openPage} />
      </>
    );
  }
}
