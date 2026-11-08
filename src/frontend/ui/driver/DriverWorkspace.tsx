"use client";

import { apiGet, apiPost } from "../api";
import type { Workspace } from "../products";
import {
  compareRoutes,
  formatDateTime,
  loadRoutesAndStops,
  ROUTE_SECTIONS,
  stopsOf,
  TECHNICAL_STATE_LABELS,
  type Vehicle,
} from "../shared/fleet";
import { Messages } from "../shared/Messages";
import { StopLine } from "../shared/StopLine";
import { StatusSections } from "../shared/StatusSections";
import { useData } from "../shared/useData";
import { useHash } from "../shared/useHash";
import { DriverRequestsPage } from "./DriverRequestsPage";

const loadDriverRoutes = () =>
  Promise.all([loadRoutesAndStops(), apiGet<Vehicle[]>("/vehicles/")]);

export class DriverWorkspace implements Workspace {
  render() {
    return <DriverScreens workspace={this} />;
  }

  requestMedicalCheck(driverId: number, checkDate: string) {
    return apiPost("/driver-requests/", {
      driver_id: driverId,
      type: "MEDICAL_CHECK",
      medical_check_date: checkDate,
    });
  }

  submitLicenseUpdate(
    driverId: number,
    category: string | null,
    expiryDate: string,
  ) {
    return apiPost("/driver-requests/", {
      driver_id: driverId,
      type: "LICENSE_UPDATE",
      new_license_category: category,
      new_license_expiry_date: expiryDate,
    });
  }
}

function DriverScreens({ workspace }: { workspace: DriverWorkspace }) {
  const hash = useHash();
  if (hash === "requests") return <DriverRequestsPage workspace={workspace} />;
  return <DriverRoutes />;
}

function DriverRoutes() {
  const { data, error, pending, run, clearMessages } =
    useData(loadDriverRoutes);
  const [[routes, stops] = [], vehicles] = data ?? [];
  const sorted = routes?.toSorted(compareRoutes);

  const act = (routeId: number, path: string) => {
    run(() => apiPost(`/routes/${routeId}${path}`));
  };

  return (
    <>
      <h1>Маршрути</h1>
      <Messages error={error} onClose={clearMessages} />
      {routes?.length === 0 && (
        <p className="muted">Маршрутів не призначено.</p>
      )}
      <StatusSections
        items={sorted}
        statusOf={(route) => route.status}
        sections={ROUTE_SECTIONS}
      >
        {(rows) => (
          <>
            {rows.map((route) => (
              <article key={route.id} className="route">
                <div className="route-header">
                  <div>
                    <h3>Маршрут №{route.id}</h3>
                    <p className="muted">
                      {formatDateTime(route.departure_at)}, {route.distance} км
                    </p>
                  </div>
                  {route.status === "PLANNED" && route.vehicle_id !== null && (
                    <button
                      type="button"
                      disabled={pending}
                      onClick={() => act(route.id, "/start")}
                    >
                      Розпочати
                    </button>
                  )}
                  {route.status === "IN_PROGRESS" && (
                    <button
                      type="button"
                      disabled={pending}
                      onClick={() => act(route.id, "/complete")}
                    >
                      Повернувся
                    </button>
                  )}
                </div>
                <RouteVehicle
                  vehicle={vehicles?.find((v) => v.id === route.vehicle_id)}
                />
                <StopLine
                  status={route.status}
                  stops={stopsOf(stops, route.id)}
                  disabled={pending}
                  onArrive={(stop) => act(route.id, `/stops/${stop.id}/arrive`)}
                />
              </article>
            ))}
          </>
        )}
      </StatusSections>
    </>
  );
}

function RouteVehicle({ vehicle }: { vehicle?: Vehicle }) {
  if (!vehicle) return <p className="muted">Транспорт не призначено.</p>;
  return (
    <dl className="details">
      <dt>Транспорт</dt>
      <dd>{vehicle.make}</dd>
      <dt>Рік</dt>
      <dd>{vehicle.year}</dd>
      <dt>VIN</dt>
      <dd>{vehicle.vin}</dd>
      <dt>Категорія</dt>
      <dd>{vehicle.required_license_category}</dd>
      <dt>Технічний стан</dt>
      <dd>{TECHNICAL_STATE_LABELS[vehicle.technical_state]}</dd>
    </dl>
  );
}
