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
  { status: "ACTIVE", label: "Active" },
  { status: "DECOMMISSIONED", label: "Decommissioned" },
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
    run(action, "Vehicle saved.").then((saved) => {
      if (saved) setEditing(null);
    });
  };

  const decommission = (vehicle: Vehicle) => {
    if (window.confirm(`Decommission ${vehicle.make}?`)) {
      run(
        () => changeStatus(vehicle, "DECOMMISSIONED"),
        "Vehicle decommissioned.",
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
        <h1>Vehicles</h1>
        <button type="button" onClick={() => openForm("new")}>
          Add vehicle
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
                <th>Vehicle</th>
                <th>Year</th>
                <th>VIN</th>
                <th>License</th>
                <th>Technical state</th>
                <th>Actions</th>
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
                      <button
                        type="button"
                        className="secondary"
                        onClick={() => openForm(vehicle)}
                      >
                        Edit
                      </button>
                      {vehicle.status === "ACTIVE" ? (
                        <button
                          type="button"
                          className="secondary danger"
                          disabled={pending}
                          onClick={() => decommission(vehicle)}
                        >
                          Decommission
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="secondary"
                          disabled={pending}
                          onClick={() =>
                            run(
                              () => changeStatus(vehicle, "ACTIVE"),
                              "Vehicle reactivated.",
                            )
                          }
                        >
                          Reactivate
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
        {vehicle ? `Edit ${vehicle.make}` : "New vehicle"}
      </h2>
      <label>
        Make and model
        <input name="make" defaultValue={vehicle?.make} required />
      </label>
      <label>
        Year
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
          title="17 capital letters and digits, without I, O or Q"
          defaultValue={vehicle?.vin}
          required
        />
      </label>
      <label>
        Required license
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
          Save vehicle
        </button>
        <button type="button" className="secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}
