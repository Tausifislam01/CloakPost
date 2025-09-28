// frontend/src/lib/api.ts
import { API_BASE } from "./env";
import type { Post } from "../types"; // ✅ use your canonical Post (has ciphertext, etc.)

/** Extra options we support on top of RequestInit */
export type Options = RequestInit & { json?: any };

/** --- Small utilities --- */
function joinUrl(path: string) {
  const base = API_BASE.endsWith("/") ? API_BASE.slice(0, -1) : API_BASE;
  const rel = path.startsWith("/") ? path : `/${path}`;
  return `${base}${rel}`;
}

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

/** --- Low-level helpers (return Response) --- */
export async function apiFetch(path: string, opts: Options = {}) {
  const { url, init } = await prepare(path, opts);
  const res = await fetch(url, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Request failed ${res.status}: ${text || res.statusText}`);
  }
  return res;
}
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

/** --- App-level types --- */
export type { Post }; // re-export for convenience
export type Message = {
  id: number;
  from: string;
  to: string;
  content: string;
  created_at?: string;
  [k: string]: any;
};

/** --- High-level helpers that RETURN PARSED JSON --- */
/** Auth */
async function login(username: string, password: string): Promise<any> {
  const r = await post("/users/login/", { username, password });
  return r.json().catch(() => ({}));
}
async function register(username: string, password: string, email?: string): Promise<any> {
  const body = email ? { username, password, email } : { username, password };
  const r = await post("/users/register/", body);
  return r.json().catch(() => ({}));
}
async function logout(): Promise<any> {
  const r = await post("/users/logout/", {});
  return r.json().catch(() => ({}));
}

/** Posts */
async function listPosts(): Promise<Post[]> {
  const r = await get("/posts/");
  // Backend returns array of posts that match your Post type (with ciphertext, etc.)
  return r.json() as Promise<Post[]>;
}
async function createPost(content: string): Promise<Post> {
  const r = await post("/posts/", { content });
  return r.json() as Promise<Post>;
}

/** Users / Friends */
async function searchUsers(q: string): Promise<string[]> {
  const qs = new URLSearchParams({ q }).toString();
  const r = await get(`/users/search/?${qs}`);
  return r.json();
}
async function sendFriendRequest(username: string): Promise<any> {
  const r = await post("/users/friends/requests/", { username });
  return r.json().catch(() => ({}));
}
async function listFriendRequests(): Promise<any[]> {
  const r = await get("/users/friends/requests/");
  return r.json();
}
async function acceptFriendRequest(requestId: number): Promise<any> {
  const r = await post(`/users/friends/requests/${requestId}/accept/`, {});
  return r.json().catch(() => ({}));
}

/** Messages */
async function inbox(): Promise<Message[]> {
  const r = await get("/messages/");
  return r.json();
}
async function sendMessage(toUsername: string, content: string): Promise<any> {
  const r = await post("/messages/send/", { to: toUsername, content });
  return r.json().catch(() => ({}));
}

/** 🔙 Facade expected by your code/tests */
export const api = {
  // low-level
  fetch: apiFetch,
  get,
  post,
  put,
  patch,
  delete: del,
  // high-level returning parsed JSON
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