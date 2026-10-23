import type {
  Admin,
  CityResponse,
  CountryResponse,
  LoginResponse,
  Profile,
  ProfilePage,
  ProfilePayload,
} from "../types";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/$/, "");
const CSRF_COOKIE = "admin_csrf";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly fieldErrors: Record<string, string> = {},
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function csrfToken(): string | null {
  const value = document.cookie
    .split("; ")
    .find((cookie) => cookie.startsWith(`${CSRF_COOKIE}=`))
    ?.split("=")[1];
  return value ? decodeURIComponent(value) : null;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  stateChanging = false,
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.body) headers.set("Content-Type", "application/json");
  if (stateChanging) {
    const token = csrfToken();
    if (token) headers.set("X-CSRF-Token", token);
  }
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers,
  });
  if (response.status === 204) return undefined as T;
  const body = (await response.json().catch(() => ({}))) as {
    detail?: string | Array<{ loc?: string[]; msg?: string }>;
  };
  if (!response.ok) {
    const detail = Array.isArray(body.detail) ? body.detail : [];
    const fieldErrors = Object.fromEntries(
      detail
        .filter((item) => item.loc?.length && item.msg)
        .map((item) => [item.loc?.at(-1) ?? "form", item.msg ?? "Invalid value"]),
    );
    const message =
      typeof body.detail === "string"
        ? body.detail
        : detail[0]?.msg ?? "The request could not be completed.";
    throw new ApiError(response.status, message, fieldErrors);
  }
  return body as T;
}

export const api = {
  login: (email: string, password: string) =>
    request<LoginResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }, true),
  logout: () => request<void>("/api/v1/auth/logout", { method: "POST" }, true),
  me: () => request<Admin>("/api/v1/auth/me"),
  countries: () => request<CountryResponse>("/api/v1/locations/countries"),
  cities: (country: string) =>
    request<CityResponse>(`/api/v1/locations/cities?country=${encodeURIComponent(country)}`),
  profiles: (query: string, page: number, pageSize = 20) =>
    request<ProfilePage>(
      `/api/v1/profiles?q=${encodeURIComponent(query)}&page=${page}&page_size=${pageSize}`,
    ),
  profile: (id: number) => request<Profile>(`/api/v1/profiles/${id}`),
  createProfile: (payload: ProfilePayload) =>
    request<Profile>("/api/v1/profiles", {
      method: "POST",
      body: JSON.stringify(payload),
    }, true),
};
