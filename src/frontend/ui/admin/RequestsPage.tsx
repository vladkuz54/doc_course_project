"use client";

import type { FormEvent } from "react";
import { apiGet, apiPost } from "../api";
import {
  describeRequest,
  formatDateTime,
  REQUEST_STATUS_LABELS,
  type Driver,
  type DriverRequest,
} from "../shared/fleet";
import { DateField, toIsoDate } from "../shared/DateField";
import { useData } from "../shared/useData";

const loadRequests = () =>
  Promise.all([
    apiGet<DriverRequest[]>("/driver-requests/"),
    apiGet<Driver[]>("/drivers/"),
  ]);

function pendingFirst(a: DriverRequest, b: DriverRequest) {
  const byStatus =
    Number(b.status === "PENDING") - Number(a.status === "PENDING");
  return byStatus || b.created_at.localeCompare(a.created_at);
}

export function RequestsPage() {
  const { data, error, notice, pending, run } = useData(loadRequests);
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
      "Request approved.",
    );
  };

  return (
    <>
      <h1>Requests</h1>
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
      {requests?.length === 0 && <p className="muted">No requests yet.</p>}
      {requests && requests.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Driver</th>
              <th>Request</th>
              <th>Submitted</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {requests.toSorted(pendingFirst).map((request) => (
              <tr key={request.id}>
                <td>
                  {drivers?.find((d) => d.id === request.driver_id)?.full_name}
                </td>
                <td>{describeRequest(request)}</td>
                <td>{formatDateTime(request.created_at)}</td>
                <td>{REQUEST_STATUS_LABELS[request.status]}</td>
                <td className="actions">
                  {request.status === "PENDING" && (
                    <>
                      {request.type === "MEDICAL_CHECK" ? (
                        <form
                          className="approve-medical"
                          onSubmit={(event) => approveMedical(event, request)}
                        >
                          <label>
                            Valid until
                            <DateField name="valid_until" required />
                          </label>
                          <button type="submit" disabled={pending}>
                            Approve
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
                              "Request approved.",
                            )
                          }
                        >
                          Approve
                        </button>
                      )}
                      <button
                        type="button"
                        className="secondary danger"
                        disabled={pending}
                        onClick={() =>
                          run(
                            () =>
                              apiPost(`/driver-requests/${request.id}/reject`),
                            "Request rejected.",
                          )
                        }
                      >
                        Reject
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
