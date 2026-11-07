"use client";

import { useSyncExternalStore } from "react";

function subscribe(onChange: () => void) {
  window.addEventListener("hashchange", onChange);
  return () => window.removeEventListener("hashchange", onChange);
}

// The hash is "screen" or "screen/tab", such as #accounting/insurance
const part = (index: number) => () =>
  window.location.hash.slice(1).split("/")[index] ?? "";

const readScreen = part(0);
const readTab = part(1);

export function useHash() {
  return useSyncExternalStore(subscribe, readScreen, () => "");
}

export function useHashTab() {
  return useSyncExternalStore(subscribe, readTab, () => "");
}
