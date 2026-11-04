"use client";

import { apiGet } from "../api";
import type { ProfilePage } from "../products";
import { useData } from "../shared/useData";

type Driver = {
  id: number;
  full_name: string;
  license_categories: string[];
  experience_years: number;
  license_expiry_date: string;
  medical_valid_until: string;
  medical_check_status: "VALID" | "EXPIRED" | "PENDING";
};

const MEDICAL_LABELS: Record<Driver["medical_check_status"], string> = {
  VALID: "Valid",
  EXPIRED: "Expired",
  PENDING: "Pending",
};

const loadDriver = () =>
  apiGet<Driver[]>("/drivers/").then((drivers) => drivers[0]);

export class DriverProfilePage implements ProfilePage {
  render() {
    return <DriverProfile />;
  }
}

function DriverProfile() {
  const { data: driver, error } = useData(loadDriver);

  return (
    <>
      <h1>Profile</h1>
      {error && <p className="error" role="alert">{error}</p>}
      {driver && (
        <dl className="details">
          <dt>Name</dt>
          <dd>{driver.full_name}</dd>
          <dt>Experience</dt>
          <dd>{driver.experience_years} years</dd>
          <dt>License categories</dt>
          <dd>{driver.license_categories.join(", ")}</dd>
          <dt>License valid until</dt>
          <dd>{driver.license_expiry_date}</dd>
          <dt>Medical check</dt>
          <dd>
            {MEDICAL_LABELS[driver.medical_check_status]}, until{" "}
            {driver.medical_valid_until}
          </dd>
        </dl>
      )}
    </>
  );
}
