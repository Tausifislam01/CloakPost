// frontend/src/lib/api.ts
import { API_BASE } from "./env";

type Options = RequestInit & { json?: any };

export async function apiFetch(path: string, opts: Options = {}) {
  // Join API_BASE (which includes /api) with the relative path
  const base = API_BASE.endsWith("/") ? API_BASE.slice(0, -1) : API_BASE;
  const rel  = path.startsWith("/") ? path : `/${path}`;
  const url  = `${base}${rel}`;

  const headers = new Headers(opts.headers);

  // JSON helper
  if (opts.json !== undefined) {
    headers.set("Content-Type", "application/json");
    opts.body = JSON.stringify(opts.json);
  }

  // Add CSRF header for unsafe methods
  const method = (opts.method || "GET").toUpperCase();
  if (method !== "GET" && method !== "HEAD") {
    const { ensureCsrfToken } = await import("./csrf");
    const token = await ensureCsrfToken();
    headers.set("X-CSRFToken", token);
  }

  const res = await fetch(url, {
    ...opts,
    headers,
    credentials: "include", // send cookies across origins
    mode: "cors",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Request failed ${res.status}: ${text || res.statusText}`);
  }
  return res;
}