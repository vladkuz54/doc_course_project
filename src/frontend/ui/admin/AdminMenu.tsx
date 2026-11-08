"use client";

import type { NavigationMenu } from "../products";
import { MenuLinks } from "../shared/MenuLinks";
import {
  NotificationsPopover,
  type Notification,
  type RelatedEntity,
} from "../shared/NotificationsPopover";
import { ADMIN_LINKS } from "./adminLinks";

const OPEN_PAGES: Record<RelatedEntity, string> = {
  drivers: "drivers",
  driver_requests: "requests",
  routes: "routes",
  vehicles: "vehicles",
};

const OPEN_BY_TYPE: Record<string, string> = {
  INSURANCE_EXPIRING: "accounting/insurance",
  MAINTENANCE_SCHEDULED: "accounting/repairs",
  MAINTENANCE_DUE: "accounting/repairs",
  REPAIR_COST_MISSING: "accounting/repairs",
};

function openPage(notification: Notification) {
  return (
    OPEN_BY_TYPE[notification.type] ?? OPEN_PAGES[notification.related_entity]
  );
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
