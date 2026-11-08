"use client";

import { Fragment, useEffect, useState, type FormEvent } from "react";
import { apiGet, apiPost, apiPut } from "../api";
import { DateField, nowForField, toIsoDateTime } from "../shared/DateField";
import {
  compareRoutes,
  formatDateTime,
  ROUTE_SECTIONS,
  stopsOf,
  type Driver,
  type Route,
  type RouteStop,
  type Vehicle,
} from "../shared/fleet";
import { FormRow } from "../shared/FormRow";
import { Messages } from "../shared/Messages";
import { StatusSections } from "../shared/StatusSections";
import { StopLine } from "../shared/StopLine";
import { useData } from "../shared/useData";
import {
  EMPTY_STOP,
  joinAddress,
  splitAddress,
  StopFields,
  type StopAddress,
} from "./StopFields";

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
    title: "Розпочати маршрут",
    label: "Час початку",
    path: "start",
    field: "started_at",
    notice: "Маршрут розпочато.",
  },
  close: {
    title: "Закрити маршрут",
    label: "Час повернення",
    path: "complete",
    field: "returned_at",
    notice: "Маршрут закрито.",
  },
  complete: {
    title: "Завершити маршрут",
    label: "Час повернення",
    path: "complete",
    field: "returned_at",
    notice: "Маршрут завершено.",
  },
};

const loadRoutesPage = () =>
  Promise.all([
    apiGet<Route[]>("/routes/"),
    apiGet<Driver[]>("/drivers/"),
    apiGet<Vehicle[]>("/vehicles/"),
    apiGet<RouteStop[]>("/route-stops/"),
  ]);

function routeFields(form: FormData) {
  return {
    driver_id: Number(form.get("driver_id")) || null,
    vehicle_id: Number(form.get("vehicle_id")) || null,
    distance: Number(form.get("distance")),
    departure_at: toIsoDateTime(String(form.get("departure_at"))),
  };
}

function createRoute(form: FormData, stops: StopAddress[]) {
  return apiPost("/routes/", {
    ...routeFields(form),
    stops: stops.map(joinAddress),
  });
}

export function RoutesPage() {
  const { data, error, notice, pending, reload, run, clearMessages } =
    useData(loadRoutesPage);
  const [editing, setEditing] = useState<Editing | null>(null);
  const [stopsOpen, setStopsOpen] = useState<number | null>(null);

  const openForm = (next: Editing | null) => {
    clearMessages();
    setEditing(next);
  };
  const [routes, drivers, vehicles, stops] = data ?? [];

  const updateRoute = async (
    route: Route,
    form: FormData,
    edited: StopAddress[],
  ) => {
    await apiPut(`/routes/${route.id}`, routeFields(form));
    await reload();
    const addresses = edited.map(joinAddress);
    const current = stopsOf(stops, route.id).map((stop) => stop.address);
    if (addresses.join("\n") !== current.join("\n")) {
      await apiPut(`/routes/${route.id}/stops`, { stops: addresses });
    }
  };

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
        initialStops={stopsOf(stops, editing.route.id).map((stop) =>
          splitAddress(stop.address),
        )}
        drivers={drivers ?? []}
        vehicles={vehicles ?? []}
        pending={pending}
        onSubmit={(form, edited) =>
          save(
            () => updateRoute(editing.route, form, edited),
            "Маршрут збережено.",
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
        <h1>Маршрути</h1>
        <button type="button" onClick={() => openForm({ form: "new" })}>
          Додати маршрут
        </button>
      </div>
      <Messages error={error} notice={notice} onClose={clearMessages} />

      {editing?.form === "new" && (
        <RouteForm
          key="new"
          route={null}
          initialStops={[EMPTY_STOP]}
          drivers={drivers ?? []}
          vehicles={vehicles ?? []}
          pending={pending}
          onSubmit={(form, stops) =>
            save(() => createRoute(form, stops), "Маршрут збережено.")
          }
          onCancel={() => openForm(null)}
        />
      )}
      <StatusSections
        items={routes?.toSorted(compareRoutes)}
        statusOf={(route) => route.status}
        sections={ROUTE_SECTIONS}
      >
        {(rows) => (
          <table className="compact">
            <thead>
              <tr>
                <th>Маршрут</th>
                <th>Виїзд</th>
                <th>Відстань</th>
                <th>Водій</th>
                <th>Транспорт</th>
                <th>Дії</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((route) => (
                <Fragment key={route.id}>
                  <tr>
                    <td>{route.id}</td>
                    <td>{formatDateTime(route.departure_at)}</td>
                    <td>{route.distance} км</td>
                    <td className="name">
                      {drivers?.find((d) => d.id === route.driver_id)
                        ?.full_name ?? "Не призначено"}
                    </td>
                    <td>
                      {vehicles?.find((v) => v.id === route.vehicle_id)?.make ??
                        "Не призначено"}
                    </td>
                    <td className="actions">
                      <button
                        type="button"
                        className="secondary"
                        aria-expanded={stopsOpen === route.id}
                        onClick={() =>
                          setStopsOpen(stopsOpen === route.id ? null : route.id)
                        }
                      >
                        Зупинки
                      </button>
                      {route.status === "PLANNED" && (
                        <>
                          <button
                            type="button"
                            className="secondary"
                            onClick={() => openForm({ form: "edit", route })}
                          >
                            Редагувати
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
                                Розпочати
                              </button>
                            )}
                          <button
                            type="button"
                            className="secondary"
                            onClick={() => openForm({ form: "close", route })}
                          >
                            Закрити
                          </button>
                        </>
                      )}
                      {route.status === "IN_PROGRESS" && (
                        <button
                          type="button"
                          className="secondary"
                          onClick={() => openForm({ form: "complete", route })}
                        >
                          Завершити
                        </button>
                      )}
                      {(route.status === "PLANNED" ||
                        route.status === "IN_PROGRESS") && (
                        <button
                          type="button"
                          className="secondary danger"
                          disabled={pending}
                          onClick={() =>
                            confirmed(
                              `Скасувати маршрут №${route.id}?`,
                              () => apiPost(`/routes/${route.id}/cancel`),
                              "Маршрут скасовано.",
                            )
                          }
                        >
                          Скасувати
                        </button>
                      )}
                    </td>
                  </tr>
                  {stopsOpen === route.id && (
                    <FormRow colSpan={6}>
                      <div className="stops-view">
                        <StopLine
                          status={route.status}
                          stops={stopsOf(stops, route.id)}
                        />
                      </div>
                    </FormRow>
                  )}
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
  initialStops,
  drivers,
  vehicles,
  pending,
  onSubmit,
  onCancel,
}: {
  route: Route | null;
  initialStops: StopAddress[];
  drivers: Driver[];
  vehicles: Vehicle[];
  pending: boolean;
  onSubmit: (form: FormData, stops: StopAddress[]) => void;
  onCancel: () => void;
}) {
  const [stops, setStops] = useState(initialStops);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSubmit(new FormData(event.currentTarget), stops);
  };

  return (
    <form className="panel" onSubmit={submit}>
      <h2 className="panel-title">
        {route ? `Редагування маршруту №${route.id}` : "Новий маршрут"}
      </h2>
      <label>
        Водій
        <select name="driver_id" defaultValue={route?.driver_id ?? ""}>
          {!route?.driver_id && <option value="">Не призначено</option>}
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
        Транспорт
        <select name="vehicle_id" defaultValue={route?.vehicle_id ?? ""}>
          {!route?.vehicle_id && <option value="">Не призначено</option>}
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
        Відстань, км
        <input
          name="distance"
          type="number"
          min="0.1"
          max="100000"
          step="any"
          defaultValue={route?.distance}
          required
        />
      </label>
      <label>
        Виїзд
        <DateField
          name="departure_at"
          withTime
          defaultValue={route?.departure_at}
          required
        />
      </label>
      <StopFields stops={stops} onChange={setStops} />
      <div className="form-actions">
        <button type="submit" disabled={pending}>
          Зберегти маршрут
        </button>
        <button type="button" className="secondary" onClick={onCancel}>
          Скасувати
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
        {title} №{route.id}
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
          Назад
        </button>
      </div>
    </form>
  );
}
