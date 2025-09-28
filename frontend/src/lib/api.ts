// frontend/src/lib/api.ts
import { API_BASE } from "./env";

/** Extra options we support on top of RequestInit */
export type Options = RequestInit & { json?: any };

/** Join API_BASE (which already includes /api) with a relative path */
function joinUrl(path: string) {
  const base = API_BASE.endsWith("/") ? API_BASE.slice(0, -1) : API_BASE;
  const rel = path.startsWith("/") ? path : `/${path}`;
  return `${base}${rel}`;
}

/** Prepare init: JSON body + CSRF header for unsafe methods */
async function prepare(path: string, opts: Options = {}) {
  const headers = new Headers(opts.headers);

  // JSON helper
  if (opts.json !== undefined) {
    headers.set("Content-Type", "application/json");
    opts.body = JSON.stringify(opts.json);
  }

  // CSRF for non-GET/HEAD
  const method = (opts.method || "GET").toUpperCase();
  if (method !== "GET" && method !== "HEAD") {
    const { ensureCsrfToken } = await import("./csrf"); // lazy import
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

/** Primary low-level helper */
export async function apiFetch(path: string, opts: Options = {}) {
  const { url, init } = await prepare(path, opts);
  const res = await fetch(url, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Request failed ${res.status}: ${text || res.statusText}`);
  }
  return res;
}

/** Convenience low-level helpers */
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

/* =========================
   High-level, app-specific API
   Paths assume API_BASE ends with /api
   ========================= */

/** Auth */
async function login(username: string, password: string) {
  return post("/users/login/", { username, password });
}
async function register(username: string, password: string, email: string) {
  return post("/users/register/", { username, password, email });
}
async function logout() {
  return post("/users/logout/", {});
}

/** Posts */
async function listPosts() {
  return get("/posts/");
}
async function createPost(content: string) {
  // adjust body shape to your backend contract if different
  return post("/posts/", { content });
}

/** Users / Friends */
async function searchUsers(q: string) {
  const qs = new URLSearchParams({ q }).toString();
  return get(`/users/search/?${qs}`);
}
async function sendFriendRequest(username: string) {
  return post("/users/friends/requests/", { username });
}
async function listFriendRequests() {
  return get("/users/friends/requests/");
}
async function acceptFriendRequest(requestId: number) {
  return post(`/users/friends/requests/${requestId}/accept/`, {});
}

/** Messages */
async function inbox() {
  return get("/messages/");
}
async function sendMessage(toUsername: string, content: string) {
  return post("/messages/send/", { to: toUsername, content });
}

/**
 * 🔙 Backwards-compatible facade:
 * Your code/tests import `{ api }` and expect both low-level
 * methods (get/post/...) and high-level methods (login, register, etc).
 */
export const api = {
  // low-level
  fetch: apiFetch,
  get,
  post,
  put,
  patch,
  delete: del,
  // high-level
  login,
  register,
  logout,
  listPosts,
  createPost,
  searchUsers,
  sendFriendRequest,
  acceptFriendRequest,
  listFriendRequests,
  inbox,
  sendMessage,
};
