"use client";

import { useEffect, useState, type FormEvent } from "react";
import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from "../api";
import { DateField, toIsoDate } from "../shared/DateField";
import {
  formatDate,
  LICENSE_CATEGORIES,
  MEDICAL_LABELS,
  type Driver,
} from "../shared/fleet";
import { Messages } from "../shared/Messages";
import { useData } from "../shared/useData";

const loadDrivers = () => apiGet<Driver[]>("/drivers/");

function driverFields(form: FormData) {
  return {
    full_name: String(form.get("full_name")),
    license_categories: form.getAll("license_categories").map(String),
    experience_years: Number(form.get("experience_years")),
    license_expiry_date: toIsoDate(String(form.get("license_expiry_date"))),
    medical_check_date: toIsoDate(String(form.get("medical_check_date"))),
    medical_valid_until: toIsoDate(String(form.get("medical_valid_until"))),
  };
}

async function createDriver(form: FormData) {
  const user = await apiPost<{ id: number }>("/users/", {
    username: form.get("username"),
    password: form.get("password"),
    role: "DRIVER",
  });
  try {
    await apiPost("/drivers/", { ...driverFields(form), user_id: user.id });
  } catch (error) {
    await apiDelete(`/users/${user.id}`);
    throw error;
  }
}

function updateDriver(driver: Driver, form: FormData) {
  return apiPut(`/drivers/${driver.id}`, {
    ...driverFields(form),
    user_id: driver.user_id,
    employment_status: driver.employment_status,
    medical_check_status: form.get("medical_check_status"),
  });
}

function changeStatus(driver: Driver, status: Driver["employment_status"]) {
  return apiPatch(`/drivers/${driver.id}/status`, {
    employment_status: status,
  });
}

export function DriversPage() {
  const { data: drivers, error, notice, pending, run, clearMessages } = useData(loadDrivers);
  const [editing, setEditing] = useState<Driver | "new" | null>(null);

  const openForm = (next: Driver | "new" | null) => {
    clearMessages();
    setEditing(next);
  };

  useEffect(() => {
    if (editing) window.scrollTo(0, 0);
  }, [editing]);

  const submit = (form: FormData) => {
    const action =
      editing && editing !== "new"
        ? () => updateDriver(editing, form)
        : () => createDriver(form);
    run(action, "Driver saved.").then((saved) => {
      if (saved) setEditing(null);
    });
  };

  const dismiss = (driver: Driver) => {
    if (window.confirm(`Dismiss ${driver.full_name}?`)) {
      run(() => changeStatus(driver, "DISMISSED"), "Driver dismissed.");
    }
  };

  return (
    <>
      <div className="page-header">
        <h1>Drivers</h1>
        <button type="button" onClick={() => openForm("new")}>
          Add driver
        </button>
      </div>
      <Messages error={error} notice={notice} onClose={clearMessages} />

      {editing && (
        <DriverForm
          key={editing === "new" ? "new" : editing.id}
          driver={editing === "new" ? null : editing}
          pending={pending}
          onSubmit={submit}
          onCancel={() => openForm(null)}
        />
      )}

      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Categories</th>
            <th>Experience</th>
            <th>License until</th>
            <th>Medical check</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {drivers?.map((driver) => (
            <tr key={driver.id}>
              <td>{driver.full_name}</td>
              <td>{driver.license_categories.join(", ")}</td>
              <td>{driver.experience_years} years</td>
              <td>{formatDate(driver.license_expiry_date)}</td>
              <td>
                {MEDICAL_LABELS[driver.medical_check_status]}, until{" "}
                {formatDate(driver.medical_valid_until)}
              </td>
              <td>
                {driver.employment_status === "ACTIVE" ? "Active" : "Dismissed"}
              </td>
              <td className="actions">
                <button
                  type="button"
                  className="secondary"
                  onClick={() => openForm(driver)}
                >
                  Edit
                </button>
                {driver.employment_status === "ACTIVE" ? (
                  <button
                    type="button"
                    className="secondary danger"
                    disabled={pending}
                    onClick={() => dismiss(driver)}
                  >
                    Dismiss
                  </button>
                ) : (
                  <button
                    type="button"
                    className="secondary"
                    disabled={pending}
                    onClick={() =>
                      run(
                        () => changeStatus(driver, "ACTIVE"),
                        "Driver reinstated.",
                      )
                    }
                  >
                    Reinstate
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
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
        {driver ? `Edit ${driver.full_name}` : "New driver"}
      </h2>
      {!driver && (
        <>
          <label>
            Username
            <input name="username" autoComplete="off" required />
          </label>
          <label>
            Password
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
        Full name
        <input name="full_name" defaultValue={driver?.full_name} required />
      </label>
      <label>
        Experience, years
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
        License valid until
        <DateField
          name="license_expiry_date"
          defaultValue={driver?.license_expiry_date}
          required
        />
      </label>
      <label>
        Medical check date
        <DateField
          name="medical_check_date"
          defaultValue={driver?.medical_check_date}
          required
        />
      </label>
      <label>
        Medical valid until
        <DateField
          name="medical_valid_until"
          defaultValue={driver?.medical_valid_until}
          required
        />
      </label>
      {driver && (
        <label>
          Medical status
          <select
            name="medical_check_status"
            defaultValue={driver.medical_check_status}
          >
            {Object.entries(MEDICAL_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
      )}
      <fieldset className="categories">
        <legend>License categories</legend>
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
          Save driver
        </button>
        <button type="button" className="secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}
