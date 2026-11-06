"use client";

import { useEffect, useRef, type ReactNode } from "react";

export function FormRow({
  colSpan,
  children,
}: {
  colSpan: number;
  children: ReactNode;
}) {
  const row = useRef<HTMLTableRowElement>(null);

  useEffect(() => {
    row.current?.scrollIntoView({ block: "nearest" });
  }, []);

  return (
    <tr ref={row} className="form-row">
      <td colSpan={colSpan}>{children}</td>
    </tr>
  );
}
