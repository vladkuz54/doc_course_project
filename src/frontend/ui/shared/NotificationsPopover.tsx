"use client";

import { useEffect, useRef } from "react";
import { apiGet, apiPatch } from "../api";
import { formatDateTime } from "./fleet";
import { useData } from "./useData";

export type RelatedEntity = "drivers" | "vehicles" | "routes" | "driver_requests";

type Notification = {
  id: number;
  text: string;
  related_entity: RelatedEntity;
  created_at: string;
  is_read: boolean;
};

const REFRESH_MS = 15000;

const loadNotifications = () => apiGet<Notification[]>("/notifications/");

const markAsRead = (id: number) => apiPatch(`/notifications/${id}/read`);

export function NotificationsPopover({
  openPage,
  canCheckDeadlines = false,
}: {
  openPage: (entity: RelatedEntity) => string | null;
  canCheckDeadlines?: boolean;
}) {
  const { data, error, pending, reload, run } = useData(loadNotifications);
  const panel = useRef<HTMLDivElement>(null);
  const unread = data?.filter((notification) => !notification.is_read) ?? [];

  useEffect(() => {
    const timer = setInterval(() => {
      if (!document.hidden) reload();
    }, REFRESH_MS);
    return () => clearInterval(timer);
  }, [reload]);

  const open = (notification: Notification) => {
    panel.current?.hidePopover();
    if (!notification.is_read) run(() => markAsRead(notification.id));
  };

  return (
    <>
      <button
        type="button"
        className="bell"
        popoverTarget="notifications"
        aria-label={
          unread.length > 0
            ? `Сповіщення (${unread.length})`
            : "Сповіщення"
        }
      >
        <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
          <path
            fill="currentColor"
            d="M12 2a6 6 0 0 0-6 6v4.6L4 16v2h16v-2l-2-3.4V8a6 6 0 0 0-6-6zm-2.6 18a2.7 2.7 0 0 0 5.2 0H9.4z"
          />
        </svg>
        {unread.length > 0 && (
          <span className="bell-count">
            {unread.length > 99 ? "99+" : unread.length}
          </span>
        )}
      </button>
      <div
        id="notifications"
        ref={panel}
        popover="auto"
        className="notifications"
        aria-label="Сповіщення"
        onToggle={(event) => {
          if (event.newState === "open") reload();
        }}
      >
        <div className="notifications-header">
          <h2>Сповіщення</h2>
          <div className="notifications-actions">
            {canCheckDeadlines && (
              <button
                type="button"
                className="secondary"
                disabled={pending}
                onClick={() =>
                  run(() => apiGet("/notifications/check-deadlines"))
                }
              >
                Перевірити терміни
              </button>
            )}
            {unread.length > 0 && (
              <button
                type="button"
                className="secondary"
                disabled={pending}
                onClick={() => run(() => apiPatch("/notifications/read-all"))}
              >
                Позначити всі прочитаними
              </button>
            )}
          </div>
        </div>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {data?.length === 0 && <p className="muted">Сповіщень немає.</p>}
        <ul>
          {data?.map((notification) => {
            const page = openPage(notification.related_entity);
            return (
              <li
                key={notification.id}
                className={notification.is_read ? "read" : "unread"}
              >
                <p>{notification.text}</p>
                <div className="notification-meta">
                  <span className="muted">
                    {formatDateTime(notification.created_at)}
                  </span>
                  <span className="notification-buttons">
                    {page && (
                      <a
                        href={`#${page}`}
                        className="link-button"
                        onClick={() => open(notification)}
                      >
                        Відкрити
                      </a>
                    )}
                    {!notification.is_read && (
                      <button
                        type="button"
                        className="secondary"
                        disabled={pending}
                        onClick={() => run(() => markAsRead(notification.id))}
                      >
                        Позначити прочитаним
                      </button>
                    )}
                  </span>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </>
  );
}
