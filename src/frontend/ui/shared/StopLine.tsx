"use client";

import type { RouteStatus, RouteStop } from "./fleet";

export function StopLine({
  status,
  stops,
  onArrive,
  disabled,
}: {
  status: RouteStatus;
  stops: RouteStop[];
  onArrive?: (stop: RouteStop) => void;
  disabled?: boolean;
}) {
  const canArrive = (stop: RouteStop) =>
    status === "IN_PROGRESS" &&
    !stop.arrived_at &&
    !stops.some((s) => s.arrived_at && s.order_no > stop.order_no);

  return (
    <ol className="stops">
      {stops.map((stop) => (
        <li key={stop.id} className={stop.arrived_at ? "reached" : undefined}>
          <span>{stop.address}</span>
          {stop.arrived_at && (
            <time className="muted" dateTime={stop.arrived_at}>
              {new Date(stop.arrived_at).toLocaleTimeString("en-GB", {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </time>
          )}
          {onArrive && canArrive(stop) && (
            <button
              type="button"
              className="secondary"
              disabled={disabled}
              onClick={() => onArrive(stop)}
            >
              Прибув
            </button>
          )}
        </li>
      ))}
    </ol>
  );
}
