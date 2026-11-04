"use client";

import { useHash } from "./useHash";

export type MenuLink = { page: string; label: string };

export function MenuLinks({ links }: { links: MenuLink[] }) {
  const hash = useHash();
  const current = links.some((link) => link.page === hash)
    ? hash
    : links[0].page;

  return (
    <nav aria-label="Main" className="menu">
      {links.map((link) => (
        <a
          key={link.page}
          href={`#${link.page}`}
          aria-current={link.page === current ? "page" : undefined}
        >
          {link.label}
        </a>
      ))}
    </nav>
  );
}
