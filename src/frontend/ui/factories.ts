"use client";

import { AdminMenu } from "./admin/AdminMenu";
import { AdminProfilePage } from "./admin/AdminProfilePage";
import { AdminWorkspace } from "./admin/AdminWorkspace";
import { DriverMenu } from "./driver/DriverMenu";
import { DriverProfilePage } from "./driver/DriverProfilePage";
import { DriverWorkspace } from "./driver/DriverWorkspace";
import type { NavigationMenu, ProfilePage, Role, Workspace } from "./products";

export abstract class RoleUIFactory {
  static forRole(role: Role): RoleUIFactory {
    switch (role) {
      case "DRIVER":
        return new DriverUIFactory();
      case "ADMIN":
        return new AdminUIFactory();
      default:
        throw new Error(`Unknown role: ${role}`);
    }
  }

  abstract createProfilePage(): ProfilePage;
  abstract createMenu(): NavigationMenu;
  abstract createWorkspace(): Workspace;
}

export class DriverUIFactory extends RoleUIFactory {
  createProfilePage(): ProfilePage {
    return new DriverProfilePage();
  }

  createMenu(): NavigationMenu {
    return new DriverMenu();
  }

  createWorkspace(): Workspace {
    return new DriverWorkspace();
  }
}

export class AdminUIFactory extends RoleUIFactory {
  createProfilePage(): ProfilePage {
    return new AdminProfilePage();
  }

  createMenu(): NavigationMenu {
    return new AdminMenu();
  }

  createWorkspace(): Workspace {
    return new AdminWorkspace();
  }
}
