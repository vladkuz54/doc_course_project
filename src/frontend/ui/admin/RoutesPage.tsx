"use client";

import { Fragment, useEffect, useState, type FormEvent } from "react";
import { apiDelete, apiGet, apiPost, apiPut } from "../api";
import { DateField, nowForField, toIsoDateTime } from "../shared/DateField";
import {
  compareRoutes,
  formatDateTime,
  ROUTE_SECTIONS,
  type Driver,
  type Route,
  type Vehicle,
} from "../shared/fleet";
import { FormRow } from "../shared/FormRow";
import { Messages } from "../shared/Messages";
import { StatusSections } from "../shared/StatusSections";
import { useData } from "../shared/useData";

type TimeAction = "start" | "close" | "complete";

type Editing =
  | { form: "new" }
  | { form: "edit"; route: Route }
  | { form: TimeAction; route: Route };

const TIME_ACTIONS: Record<
  TimeAction,
  { title: string; label: string; path: string; field: string; notice: string }
> = {
  start: {
    title: "Start route",
    label: "Start time",
    path: "start",
    field: "started_at",
    notice: "Route started.",
  },
  close: {
    title: "Close route",
    label: "Return time",
    path: "complete",
    field: "returned_at",
    notice: "Route closed.",
  },
  complete: {
    title: "Complete route",
    label: "Return time",
    path: "complete",
    field: "returned_at",
    notice: "Route completed.",
  },
};

const loadRoutesPage = () =>
  Promise.all([
    apiGet<Route[]>("/routes/"),
    apiGet<Driver[]>("/drivers/"),
    apiGet<Vehicle[]>("/vehicles/"),
  ]);

function isActive(route: Route) {
  return route.status === "PLANNED" || route.status === "IN_PROGRESS";
}

function routeFields(form: FormData) {
  return {
    driver_id: Number(form.get("driver_id")) || null,
    vehicle_id: Number(form.get("vehicle_id")) || null,
    distance: Number(form.get("distance")),
    departure_at: toIsoDateTime(String(form.get("departure_at"))),
  };
}

function createRoute(form: FormData) {
  return apiPost("/routes/", {
    ...routeFields(form),
    stops: String(form.get("stops"))
      .split("\n")
      .map((address) => address.trim())
      .filter(Boolean),
  });
}

export function RoutesPage() {
  const { data, error, notice, pending, run, clearMessages } =
    useData(loadRoutesPage);
  const [editing, setEditing] = useState<Editing | null>(null);

  const openForm = (next: Editing | null) => {
    clearMessages();
    setEditing(next);
  };
  const [routes, drivers, vehicles] = data ?? [];

  useEffect(() => {
    if (editing?.form === "new") window.scrollTo(0, 0);
  }, [editing]);

  const save = (action: () => Promise<unknown>, doneNotice: string) => {
    run(action, doneNotice).then((saved) => {
      if (saved) setEditing(null);
    });
  };

  const confirmed = (
    message: string,
    action: () => Promise<unknown>,
    doneNotice: string,
  ) => {
    if (window.confirm(message)) run(action, doneNotice);
  };

  const rowForm =
    editing?.form === "edit" ? (
      <RouteForm
        key={editing.route.id}
        route={editing.route}
        drivers={drivers ?? []}
        vehicles={vehicles ?? []}
        pending={pending}
        onSubmit={(form) =>
          save(
            () => apiPut(`/routes/${editing.route.id}`, routeFields(form)),
            "Route saved.",
          )
        }
        onCancel={() => openForm(null)}
      />
    ) : editing && editing.form !== "new" ? (
      <RouteTimeForm
        key={`${editing.form}-${editing.route.id}`}
        action={editing.form}
        route={editing.route}
        pending={pending}
        onSubmit={(time) => {
          const { path, field, notice: done } = TIME_ACTIONS[editing.form];
          save(
            () =>
              apiPost(`/routes/${editing.route.id}/${path}`, {
                [field]: time,
              }),
            done,
          );
        }}
        onCancel={() => openForm(null)}
      />
    ) : null;

  return (
    <>
      <div className="page-header">
        <h1>Routes</h1>
        <button type="button" onClick={() => openForm({ form: "new" })}>
          Add route
        </button>
      </div>
      <Messages error={error} notice={notice} onClose={clearMessages} />

      {editing?.form === "new" && (
        <RouteForm
          key="new"
          route={null}
          drivers={drivers ?? []}
          vehicles={vehicles ?? []}
          pending={pending}
          onSubmit={(form) => save(() => createRoute(form), "Route saved.")}
          onCancel={() => openForm(null)}
        />
      )}
      <StatusSections
        items={routes?.toSorted(compareRoutes)}
        statusOf={(route) => route.status}
        sections={ROUTE_SECTIONS}
      >
        {(rows) => (
          <table>
            <thead>
              <tr>
                <th>Route</th>
                <th>Departure</th>
                <th>Distance</th>
                <th>Driver</th>
                <th>Vehicle</th>
                {isActive(rows[0]) && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {rows.map((route) => (
                <Fragment key={route.id}>
                  <tr>
                    <td>{route.id}</td>
                    <td>{formatDateTime(route.departure_at)}</td>
                    <td>{route.distance} km</td>
                    <td>
                      {drivers?.find((d) => d.id === route.driver_id)
                        ?.full_name ?? "Not assigned"}
                    </td>
                    <td>
                      {vehicles?.find((v) => v.id === route.vehicle_id)?.make ??
                        "Not assigned"}
                    </td>
                    {isActive(route) && (
                      <td className="actions">
                        {route.status === "PLANNED" && (
                          <>
                            <button
                              type="button"
                              className="secondary"
                              onClick={() => openForm({ form: "edit", route })}
                            >
                              Edit
                            </button>
                            {route.driver_id !== null &&
                              route.vehicle_id !== null && (
                                <button
                                  type="button"
                                  className="secondary"
                                  onClick={() =>
                                    openForm({ form: "start", route })
                                  }
                                >
                                  Start
                                </button>
                              )}
                            <button
                              type="button"
                              className="secondary"
                              onClick={() => openForm({ form: "close", route })}
                            >
                              Close
                            </button>
                          </>
                        )}
                        {route.status === "IN_PROGRESS" && (
                          <button
                            type="button"
                            className="secondary"
                            onClick={() =>
                              openForm({ form: "complete", route })
                            }
                          >
                            Complete
                          </button>
                        )}
                        <button
                          type="button"
                          className="secondary danger"
                          disabled={pending}
                          onClick={() =>
                            confirmed(
                              `Cancel route ${route.id}?`,
                              () => apiPost(`/routes/${route.id}/cancel`),
                              "Route cancelled.",
                            )
                          }
                        >
                          Cancel
                        </button>
                        {route.status === "PLANNED" && (
                          <button
                            type="button"
                            className="secondary danger"
                            disabled={pending}
                            onClick={() =>
                              confirmed(
                                `Delete route ${route.id}?`,
                                () => apiDelete(`/routes/${route.id}`),
                                "Route deleted.",
                              )
                            }
                          >
                            Delete
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                  {editing &&
                    editing.form !== "new" &&
                    editing.route.id === route.id && (
                      <FormRow colSpan={6}>{rowForm}</FormRow>
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

function RouteForm({
  route,
  drivers,
  vehicles,
  pending,
  onSubmit,
  onCancel,
}: {
  route: Route | null;
  drivers: Driver[];
  vehicles: Vehicle[];
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
        {route ? `Edit route ${route.id}` : "New route"}
      </h2>
      <label>
        Driver
        <select name="driver_id" defaultValue={route?.driver_id ?? ""}>
          {!route?.driver_id && <option value="">Not assigned</option>}
          {drivers
            .filter(
              (d) =>
                d.employment_status === "ACTIVE" || d.id === route?.driver_id,
            )
            .map((d) => (
              <option key={d.id} value={d.id}>
                {d.full_name}
              </option>
            ))}
        </select>
      </label>
      <label>
        Vehicle
        <select name="vehicle_id" defaultValue={route?.vehicle_id ?? ""}>
          {!route?.vehicle_id && <option value="">Not assigned</option>}
          {vehicles
            .filter((v) => v.status === "ACTIVE" || v.id === route?.vehicle_id)
            .map((v) => (
              <option key={v.id} value={v.id}>
                {v.make}
              </option>
            ))}
        </select>
      </label>
      <label>
        Distance, km
        <input
          name="distance"
          type="number"
          min="0.1"
          step="any"
          defaultValue={route?.distance}
          required
        />
      </label>
      <label>
        Departure
        <DateField
          name="departure_at"
          withTime
          defaultValue={route?.departure_at}
          required
        />
      </label>
      {!route && (
        <label className="wide">
          Stops, one address per line
          <textarea name="stops" rows={4} required />
        </label>
      )}
      <div className="form-actions">
        <button type="submit" disabled={pending}>
          Save route
        </button>
        <button type="button" className="secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}

function RouteTimeForm({
  action,
  route,
  pending,
  onSubmit,
  onCancel,
}: {
  action: TimeAction;
  route: Route;
  pending: boolean;
  onSubmit: (time: string) => void;
  onCancel: () => void;
}) {
  const { title, label } = TIME_ACTIONS[action];

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const time = new FormData(event.currentTarget).get("time");
    onSubmit(toIsoDateTime(String(time)));
  };

  return (
    <form className="panel" onSubmit={submit}>
      <h2 className="panel-title">
        {title} {route.id}
      </h2>
      <label>
        {label}
        <DateField
          name="time"
          withTime
          required
          defaultValue={action === "close" ? undefined : nowForField()}
        />
      </label>
      <div className="form-actions">
        <button type="submit" disabled={pending}>
          {title}
        </button>
        <button type="button" className="secondary" onClick={onCancel}>
          Back
        </button>
      </div>
    </form>
  );
}
