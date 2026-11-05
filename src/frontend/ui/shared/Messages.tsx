"use client";

import { useEffect } from "react";

const NOTICE_MS = 5000;

export function Messages({
  error,
  notice = "",
  onClose,
}: {
  error: string;
  notice?: string;
  onClose: () => void;
}) {
  useEffect(() => {
    if (!notice) return;
    const timer = setTimeout(onClose, NOTICE_MS);
    return () => clearTimeout(timer);
  }, [notice, onClose]);

  if (!error && !notice) return null;

  return (
    <p
      className={error ? "toast error" : "toast notice"}
      role={error ? "alert" : "status"}
    >
      <span>{error || notice}</span>
      <button type="button" aria-label="Close message" onClick={onClose}>
        <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
          <path
            stroke="currentColor"
            strokeWidth="2"
            d="M1 1l10 10M11 1L1 11"
          />
        </svg>
      </button>
    </p>
  );
}
