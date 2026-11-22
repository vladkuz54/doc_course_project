"use client";

import { Fragment, useEffect, useState, type FormEvent } from "react";
import { apiGet, apiPatch, apiPost, apiPut } from "../api";
import { DateField, nowForField, toIsoDate } from "../shared/DateField";
import {
  formatDate,
  LICENSE_CATEGORIES,
  MEDICAL_LABELS,
  type Driver,
} from "../shared/fleet";
import { FormRow } from "../shared/FormRow";
import { Messages } from "../shared/Messages";
import { StatusSections } from "../shared/StatusSections";
import { useData } from "../shared/useData";

const DRIVER_SECTIONS: {
  status: Driver["employment_status"];
  label: string;
}[] = [
  { status: "ACTIVE", label: "Працюють" },
  { status: "DISMISSED", label: "Звільнені" },
];

const loadDrivers = () => apiGet<Driver[]>("/drivers/");

function driverFields(form: FormData) {
  return {
    full_name: String(form.get("full_name")),
    license_categories: form.getAll("license_categories").map(String),
    experience_years: Number(form.get("experience_years")),
    license_expiry_date: toIsoDate(String(form.get("license_expiry_date"))),
    medical_check_date: toIsoDate(String(form.get("medical_check_date"))),
  };
}

function createDriver(form: FormData) {
  return apiPost("/drivers/", {
    ...driverFields(form),
    username: form.get("username"),
    password: form.get("password"),
  });
}

function updateDriver(driver: Driver, form: FormData) {
  return apiPut(`/drivers/${driver.id}`, {
    ...driverFields(form),
    user_id: driver.user_id,
    employment_status: driver.employment_status,
  });
}

function changeStatus(driver: Driver, status: Driver["employment_status"]) {
  return apiPatch(`/drivers/${driver.id}/status`, {
    employment_status: status,
  });
}

export function DriversPage() {
  const {
    data: drivers,
    error,
    notice,
    pending,
    run,
    clearMessages,
  } = useData(loadDrivers);
  const [editing, setEditing] = useState<Driver | "new" | null>(null);

  const openForm = (next: Driver | "new" | null) => {
    clearMessages();
    setEditing(next);
  };

  useEffect(() => {
    if (editing === "new") window.scrollTo(0, 0);
  }, [editing]);

  const submit = (form: FormData) => {
    const action =
      editing && editing !== "new"
        ? () => updateDriver(editing, form)
        : () => createDriver(form);
    run(action, "Водія збережено.").then((saved) => {
      if (saved) setEditing(null);
    });
  };

  const dismiss = (driver: Driver) => {
    if (window.confirm(`Звільнити водія ${driver.full_name}?`)) {
      run(() => changeStatus(driver, "DISMISSED"), "Водія звільнено.");
    }
  };

  const form = editing && (
    <DriverForm
      key={editing === "new" ? "new" : editing.id}
      driver={editing === "new" ? null : editing}
      pending={pending}
      onSubmit={submit}
      onCancel={() => openForm(null)}
    />
  );

  return (
    <>
      <div className="page-header">
        <h1>Водії</h1>
        <button type="button" onClick={() => openForm("new")}>
          Додати водія
        </button>
      </div>
      <Messages error={error} notice={notice} onClose={clearMessages} />

      {editing === "new" && form}

      <StatusSections
        items={drivers}
        statusOf={(driver) => driver.employment_status}
        sections={DRIVER_SECTIONS}
      >
        {(rows) => (
          <table>
            <thead>
              <tr>
                <th>ПІБ</th>
                <th>Категорії</th>
                <th>Стаж</th>
                <th>Посвідчення до</th>
                <th>Медогляд</th>
                <th>Дії</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((driver) => (
                <Fragment key={driver.id}>
                  <tr>
                    <td>{driver.full_name}</td>
                    <td>{driver.license_categories.join(", ")}</td>
                    <td>{driver.experience_years} р.</td>
                    <td>{formatDate(driver.license_expiry_date)}</td>
                    <td>
                      {MEDICAL_LABELS[driver.medical_check_status]}, до{" "}
                      {formatDate(driver.medical_valid_until)}
                    </td>
                    <td className="actions">
                      {driver.employment_status === "ACTIVE" && (
                        <button
                          type="button"
                          className="secondary"
                          onClick={() => openForm(driver)}
                        >
                          Редагувати
                        </button>
                      )}
                      {driver.employment_status === "ACTIVE" ? (
                        <button
                          type="button"
                          className="secondary danger"
                          disabled={pending}
                          onClick={() => dismiss(driver)}
                        >
                          Звільнити
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="secondary"
                          disabled={pending}
                          onClick={() =>
                            run(
                              () => changeStatus(driver, "ACTIVE"),
                              "Водія поновлено.",
                            )
                          }
                        >
                          Поновити
                        </button>
                      )}
                    </td>
                  </tr>
                  {editing !== "new" && editing?.id === driver.id && (
                    <FormRow colSpan={6}>{form}</FormRow>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        )}
      </StatusSections>
    </>
  );
}

function DriverForm({
  driver,
  pending,
  onSubmit,
  onCancel,
}: {
  driver: Driver | null;
  pending: boolean;
  onSubmit: (form: FormData) => void;
  onCancel: () => void;
}) {
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSubmit(new FormData(event.currentTarget));
  };

  return (
    <form className="panel" onSubmit={submit}>
      <h2 className="panel-title">
        {driver ? `Редагування: ${driver.full_name}` : "Новий водій"}
      </h2>
      {!driver && (
        <>
          <label>
            Ім’я користувача
            <input name="username" autoComplete="off" required />
          </label>
          <label>
            Пароль
            <input
              name="password"
              type="password"
              autoComplete="new-password"
              required
            />
          </label>
        </>
      )}
      <label>
        ПІБ
        <input name="full_name" defaultValue={driver?.full_name} required />
      </label>
      <label>
        Стаж, років
        <input
          name="experience_years"
          type="number"
          min="0"
          max="60"
          defaultValue={driver?.experience_years ?? 0}
          required
        />
      </label>
      <label>
        Посвідчення дійсне до
        <DateField
          name="license_expiry_date"
          defaultValue={driver?.license_expiry_date}
          required
        />
      </label>
      <label>
        Дата медогляду
        <DateField
          name="medical_check_date"
          defaultValue={driver?.medical_check_date}
          max={nowForField().slice(0, 10)}
          required
        />
      </label>
      <fieldset className="categories">
        <legend>Категорії посвідчення</legend>
        {LICENSE_CATEGORIES.map((category) => (
          <label key={category}>
            <input
              type="checkbox"
              name="license_categories"
              value={category}
              defaultChecked={driver?.license_categories.includes(category)}
            />
            {category}
          </label>
        ))}
      </fieldset>
      <div className="form-actions">
        <button type="submit" disabled={pending}>
          Зберегти водія
        </button>
        <button type="button" className="secondary" onClick={onCancel}>
          Скасувати
        </button>
      </div>
    </form>
  );
}
