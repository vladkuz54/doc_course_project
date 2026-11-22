"use client";

import { Fragment, useEffect, useState, type FormEvent } from "react";
import { apiGet, apiPatch, apiPost, apiPut } from "../api";
import {
  LICENSE_CATEGORIES,
  TECHNICAL_STATE_LABELS,
  type Vehicle,
} from "../shared/fleet";
import { FormRow } from "../shared/FormRow";
import { Messages } from "../shared/Messages";
import { StatusSections } from "../shared/StatusSections";
import { useData } from "../shared/useData";

const VEHICLE_SECTIONS: { status: Vehicle["status"]; label: string }[] = [
  { status: "ACTIVE", label: "Активний" },
  { status: "DECOMMISSIONED", label: "Списаний" },
];

const loadVehicles = () => apiGet<Vehicle[]>("/vehicles/");

function vehicleFields(form: FormData) {
  return {
    make: form.get("make"),
    year: Number(form.get("year")),
    vin: form.get("vin"),
    required_license_category: form.get("required_license_category"),
  };
}

function changeStatus(vehicle: Vehicle, status: Vehicle["status"]) {
  return apiPatch(`/vehicles/${vehicle.id}/status`, { status });
}

export function VehiclesPage() {
  const {
    data: vehicles,
    error,
    notice,
    pending,
    run,
    clearMessages,
  } = useData(loadVehicles);
  const [editing, setEditing] = useState<Vehicle | "new" | null>(null);

  const openForm = (next: Vehicle | "new" | null) => {
    clearMessages();
    setEditing(next);
  };

  useEffect(() => {
    if (editing === "new") window.scrollTo(0, 0);
  }, [editing]);

  const submit = (form: FormData) => {
    const action =
      editing && editing !== "new"
        ? () =>
            apiPut(`/vehicles/${editing.id}`, {
              ...vehicleFields(form),
              status: editing.status,
            })
        : () => apiPost("/vehicles/", vehicleFields(form));
    run(action, "Транспорт збережено.").then((saved) => {
      if (saved) setEditing(null);
    });
  };

  const decommission = (vehicle: Vehicle) => {
    if (window.confirm(`Списати ${vehicle.make}?`)) {
      run(
        () => changeStatus(vehicle, "DECOMMISSIONED"),
        "Транспорт списано.",
      );
    }
  };

  const form = editing && (
    <VehicleForm
      key={editing === "new" ? "new" : editing.id}
      vehicle={editing === "new" ? null : editing}
      pending={pending}
      onSubmit={submit}
      onCancel={() => openForm(null)}
    />
  );

  return (
    <>
      <div className="page-header">
        <h1>Транспорт</h1>
        <button type="button" onClick={() => openForm("new")}>
          Додати транспорт
        </button>
      </div>
      <Messages error={error} notice={notice} onClose={clearMessages} />

      {editing === "new" && form}

      <StatusSections
        items={vehicles}
        statusOf={(vehicle) => vehicle.status}
        sections={VEHICLE_SECTIONS}
      >
        {(rows) => (
          <table>
            <thead>
              <tr>
                <th>Транспорт</th>
                <th>Рік</th>
                <th>VIN</th>
                <th>Категорія</th>
                <th>Технічний стан</th>
                <th>Дії</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((vehicle) => (
                <Fragment key={vehicle.id}>
                  <tr>
                    <td>{vehicle.make}</td>
                    <td>{vehicle.year}</td>
                    <td>{vehicle.vin}</td>
                    <td>{vehicle.required_license_category}</td>
                    <td>{TECHNICAL_STATE_LABELS[vehicle.technical_state]}</td>
                    <td className="actions">
                      {vehicle.status === "ACTIVE" && (
                        <button
                          type="button"
                          className="secondary"
                          onClick={() => openForm(vehicle)}
                        >
                          Редагувати
                        </button>
                      )}
                      {vehicle.status === "ACTIVE" ? (
                        <button
                          type="button"
                          className="secondary danger"
                          disabled={pending}
                          onClick={() => decommission(vehicle)}
                        >
                          Списати
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="secondary"
                          disabled={pending}
                          onClick={() =>
                            run(
                              () => changeStatus(vehicle, "ACTIVE"),
                              "Транспорт повернуто в роботу.",
                            )
                          }
                        >
                          Повернути в роботу
                        </button>
                      )}
                    </td>
                  </tr>
                  {editing !== "new" && editing?.id === vehicle.id && (
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

function VehicleForm({
  vehicle,
  pending,
  onSubmit,
  onCancel,
}: {
  vehicle: Vehicle | null;
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
        {vehicle ? `Редагування: ${vehicle.make}` : "Новий транспорт"}
      </h2>
      <label>
        Марка й модель
        <input name="make" defaultValue={vehicle?.make} required />
      </label>
      <label>
        Рік
        <input
          name="year"
          type="number"
          min="1980"
          max={new Date().getFullYear() + 1}
          defaultValue={vehicle?.year}
          required
        />
      </label>
      <label>
        VIN
        <input
          name="vin"
          pattern="[A-HJ-NPR-Z0-9]{17}"
          title="17 символів: великі латинські літери (крім I, O, Q) і цифри"
          defaultValue={vehicle?.vin}
          required
        />
      </label>
      <label>
        Потрібна категорія
        <select
          name="required_license_category"
          defaultValue={vehicle?.required_license_category ?? "B"}
        >
          {LICENSE_CATEGORIES.map((category) => (
            <option key={category}>{category}</option>
          ))}
        </select>
      </label>
      <div className="form-actions">
        <button type="submit" disabled={pending}>
          Зберегти транспорт
        </button>
        <button type="button" className="secondary" onClick={onCancel}>
          Скасувати
        </button>
      </div>
    </form>
  );
}
