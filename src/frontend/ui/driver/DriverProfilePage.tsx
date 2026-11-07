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
import { DateField, nowForField, toIsoDate } from "../shared/DateField";
import { Messages } from "../shared/Messages";
import { StatusSections } from "../shared/StatusSections";
import { useData } from "../shared/useData";

const loadProfile = () =>
  Promise.all([
    apiGet<Driver[]>("/drivers/").then((drivers) => drivers[0]),
    apiGet<DriverRequest[]>("/driver-requests/"),
  ]);

const today = () => nowForField().slice(0, 10);

function dayAfter(isoDate: string) {
  const next = new Date(`${isoDate}T00:00:00Z`);
  next.setUTCDate(next.getUTCDate() + 1);
  return next.toISOString().slice(0, 10);
}

function newestFirst(a: DriverRequest, b: DriverRequest) {
  return b.created_at.localeCompare(a.created_at);
}

export class DriverProfilePage implements ProfilePage {
  render() {
    return <DriverProfile page={this} />;
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

function DriverProfile({ page }: { page: DriverProfilePage }) {
  const { data, error, notice, pending, run, clearMessages } =
    useData(loadProfile);
  const [driver, requests] = data ?? [];

  const submitMedical = (event: FormEvent<HTMLFormElement>, id: number) => {
    event.preventDefault();
    const form = event.currentTarget;
    const checkDate = toIsoDate(String(new FormData(form).get("check_date")));
    run(
      () => page.requestMedicalCheck(id, checkDate),
      "Повідомлення про медогляд надіслано.",
    ).then((saved) => {
      if (saved) form.reset();
    });
  };

  const submitLicense = (event: FormEvent<HTMLFormElement>, id: number) => {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    run(
      () =>
        page.submitLicenseUpdate(
          id,
          String(fields.get("category")) || null,
          toIsoDate(String(fields.get("expiry"))),
        ),
      "Запит на оновлення посвідчення надіслано.",
    ).then((saved) => {
      if (saved) form.reset();
    });
  };

  return (
    <>
      <h1>Профіль</h1>
      <Messages error={error} notice={notice} onClose={clearMessages} />
      {driver && (
        <>
          <dl className="details">
            <dt>ПІБ</dt>
            <dd>{driver.full_name}</dd>
            <dt>Стаж</dt>
            <dd>{driver.experience_years} р.</dd>
            <dt>Категорії посвідчення</dt>
            <dd>{driver.license_categories.join(", ")}</dd>
            <dt>Посвідчення дійсне до</dt>
            <dd>{formatDate(driver.license_expiry_date)}</dd>
            <dt>Медогляд</dt>
            <dd>
              {MEDICAL_LABELS[driver.medical_check_status]}, до{" "}
              {formatDate(driver.medical_valid_until)}
            </dd>
          </dl>

          <form
            className="panel"
            onSubmit={(event) => submitMedical(event, driver.id)}
          >
            <label>
              Дата, коли ви пройшли медогляд
              <DateField
                name="check_date"
                max={today()}
                required
              />
            </label>
            <div className="form-actions">
              <button type="submit" disabled={pending}>
                Повідомити про медогляд
              </button>
            </div>
          </form>

          <form
            className="panel"
            onSubmit={(event) => submitLicense(event, driver.id)}
          >
            <label>
              Нове посвідчення дійсне до
              <DateField
                name="expiry"
                min={dayAfter(
                  [today(), driver.license_expiry_date].toSorted().at(-1)!,
                )}
                required
              />
            </label>
            <label>
              Нова категорія (необов’язково)
              <select name="category">
                <option value="">Без нової категорії</option>
                {LICENSE_CATEGORIES.filter(
                  (category) => !driver.license_categories.includes(category),
                ).map((category) => (
                  <option key={category}>{category}</option>
                ))}
              </select>
            </label>
            <div className="form-actions">
              <button type="submit" disabled={pending}>
                Подати запит на оновлення посвідчення
              </button>
            </div>
          </form>

          <h2 className="section-title">Мої запити</h2>
          {requests?.length === 0 && <p className="muted">Запитів ще немає.</p>}
          <StatusSections
            items={requests?.toSorted(newestFirst)}
            statusOf={(request) => request.status}
            sections={REQUEST_SECTIONS}
          >
            {(rows) => (
              <table>
                <thead>
                  <tr>
                    <th>Запит</th>
                    <th>Подано</th>
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
