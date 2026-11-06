"use client";

import type { FormEvent } from "react";
import { apiGet, apiPost } from "../api";
import type { ProfilePage } from "../products";
import {
  describeRequest,
  formatDate,
  formatDateTime,
  LICENSE_CATEGORIES,
  MEDICAL_LABELS,
  REQUEST_SECTIONS,
  type Driver,
  type DriverRequest,
} from "../shared/fleet";
import { DateField, toIsoDate } from "../shared/DateField";
import { Messages } from "../shared/Messages";
import { StatusSections } from "../shared/StatusSections";
import { useData } from "../shared/useData";

const loadProfile = () =>
  Promise.all([
    apiGet<Driver[]>("/drivers/").then((drivers) => drivers[0]),
    apiGet<DriverRequest[]>("/driver-requests/"),
  ]);

function newestFirst(a: DriverRequest, b: DriverRequest) {
  return b.created_at.localeCompare(a.created_at);
}

export class DriverProfilePage implements ProfilePage {
  render() {
    return <DriverProfile page={this} />;
  }

  requestMedicalCheck(driverId: number) {
    return apiPost("/driver-requests/", {
      driver_id: driverId,
      type: "MEDICAL_CHECK",
    });
  }

  submitLicenseUpdate(
    driverId: number,
    category: string,
    expiryDate?: string | null,
  ) {
    return apiPost("/driver-requests/", {
      driver_id: driverId,
      type: "LICENSE_UPDATE",
      new_license_category: category,
      new_license_expiry_date: expiryDate ?? null,
    });
  }
}

function DriverProfile({ page }: { page: DriverProfilePage }) {
  const { data, error, notice, pending, run, clearMessages } =
    useData(loadProfile);
  const [driver, requests] = data ?? [];

  const submitLicense = (event: FormEvent<HTMLFormElement>, id: number) => {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    run(
      () =>
        page.submitLicenseUpdate(
          id,
          String(fields.get("category")),
          toIsoDate(String(fields.get("expiry"))) || null,
        ),
      "License update requested.",
    ).then((saved) => {
      if (saved) form.reset();
    });
  };

  return (
    <>
      <h1>Profile</h1>
      <Messages error={error} notice={notice} onClose={clearMessages} />
      {driver && (
        <>
          <dl className="details">
            <dt>Name</dt>
            <dd>{driver.full_name}</dd>
            <dt>Experience</dt>
            <dd>{driver.experience_years} years</dd>
            <dt>License categories</dt>
            <dd>{driver.license_categories.join(", ")}</dd>
            <dt>License valid until</dt>
            <dd>{formatDate(driver.license_expiry_date)}</dd>
            <dt>Medical check</dt>
            <dd>
              {MEDICAL_LABELS[driver.medical_check_status]}, until{" "}
              {formatDate(driver.medical_valid_until)}
            </dd>
          </dl>

          <button
            type="button"
            disabled={pending}
            onClick={() =>
              run(
                () => page.requestMedicalCheck(driver.id),
                "Medical check requested.",
              )
            }
          >
            Request medical check
          </button>

          <form
            className="panel"
            onSubmit={(event) => submitLicense(event, driver.id)}
          >
            <label>
              New license category
              <select name="category" required>
                {LICENSE_CATEGORIES.filter(
                  (category) => !driver.license_categories.includes(category),
                ).map((category) => (
                  <option key={category}>{category}</option>
                ))}
              </select>
            </label>
            <label>
              New expiry date (optional)
              <DateField name="expiry" />
            </label>
            <div className="form-actions">
              <button type="submit" disabled={pending}>
                Request license update
              </button>
            </div>
          </form>

          <h2 className="section-title">My requests</h2>
          {requests?.length === 0 && <p className="muted">No requests yet.</p>}
          <StatusSections
            items={requests?.toSorted(newestFirst)}
            statusOf={(request) => request.status}
            sections={REQUEST_SECTIONS}
          >
            {(rows) => (
              <table>
                <thead>
                  <tr>
                    <th>Request</th>
                    <th>Submitted</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((request) => (
                    <tr key={request.id}>
                      <td>{describeRequest(request)}</td>
                      <td>{formatDateTime(request.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </StatusSections>
        </>
      )}
    </>
  );
}
