import type { ReactNode } from "react";

export type Role = "DRIVER" | "ADMIN";

export interface ProfilePage {
  render(): ReactNode;
}

export interface NavigationMenu {
  render(): ReactNode;
}

export interface Workspace {
  render(): ReactNode;
}
