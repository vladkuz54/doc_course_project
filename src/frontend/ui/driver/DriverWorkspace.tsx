"use client";

import { useState } from "react";
import { apiPost } from "../api";
import type { Workspace } from "../products";
import {
  compareRoutes,
  formatDateTime,
  loadRoutesAndStops,
  STATUS_LABELS,
  stopsOf,
} from "../shared/fleet";
import { StopLine } from "../shared/StopLine";
import { useData } from "../shared/useData";

export class DriverWorkspace implements Workspace {
  render() {
    return <DriverRoutes />;
  }
}

function DriverRoutes() {
  const { data, error, pending, run } = useData(loadRoutesAndStops);
  const [actedOn, setActedOn] = useState<number | null>(null);
  const [routes, stops] = data ?? [];
  const sorted = routes?.toSorted(compareRoutes);

  const act = (routeId: number, path: string) => {
    setActedOn(routeId);
    run(() => apiPost(`/routes/${routeId}${path}`));
  };

  return (
    <>
      <h1>Routes</h1>
      {error && actedOn === null && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {routes?.length === 0 && <p className="muted">No routes assigned.</p>}
      {sorted?.map((route) => (
        <article key={route.id} className="route">
          <div className="route-header">
            <div>
              <h2>Route {route.id}</h2>
              <p className="muted">
                {STATUS_LABELS[route.status]},{" "}
                {formatDateTime(route.departure_at)}, {route.distance} km
              </p>
            </div>
            {route.status === "PLANNED" && route.vehicle_id !== null && (
              <button
                type="button"
                disabled={pending}
                onClick={() => act(route.id, "/start")}
              >
                Start
              </button>
            )}
            {route.status === "IN_PROGRESS" && (
              <button
                type="button"
                disabled={pending}
                onClick={() => act(route.id, "/complete")}
              >
                Returned
              </button>
            )}
          </div>
          {error && actedOn === route.id && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
          <StopLine
            status={route.status}
            stops={stopsOf(stops, route.id)}
            disabled={pending}
            onArrive={(stop) => act(route.id, `/stops/${stop.id}/arrive`)}
          />
        </article>
      ))}
    </>
  );
}
