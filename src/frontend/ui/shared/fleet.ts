import { apiGet } from "../api";

export type Driver = {
  id: number;
  user_id: number;
  full_name: string;
  license_categories: string[];
  experience_years: number;
  license_expiry_date: string;
  medical_check_date: string;
  medical_valid_until: string;
  medical_check_status: "VALID" | "EXPIRED" | "PENDING";
  employment_status: "ACTIVE" | "DISMISSED";
};

export type RouteStatus = "PLANNED" | "IN_PROGRESS" | "COMPLETED" | "CANCELLED";

export type Route = {
  id: number;
  driver_id: number | null;
  vehicle_id: number | null;
  distance: number;
  departure_at: string;
  planned_return_at: string;
  started_at: string | null;
  completed_at: string | null;
  status: RouteStatus;
};

export type RouteStop = {
  id: number;
  route_id: number;
  order_no: number;
  address: string;
  arrived_at: string | null;
};

export type TechnicalState = "GOOD" | "NEEDS_SERVICE" | "IN_REPAIR" | "FAULTY";

export type Vehicle = {
  id: number;
  make: string;
  year: number;
  vin: string;
  required_license_category: string;
  technical_state: TechnicalState;
  status: "ACTIVE" | "DECOMMISSIONED";
};

export type DriverRequest = {
  id: number;
  driver_id: number;
  type: "LICENSE_UPDATE" | "MEDICAL_CHECK";
  status: "PENDING" | "APPROVED" | "REJECTED";
  new_license_category: string | null;
  new_license_expiry_date: string | null;
  medical_check_date: string | null;
  created_at: string;
};

export const LICENSE_CATEGORIES = [
  "A1",
  "A",
  "B1",
  "B",
  "BE",
  "C1",
  "C1E",
  "C",
  "CE",
  "D1",
  "D1E",
  "D",
  "DE",
  "T",
];

export const MEDICAL_LABELS: Record<Driver["medical_check_status"], string> = {
  VALID: "Дійсний",
  EXPIRED: "Прострочений",
  PENDING: "Очікує підтвердження",
};

export const TECHNICAL_STATE_LABELS: Record<TechnicalState, string> = {
  GOOD: "Справний",
  NEEDS_SERVICE: "Потребує ТО",
  IN_REPAIR: "На ремонті",
  FAULTY: "Несправний",
};

export const STATUS_LABELS: Record<RouteStatus, string> = {
  PLANNED: "Заплановано",
  IN_PROGRESS: "У дорозі",
  COMPLETED: "Завершено",
  CANCELLED: "Скасовано",
};

export const REQUEST_STATUS_LABELS: Record<DriverRequest["status"], string> = {
  PENDING: "Очікують розгляду",
  APPROVED: "Схвалено",
  REJECTED: "Відхилено",
};

export const REQUEST_SECTIONS = (
  ["PENDING", "APPROVED", "REJECTED"] as const
).map((status) => ({ status, label: REQUEST_STATUS_LABELS[status] }));

export function describeRequest(request: DriverRequest) {
  if (request.type === "MEDICAL_CHECK") {
    return `Медогляд пройдено ${formatDate(request.medical_check_date ?? "")}`;
  }
  const category = request.new_license_category
    ? `, категорія ${request.new_license_category}`
    : "";
  return `Посвідчення до ${formatDate(request.new_license_expiry_date ?? "")}${category}`;
}

const STATUS_ORDER: RouteStatus[] = [
  "IN_PROGRESS",
  "PLANNED",
  "COMPLETED",
  "CANCELLED",
];

export const ROUTE_SECTIONS = STATUS_ORDER.map((status) => ({
  status,
  label: STATUS_LABELS[status],
}));

export function compareRoutes(a: Route, b: Route) {
  const byStatus =
    STATUS_ORDER.indexOf(a.status) - STATUS_ORDER.indexOf(b.status);
  if (byStatus !== 0) return byStatus;
  const byDeparture = a.departure_at.localeCompare(b.departure_at);
  return a.status === "IN_PROGRESS" || a.status === "PLANNED"
    ? byDeparture
    : -byDeparture;
}

export function formatDate(value: string) {
  const [year, month, day] = value.split("-");
  return `${day}/${month}/${year}`;
}

export function formatDateTime(value: string) {
  return new Date(value).toLocaleString("en-GB", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

export function stopsOf(
  stops: RouteStop[] | null | undefined,
  routeId: number,
) {
  return (stops ?? [])
    .filter((stop) => stop.route_id === routeId)
    .sort((a, b) => a.order_no - b.order_no);
}

export function loadRoutesAndStops() {
  return Promise.all([
    apiGet<Route[]>("/routes/"),
    apiGet<RouteStop[]>("/route-stops/"),
  ]);
}
