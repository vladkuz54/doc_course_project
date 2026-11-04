"use client";

import { useRef, type ChangeEvent } from "react";
import { formatDate } from "./fleet";

export function toIsoDate(text: string) {
  const match = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(text);
  if (!match) return "";
  const [, day, month, year] = match;
  const date = new Date(Date.UTC(Number(year), Number(month) - 1, Number(day)));
  const iso = `${year}-${month}-${day}`;
  return date.toISOString().slice(0, 10) === iso ? iso : "";
}

function withSlashes(text: string) {
  const digits = text.replace(/\D/g, "").slice(0, 8);
  return [digits.slice(0, 2), digits.slice(2, 4), digits.slice(4)]
    .filter(Boolean)
    .join("/");
}

export function DateField({
  name,
  required,
  defaultValue,
}: {
  name: string;
  required?: boolean;
  defaultValue?: string;
}) {
  const text = useRef<HTMLInputElement>(null);
  const picker = useRef<HTMLInputElement>(null);

  const typed = (event: ChangeEvent<HTMLInputElement>) => {
    const input = event.target;
    if (input.selectionStart === input.value.length) {
      input.value = withSlashes(input.value);
    }
    input.setCustomValidity(
      input.value && !toIsoDate(input.value)
        ? "Enter a real date as dd/mm/yyyy"
        : "",
    );
  };

  const picked = (event: ChangeEvent<HTMLInputElement>) => {
    if (!text.current) return;
    text.current.value = formatDate(event.target.value);
    text.current.setCustomValidity("");
  };

  const openPicker = () => {
    if (!text.current || !picker.current) return;
    picker.current.value = toIsoDate(text.current.value);
    picker.current.showPicker();
  };

  return (
    <span className="date-field">
      <input
        ref={text}
        name={name}
        placeholder="dd/mm/yyyy"
        inputMode="numeric"
        autoComplete="off"
        required={required}
        defaultValue={defaultValue && formatDate(defaultValue)}
        onChange={typed}
      />
      <input
        ref={picker}
        type="date"
        className="date-picker"
        tabIndex={-1}
        aria-hidden="true"
        onChange={picked}
      />
      <button
        type="button"
        className="date-button"
        aria-label="Choose a date"
        onClick={openPicker}
      >
        <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
          <path
            fill="currentColor"
            d="M4 0h2v2h4V0h2v2h3v14H1V2h3V0zM3 6v8h10V6H3z"
          />
        </svg>
      </button>
    </span>
  );
}
