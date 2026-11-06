"use client";

import { apiPost } from "../api";
import type { Workspace } from "../products";
import {
  compareRoutes,
  formatDateTime,
  loadRoutesAndStops,
  ROUTE_SECTIONS,
  stopsOf,
} from "../shared/fleet";
import { Messages } from "../shared/Messages";
import { StopLine } from "../shared/StopLine";
import { StatusSections } from "../shared/StatusSections";
import { useData } from "../shared/useData";

export class DriverWorkspace implements Workspace {
  render() {
    return <DriverRoutes />;
  }
}

function DriverRoutes() {
  const { data, error, pending, run, clearMessages } =
    useData(loadRoutesAndStops);
  const [routes, stops] = data ?? [];
  const sorted = routes?.toSorted(compareRoutes);

  const act = (routeId: number, path: string) => {
    run(() => apiPost(`/routes/${routeId}${path}`));
  };

  return (
    <>
      <h1>Маршрути</h1>
      <Messages error={error} onClose={clearMessages} />
      {routes?.length === 0 && <p className="muted">Маршрутів не призначено.</p>}
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
