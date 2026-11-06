"use client";

import type { FormEvent } from "react";
import { apiGet, apiPost } from "../api";
import {
  describeRequest,
  formatDateTime,
  REQUEST_SECTIONS,
  type Driver,
  type DriverRequest,
} from "../shared/fleet";
import { DateField, toIsoDate } from "../shared/DateField";
import { Messages } from "../shared/Messages";
import { StatusSections } from "../shared/StatusSections";
import { useData } from "../shared/useData";

const loadRequests = () =>
  Promise.all([
    apiGet<DriverRequest[]>("/driver-requests/"),
    apiGet<Driver[]>("/drivers/"),
  ]);

function newestFirst(a: DriverRequest, b: DriverRequest) {
  return b.created_at.localeCompare(a.created_at);
}

export function RequestsPage() {
  const { data, error, notice, pending, run, clearMessages } =
    useData(loadRequests);
  const [requests, drivers] = data ?? [];

  const approveMedical = (
    event: FormEvent<HTMLFormElement>,
    request: DriverRequest,
  ) => {
    event.preventDefault();
    const validUntil = toIsoDate(
      String(new FormData(event.currentTarget).get("valid_until")),
    );
    run(
      () =>
        apiPost(`/driver-requests/${request.id}/approve-medical`, {
          valid_until: validUntil,
        }),
      "Запит схвалено.",
    );
  };

  return (
    <>
      <h1>Запити</h1>
      <Messages error={error} notice={notice} onClose={clearMessages} />
      {requests?.length === 0 && <p className="muted">Запитів ще немає.</p>}
      {requests && requests.length > 0 && (
        <StatusSections
          items={requests.toSorted(newestFirst)}
          statusOf={(request) => request.status}
          sections={REQUEST_SECTIONS}
        >
          {(rows) => (
            <table>
              <thead>
                <tr>
                  <th>Водій</th>
                  <th>Запит</th>
                  <th>Подано</th>
                  {rows[0].status === "PENDING" && <th>Дії</th>}
                </tr>
              </thead>
              <tbody>
                {rows.map((request) => (
                  <tr key={request.id}>
                    <td>
                      {
                        drivers?.find((d) => d.id === request.driver_id)
                          ?.full_name
                      }
                    </td>
                    <td>{describeRequest(request)}</td>
                    <td>{formatDateTime(request.created_at)}</td>
                    {request.status === "PENDING" && (
                      <td className="actions">
                        {request.status === "PENDING" && (
                          <>
                            {request.type === "MEDICAL_CHECK" ? (
                              <form
                                className="approve-medical"
                                onSubmit={(event) =>
                                  approveMedical(event, request)
                                }
                              >
                                <label>
                                  Дійсний до
                                  <DateField name="valid_until" required />
                                </label>
                                <button type="submit" disabled={pending}>
                                  Схвалити
                                </button>
                              </form>
                            ) : (
                              <button
                                type="button"
                                disabled={pending}
                                onClick={() =>
                                  run(
                                    () =>
                                      apiPost(
                                        `/driver-requests/${request.id}/approve-license`,
                                      ),
                                    "Запит схвалено.",
                                  )
                                }
                              >
                                Схвалити
                              </button>
                            )}
                            <button
                              type="button"
                              className="secondary danger"
                              disabled={pending}
                              onClick={() =>
                                run(
                                  () =>
                                    apiPost(
                                      `/driver-requests/${request.id}/reject`,
                                    ),
                                  "Запит відхилено.",
                                )
                              }
                            >
                              Відхилити
                            </button>
                          </>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </StatusSections>
      )}
    </>
  );
}
