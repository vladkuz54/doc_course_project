"use client";

import { useEffect } from "react";

const NOTICE_MS = 5000;

export function Messages({
  error,
  notice = "",
  warning = "",
  onClose,
}: {
  error: string;
  notice?: string;
  warning?: string;
  onClose: () => void;
}) {
  useEffect(() => {
    if (!notice || warning) return;
    const timer = setTimeout(onClose, NOTICE_MS);
    return () => clearTimeout(timer);
  }, [notice, warning, onClose]);

  if (!error && !notice && !warning) return null;

  return (
    <p
      className={`toast ${error ? "error" : warning ? "warning" : "notice"}`}
      role={error || warning ? "alert" : "status"}
    >
      <span>{error || warning || notice}</span>
      <button type="button" aria-label="Закрити повідомлення" onClick={onClose}>
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
