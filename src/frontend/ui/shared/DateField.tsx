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

export function toIsoDateTime(text: string) {
  const match = /^(.{10}) ([01]\d|2[0-3]):([0-5]\d)$/.exec(text);
  const date = match && toIsoDate(match[1]);
  return date ? `${date}T${match[2]}:${match[3]}` : "";
}

export function nowForField() {
  const now = new Date();
  const pad = (value: number) => String(value).padStart(2, "0");
  const date = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
  return `${date}T${pad(now.getHours())}:${pad(now.getMinutes())}`;
}

function formatForField(iso: string, withTime: boolean) {
  const date = formatDate(iso.slice(0, 10));
  return withTime ? `${date} ${iso.slice(11, 16)}` : date;
}

function withSeparators(text: string, withTime: boolean) {
  const digits = text.replace(/\D/g, "").slice(0, withTime ? 12 : 8);
  const date = [digits.slice(0, 2), digits.slice(2, 4), digits.slice(4, 8)]
    .filter(Boolean)
    .join("/");
  if (digits.length <= 8) return date;
  const time = [digits.slice(8, 10), digits.slice(10)].filter(Boolean).join(":");
  return `${date} ${time}`;
}

export function DateField({
  name,
  required,
  defaultValue,
  withTime = false,
}: {
  name: string;
  required?: boolean;
  defaultValue?: string;
  withTime?: boolean;
}) {
  const text = useRef<HTMLInputElement>(null);
  const picker = useRef<HTMLInputElement>(null);
  const toIso = withTime ? toIsoDateTime : toIsoDate;
  const format = withTime ? "дд/мм/рррр гг:хх" : "дд/мм/рррр";

  const typed = (event: ChangeEvent<HTMLInputElement>) => {
    const input = event.target;
    if (input.selectionStart === input.value.length) {
      input.value = withSeparators(input.value, withTime);
    }
    input.setCustomValidity(
      input.value && !toIso(input.value) ? `Введіть справжню дату у форматі ${format}` : "",
    );
  };

  const picked = (event: ChangeEvent<HTMLInputElement>) => {
    if (!text.current) return;
    text.current.value = formatForField(event.target.value, withTime);
    text.current.setCustomValidity("");
  };

  const openPicker = () => {
    if (!text.current || !picker.current) return;
    picker.current.value = toIso(text.current.value);
    picker.current.showPicker();
  };

  return (
    <span className="date-field">
      <input
        ref={text}
        name={name}
        placeholder={format}
        inputMode="numeric"
        autoComplete="off"
        required={required}
        defaultValue={defaultValue && formatForField(defaultValue, withTime)}
        onChange={typed}
      />
      <input
        ref={picker}
        type={withTime ? "datetime-local" : "date"}
        className="date-picker"
        tabIndex={-1}
        aria-hidden="true"
        onChange={picked}
      />
      <button
        type="button"
        className="date-button"
        aria-label="Обрати дату"
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
