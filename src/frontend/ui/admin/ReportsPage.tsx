"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiDownload, apiGet } from "../api";
import { DateField, nowForField, toIsoDate } from "../shared/DateField";
import { formatDate, type Vehicle } from "../shared/fleet";
import { Messages } from "../shared/Messages";
import { useData } from "../shared/useData";

type ReportRow = Record<string, string | number | null>;

type Report = {
  title: string;
  period_from: string;
  period_to: string;
  rows: ReportRow[];
};

const REPORT_KINDS = {
  utilization: "Завантаженість автомобілів",
  maintenance: "Витрати на утримання автопарку",
  usage: "Аналітика використання транспорту за період",
};

const loadVehicles = () => apiGet<Vehicle[]>("/vehicles/");

// Same labels as the PDF and Excel exports (backend bll/exports.py)
const COLUMN_LABELS: Record<string, string> = {
  vehicle: "Транспорт",
  completed_routes: "Завершені маршрути",
  total_distance: "Загальна відстань, км",
  hours_on_route: "Годин у рейсі",
  utilization_percent: "Завантаженість, %",
  repair_cost: "Вартість обслуговування",
  insurance_cost: "Вартість страхування",
  total_cost: "Загальна вартість",
  liters: "Літри",
  fuel_cost: "Вартість пального",
  liters_per_100km: "Літрів на 100 км",
};

function columnLabel(key: string) {
  return COLUMN_LABELS[key] ?? key;
}

function reportPath(form: FormData, format?: string) {
  const query = new URLSearchParams({
    period_from: toIsoDate(String(form.get("period_from"))),
    period_to: toIsoDate(String(form.get("period_to"))),
  });
  const vehicleId = String(form.get("vehicle_id"));
  if (vehicleId) query.set("vehicle_id", vehicleId);
  if (format) query.set("format", format);
  return `/reports/${form.get("kind")}?${query}`;
}

function exportName(form: FormData, extension: string) {
  const from = toIsoDate(String(form.get("period_from")));
  const to = toIsoDate(String(form.get("period_to")));
  return `${form.get("kind")}-${from}-${to}.${extension}`;
}

export function ReportsPage() {
  const {
    data: vehicles,
    error,
    pending,
    run,
    clearMessages,
  } = useData(loadVehicles);
  const [report, setReport] = useState<Report | null>(null);
  const today = nowForField().slice(0, 10);

  const form = useRef<HTMLFormElement>(null);
  const latest = useRef(0);

  const show = useCallback(() => {
    if (!form.current?.checkValidity()) return;
    const request = ++latest.current;
    const path = reportPath(new FormData(form.current));
    run(() =>
      apiGet<Report>(path).then((loaded) => {
        if (request === latest.current) setReport(loaded);
      }),
    ).then((shown) => {
      if (!shown && request === latest.current) setReport(null);
    });
  }, [run]);

  useEffect(() => {
    show();
  }, [show]);

  const download = (format: "pdf" | "xlsx") => {
    if (!form.current?.reportValidity()) return;
    const fields = new FormData(form.current);
    run(() =>
      apiDownload(reportPath(fields, format), exportName(fields, format)),
    );
  };

  const cell = (key: string, value: ReportRow[string]) => {
    if (value === null) return "—";
    if (key !== "vehicle_id") return value;
    return vehicles?.find((vehicle) => vehicle.id === value)?.make ?? value;
  };

  const columns = report?.rows.length ? Object.keys(report.rows[0]) : [];

  return (
    <>
      <h1>Звіти</h1>
      <Messages error={error} onClose={clearMessages} />
      <form
        ref={form}
        className="panel"
        onChange={show}
        onSubmit={(event) => {
          event.preventDefault();
          show();
        }}
      >
        <label className="span-2">
          Звіт
          <select name="kind">
            {Object.entries(REPORT_KINDS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          З
          <DateField
            name="period_from"
            defaultValue={`${today.slice(0, 4)}-01-01`}
            required
          />
        </label>
        <label>
          По
          <DateField name="period_to" defaultValue={today} required />
        </label>
        <label>
          Транспорт (необов’язково)
          <select name="vehicle_id">
            <option value="">Увесь транспорт</option>
            {vehicles?.map((vehicle) => (
              <option key={vehicle.id} value={vehicle.id}>
                {vehicle.make}
              </option>
            ))}
          </select>
        </label>
        <div className="form-actions">
          <button
            type="button"
            className="secondary"
            disabled={pending}
            onClick={() => download("pdf")}
          >
            Експорт у PDF
          </button>
          <button
            type="button"
            className="secondary"
            disabled={pending}
            onClick={() => download("xlsx")}
          >
            Експорт в Excel
          </button>
        </div>
      </form>

      {report && (
        <section className="table-box">
          <h2>{report.title}</h2>
          <p className="muted report-period">
            з {formatDate(report.period_from)} по {formatDate(report.period_to)}
          </p>
          {report.rows.length === 0 && (
            <p className="muted">За цей період даних немає.</p>
          )}
          {report.rows.length > 0 && (
            <table>
              <thead>
                <tr>
                  {columns.map((column) => (
                    <th key={column}>{columnLabel(column)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {report.rows.map((row, index) => (
                  <tr key={index}>
                    {columns.map((column) => (
                      <td key={column}>{cell(column, row[column])}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}
    </>
  );
}
