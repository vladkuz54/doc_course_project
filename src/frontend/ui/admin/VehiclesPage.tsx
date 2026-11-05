"use client";

import { useEffect, useState, type FormEvent } from "react";
import { apiGet, apiPatch, apiPost, apiPut } from "../api";
import {
  LICENSE_CATEGORIES,
  TECHNICAL_STATE_LABELS,
  type Vehicle,
} from "../shared/fleet";
import { useData } from "../shared/useData";

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
  const { data: vehicles, error, notice, pending, run } = useData(loadVehicles);
  const [editing, setEditing] = useState<Vehicle | "new" | null>(null);

  useEffect(() => {
    if (error || editing) window.scrollTo(0, 0);
  }, [error, editing]);

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

  return (
    <>
      <div className="page-header">
        <h1>Vehicles</h1>
        <button type="button" onClick={() => setEditing("new")}>
          Add vehicle
        </button>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {notice && (
        <p className="notice" role="status">
          {notice}
        </p>
      )}

      {editing && (
        <VehicleForm
          key={editing === "new" ? "new" : editing.id}
          vehicle={editing === "new" ? null : editing}
          pending={pending}
          onSubmit={submit}
          onCancel={() => setEditing(null)}
        />
      )}

      <table>
        <thead>
          <tr>
            <th>Vehicle</th>
            <th>Year</th>
            <th>VIN</th>
            <th>License</th>
            <th>Technical state</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {vehicles?.map((vehicle) => (
            <tr key={vehicle.id}>
              <td>{vehicle.make}</td>
              <td>{vehicle.year}</td>
              <td>{vehicle.vin}</td>
              <td>{vehicle.required_license_category}</td>
              <td>{TECHNICAL_STATE_LABELS[vehicle.technical_state]}</td>
              <td>
                {vehicle.status === "ACTIVE" ? "Active" : "Decommissioned"}
              </td>
              <td className="actions">
                <button
                  type="button"
                  className="secondary"
                  onClick={() => setEditing(vehicle)}
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
          ))}
        </tbody>
      </table>
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
