import type { Role } from "./products";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "token";

export type CurrentUser = {
  user_id: number;
  username: string;
  role: Role;
};

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

let onUnauthorized: (() => void) | null = null;

export function setUnauthorizedHandler(handler: (() => void) | null) {
  onUnauthorized = handler;
}

export function hasToken(): boolean {
  return sessionStorage.getItem(TOKEN_KEY) !== null;
}

export function logout() {
  sessionStorage.removeItem(TOKEN_KEY);
}

type ValidationItem = { loc: (string | number)[]; msg: string };

function validationText({ loc, msg }: ValidationItem) {
  const field = String(loc[loc.length - 1]).replaceAll("_", " ");
  return `${field}: ${msg}`;
}

function detailText(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map(validationText).join("; ");
  return fallback;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = sessionStorage.getItem(TOKEN_KEY);
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_URL}${path}`, { ...init, headers }).catch(
    () => {
      throw new ApiError(0, "Can't reach the server. Try again in a moment.");
    },
  );
  if (!response.ok) {
    if (response.status === 401) {
      logout();
      if (token) onUnauthorized?.();
    }
    const body = await response.json().catch(() => null);
    throw new ApiError(
      response.status,
      detailText(body?.detail, response.statusText),
    );
  }
  return response.json();
}

function send<T>(method: string, path: string, body?: unknown): Promise<T> {
  if (body === undefined) return request<T>(path, { method });
  return request<T>(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function login(username: string, password: string): Promise<void> {
  logout();
  const { access_token } = await request<{ access_token: string }>(
    "/auth/token",
    { method: "POST", body: new URLSearchParams({ username, password }) },
  );
  sessionStorage.setItem(TOKEN_KEY, access_token);
}

export function getMe(): Promise<CurrentUser> {
  return request<CurrentUser>("/auth/me");
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path);
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return send<T>("POST", path, body);
}

export function apiPut<T>(path: string, body: unknown): Promise<T> {
  return send<T>("PUT", path, body);
}

export function apiPatch<T>(path: string, body?: unknown): Promise<T> {
  return send<T>("PATCH", path, body);
}

export function apiDelete<T>(path: string): Promise<T> {
  return send<T>("DELETE", path);
}
