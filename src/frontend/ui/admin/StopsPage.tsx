"use client";

import { useEffect, useState, type FormEvent } from "react";
import { apiPut } from "../api";
import {
  compareRoutes,
  formatDateTime,
  loadRoutesAndStops,
  STATUS_LABELS,
  stopsOf,
  type RouteStop,
} from "../shared/fleet";
import { StopLine } from "../shared/StopLine";
import { useData } from "../shared/useData";

export function StopsPage() {
  const { data, error, notice, pending, run, clearMessages } =
    useData(loadRoutesAndStops);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [routes, stops] = data ?? [];
  const sorted = routes?.toSorted(compareRoutes);
  const route =
    sorted?.find((r) => r.id === selectedId) ??
    sorted?.find((r) => r.status === "PLANNED") ??
    sorted?.[0];

  useEffect(() => {
    if (error) window.scrollTo(0, 0);
  }, [error]);

  return (
    <>
      <h1>Stops</h1>
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
      {routes?.length === 0 && <p className="muted">No routes yet.</p>}
      {route && (
        <>
          <label className="route-picker">
            Route
            <select
              value={route.id}
              onChange={(event) => {
                clearMessages();
                setSelectedId(Number(event.target.value));
              }}
            >
              {sorted?.map((r) => (
                <option key={r.id} value={r.id}>
                  Route {r.id}, {STATUS_LABELS[r.status]},{" "}
                  {formatDateTime(r.departure_at)}
                </option>
              ))}
            </select>
          </label>
          {route.status === "PLANNED" ? (
            <StopsEditor
              key={route.id}
              stops={stopsOf(stops, route.id)}
              pending={pending}
              onSave={(addresses) =>
                run(
                  () =>
                    apiPut(`/routes/${route.id}/stops`, { stops: addresses }),
                  "Stops saved.",
                )
              }
            />
          ) : (
            <>
              <p className="muted stops-note">
                Stops can only be changed on a planned route.
              </p>
              <StopLine status={route.status} stops={stopsOf(stops, route.id)} />
            </>
          )}
        </>
      )}
    </>
  );
}

function StopsEditor({
  stops,
  pending,
  onSave,
}: {
  stops: RouteStop[];
  pending: boolean;
  onSave: (addresses: string[]) => void;
}) {
  const [addresses, setAddresses] = useState(stops.map((s) => s.address));

  const move = (from: number, to: number) => {
    const next = [...addresses];
    next.splice(to, 0, next.splice(from, 1)[0]);
    setAddresses(next);
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    onSave(addresses);
  };

  return (
    <form onSubmit={submit}>
      <ol className="stop-rows">
        {addresses.map((address, index) => (
          <li key={index}>
            <input
              aria-label={`Stop ${index + 1} address`}
              value={address}
              required
              onChange={(event) =>
                setAddresses(
                  addresses.map((a, i) =>
                    i === index ? event.target.value : a,
                  ),
                )
              }
            />
            <button
              type="button"
              className="secondary"
              disabled={index === 0}
              onClick={() => move(index, index - 1)}
            >
              Up
            </button>
            <button
              type="button"
              className="secondary"
              disabled={index === addresses.length - 1}
              onClick={() => move(index, index + 1)}
            >
              Down
            </button>
            <button
              type="button"
              className="secondary danger"
              disabled={addresses.length === 1}
              onClick={() =>
                setAddresses(addresses.filter((_, i) => i !== index))
              }
            >
              Remove
            </button>
          </li>
        ))}
      </ol>
      <div className="form-actions">
        <button type="submit" disabled={pending}>
          Save stops
        </button>
        <button
          type="button"
          className="secondary"
          onClick={() => setAddresses([...addresses, ""])}
        >
          Add stop
        </button>
      </div>
    </form>
  );
}
