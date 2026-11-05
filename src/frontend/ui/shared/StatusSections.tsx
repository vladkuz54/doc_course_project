"use client";

import type { ReactNode } from "react";

export function StatusSections<T, S extends string>({
  items,
  statusOf,
  sections,
  children,
}: {
  items: T[] | null | undefined;
  statusOf: (item: T) => S;
  sections: { status: S; label: string }[];
  children: (rows: T[]) => ReactNode;
}) {
  return sections.map(({ status, label }) => {
    const rows = items?.filter((item) => statusOf(item) === status) ?? [];
    if (rows.length === 0) return null;
    return (
      <section key={status} className="status-section">
        <h2>
          {label} <span className="muted">({rows.length})</span>
        </h2>
        {children(rows)}
      </section>
    );
  });
}
