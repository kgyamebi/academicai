import { apiUrl } from "./utils";

const TOKEN_KEY = "ac_access";
const REFRESH_KEY = "ac_refresh";

export function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${apiUrl()}${path}`, { ...init, headers });
  if (response.status === 401 && typeof window !== "undefined" && !path.startsWith("/api/auth")) {
    const refresh = localStorage.getItem(REFRESH_KEY);
    if (refresh) {
      const refreshed = await fetch(`${apiUrl()}/api/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (refreshed.ok) {
        const data = await refreshed.json();
        setTokens(data.access_token, data.refresh_token);
        headers.set("Authorization", `Bearer ${data.access_token}`);
        const retry = await fetch(`${apiUrl()}${path}`, { ...init, headers });
        if (!retry.ok) throw await errorFrom(retry);
        if (retry.status === 204) return {} as T;
        return retry.json();
      }
    }
    clearTokens();
  }
  if (!response.ok) throw await errorFrom(response);
  if (response.status === 204) return {} as T;
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/pdf")) {
    return (await response.blob()) as T;
  }
  return response.json();
}

async function errorFrom(response: Response) {
  try {
    const data = await response.json();
    return new Error(data.error || "Request failed");
  } catch {
    return new Error("Request failed");
  }
}

export async function ensureGuest() {
  if (getToken()) return;
  const data = await api<{ access_token: string; refresh_token: string }>("/api/auth/guest", { method: "POST" });
  setTokens(data.access_token, data.refresh_token);
}

export async function track(event_name: string, path?: string) {
  try {
    await fetch(`${apiUrl()}/api/public/analytics`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event_name, path, properties: {} }),
    });
  } catch {
    /* privacy-friendly: analytics must never break the product */
  }
}
