// frontend/src/lib/api.ts
import { API_BASE } from "./env";

/** Extra options we support on top of RequestInit */
type Options = RequestInit & { json?: any };

/** Join API_BASE (which already includes /api) with a relative path */
function joinUrl(path: string) {
  const base = API_BASE.endsWith("/") ? API_BASE.slice(0, -1) : API_BASE;
  const rel  = path.startsWith("/") ? path : `/${path}`;
  return `${base}${rel}`;
}

/** Ensure we attach JSON body & CSRF header on unsafe methods */
async function withPreparedInit(path: string, opts: Options = {}) {
  const headers = new Headers(opts.headers);

  // JSON helper
  if (opts.json !== undefined) {
    headers.set("Content-Type", "application/json");
    opts.body = JSON.stringify(opts.json);
  }

  // CSRF for non-GET/HEAD
  const method = (opts.method || "GET").toUpperCase();
  if (method !== "GET" && method !== "HEAD") {
    // Lazy import to avoid circular deps at build
    const { ensureCsrfToken } = await import("./csrf");
    const token = await ensureCsrfToken();
    headers.set("X-CSRFToken", token);
  }

  const url = joinUrl(path);
  const init: RequestInit = {
    ...opts,
    headers,
    credentials: "include",
    mode: "cors",
  };

  return { url, init };
}

/** Primary helper used everywhere */
export async function apiFetch(path: string, opts: Options = {}) {
  const { url, init } = await withPreparedInit(path, opts);
  const res = await fetch(url, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Request failed ${res.status}: ${text || res.statusText}`);
  }
  return res;
}

/** Convenience helpers */
export async function get(path: string, opts: Options = {}) {
  return apiFetch(path, { ...opts, method: "GET" });
}
export async function post(path: string, json?: any, opts: Options = {}) {
  return apiFetch(path, { ...opts, method: "POST", json });
}
export async function put(path: string, json?: any, opts: Options = {}) {
  return apiFetch(path, { ...opts, method: "PUT", json });
}
export async function patch(path: string, json?: any, opts: Options = {}) {
  return apiFetch(path, { ...opts, method: "PATCH", json });
}
export async function del(path: string, opts: Options = {}) {
  return apiFetch(path, { ...opts, method: "DELETE" });
}

/**
 * 🔙 Backwards-compatible named export expected by your code/tests:
 * Many files do: `import { api } from "../lib/api"`
 * Provide a small facade that mirrors common methods.
 */
export const api = {
  fetch: apiFetch,
  get,
  post,
  put,
  patch,
  delete: del,
};

export type { Options };
