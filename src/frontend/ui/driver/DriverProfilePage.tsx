"use client";

import { apiGet } from "../api";
import type { ProfilePage } from "../products";
import { formatDate, MEDICAL_LABELS, type Driver } from "../shared/fleet";
import { Messages } from "../shared/Messages";
import { useData } from "../shared/useData";

const loadDriver = () =>
  apiGet<Driver[]>("/drivers/").then((drivers) => drivers[0]);

export class DriverProfilePage implements ProfilePage {
  render() {
    return <DriverProfile />;
  }
}

function DriverProfile() {
  const { data: driver, error, clearMessages } = useData(loadDriver);

  return (
    <>
      <h1>Профіль</h1>
      <Messages error={error} onClose={clearMessages} />
      {driver && (
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
      )}
    </>
  );
}
