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
  utilization: "Vehicle utilization",
  maintenance: "Maintenance cost",
  usage: "Usage analytics",
};

const loadVehicles = () => apiGet<Vehicle[]>("/vehicles/");

function columnLabel(key: string) {
  if (key === "vehicle_id") return "Vehicle";
  const label = key.replaceAll("_", " ");
  return label[0].toUpperCase() + label.slice(1);
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
      <h1>Reports</h1>
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
        <label>
          Report
          <select name="kind">
            {Object.entries(REPORT_KINDS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          From
          <DateField
            name="period_from"
            defaultValue={`${today.slice(0, 4)}-01-01`}
            required
          />
        </label>
        <label>
          To
          <DateField name="period_to" defaultValue={today} required />
        </label>
        <label>
          Vehicle (optional)
          <select name="vehicle_id">
            <option value="">All vehicles</option>
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
            Export PDF
          </button>
          <button
            type="button"
            className="secondary"
            disabled={pending}
            onClick={() => download("xlsx")}
          >
            Export Excel
          </button>
        </div>
      </form>

      {report && (
        <section className="table-box">
          <h2>{report.title}</h2>
          <p className="muted report-period">
            {formatDate(report.period_from)} to {formatDate(report.period_to)}
          </p>
          {report.rows.length === 0 && (
            <p className="muted">No data for this period.</p>
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
