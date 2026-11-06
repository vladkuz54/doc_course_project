"use client";

import type { NavigationMenu } from "../products";
import { MenuLinks, type MenuLink } from "../shared/MenuLinks";
import {
  NotificationsPopover,
  type RelatedEntity,
} from "../shared/NotificationsPopover";

export const ADMIN_LINKS: MenuLink[] = [
  { page: "drivers", label: "Водії" },
  { page: "requests", label: "Запити" },
  { page: "routes", label: "Маршрути" },
  { page: "vehicles", label: "Транспорт" },
  { page: "accounting", label: "Облік" },
  { page: "reports", label: "Звіти" },
  { page: "profile", label: "Профіль" },
];

const OPEN_PAGES: Record<RelatedEntity, string> = {
  drivers: "drivers",
  driver_requests: "requests",
  routes: "routes",
  vehicles: "vehicles",
};

function openPage(entity: RelatedEntity) {
  return OPEN_PAGES[entity];
}

export class AdminMenu implements NavigationMenu {
  render() {
    return (
      <>
        <MenuLinks links={ADMIN_LINKS} />
        <NotificationsPopover openPage={openPage} canCheckDeadlines />
      </>
    );
  }
}
