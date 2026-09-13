import { apiUrl } from "./utils";

function csrfToken() {
  if (typeof document === "undefined") return "";
  const match = document.cookie.match(/(?:^|; )ac_csrf=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const csrf = csrfToken();
  if (csrf) headers.set("X-CSRF-Token", csrf);
  const response = await fetchWithTimeout(`${apiUrl()}${path}`, { ...init, headers, credentials: "include" });
  if (response.status === 401 && typeof window !== "undefined" && !path.startsWith("/api/auth")) {
    const refreshed = await fetchWithTimeout(`${apiUrl()}/api/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(csrf ? { "X-CSRF-Token": csrf } : {}) },
      credentials: "include",
      body: JSON.stringify({}),
    });
    if (refreshed.ok) {
      const retry = await fetchWithTimeout(`${apiUrl()}${path}`, { ...init, headers, credentials: "include" });
      if (!retry.ok) throw await errorFrom(retry);
      if (retry.status === 204) return {} as T;
      return parseBody<T>(retry);
    }
    if (typeof window !== "undefined" && !path.startsWith("/api/auth")) {
      /* session is gone; caller handles empty state */
    }
  }
  if (!response.ok) throw await errorFrom(response);
  if (response.status === 204) return {} as T;
  return parseBody<T>(response);
}

async function fetchWithTimeout(url: string, init: RequestInit = {}): Promise<Response> {
  const timeoutMs = init.body instanceof FormData ? 180_000 : 60_000;
  if (init.signal) {
    return fetch(url, init);
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("Request timed out. Please try again.");
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

async function parseBody<T>(response: Response): Promise<T> {
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
  const me = await fetch(`${apiUrl()}/api/auth/me`, { credentials: "include" });
  if (me.ok) return;
  await api("/api/auth/guest", { method: "POST" });
}

export async function signOut() {
  try {
    await api("/api/auth/logout", { method: "POST", body: JSON.stringify({}) });
  } catch {
    /* still leave the app */
  }
}

export async function track(event_name: string, path?: string) {
  try {
    await fetch(`${apiUrl()}/api/public/analytics`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ event_name, path, properties: {} }),
    });
  } catch {
    /* privacy-friendly: analytics must never break the product */
  }
}
