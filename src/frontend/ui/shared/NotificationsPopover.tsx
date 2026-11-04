"use client";

import { useRef } from "react";
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

  const open = (notification: Notification) => {
    panel.current?.hidePopover();
    if (!notification.is_read) run(() => markAsRead(notification.id));
  };

  return (
    <>
      <button type="button" popoverTarget="notifications">
        Notifications{unread.length > 0 && ` (${unread.length})`}
      </button>
      <div
        id="notifications"
        ref={panel}
        popover="auto"
        className="notifications"
        aria-label="Notifications"
        onToggle={(event) => {
          if (event.newState === "open") reload();
        }}
      >
        <div className="notifications-header">
          <h2>Notifications</h2>
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
                Check deadlines
              </button>
            )}
            {unread.length > 0 && (
              <button
                type="button"
                className="secondary"
                disabled={pending}
                onClick={() => run(() => apiPatch("/notifications/read-all"))}
              >
                Mark all as read
              </button>
            )}
          </div>
        </div>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {data?.length === 0 && <p className="muted">No notifications.</p>}
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
                        Open
                      </a>
                    )}
                    {!notification.is_read && (
                      <button
                        type="button"
                        className="secondary"
                        disabled={pending}
                        onClick={() => run(() => markAsRead(notification.id))}
                      >
                        Mark as read
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
