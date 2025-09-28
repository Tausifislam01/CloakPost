// frontend/src/lib/csrf.ts
import { apiFetch } from "./api";

let CSRF_TOKEN: string | null = null;

/**
 * Fetch a CSRF token from /api/csrf/ and cache it in memory.
 * No cookie-reading needed in the SPA.
 */
export async function ensureCsrfToken(): Promise<string> {
  if (CSRF_TOKEN) return CSRF_TOKEN;
  const res = await apiFetch("/csrf/", { method: "GET" });
  const data = await res.json();
  CSRF_TOKEN = data.csrfToken;
  return CSRF_TOKEN!;
}