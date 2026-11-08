"use client";

import type { NavigationMenu } from "../products";
import { MenuLinks, type MenuLink } from "../shared/MenuLinks";
import {
  NotificationsPopover,
  type Notification,
  type RelatedEntity,
} from "../shared/NotificationsPopover";

const LINKS: MenuLink[] = [
  { page: "routes", label: "Маршрути" },
  { page: "requests", label: "Запити" },
  { page: "profile", label: "Профіль" },
];

const OPEN_PAGES: Record<RelatedEntity, string | null> = {
  drivers: "profile",
  driver_requests: "requests",
  routes: "routes",
  vehicles: null,
};

function openPage(notification: Notification) {
  return OPEN_PAGES[notification.related_entity];
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
