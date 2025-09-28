import { csrfHeader } from './csrf'
import { API_BASE } from './env'
import type { Post } from '../types'

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...csrfHeader(), ...(opts.headers || {}) },
    ...opts,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${text}`)
  }
  const ct = res.headers.get('content-type') || ''
  return ct.includes('application/json') ? await res.json() : (await res.text() as unknown as T)
}

export const api = {
  // ---- Auth ----
  login: (username: string, password: string) =>
    request<any>('/api/users/login/', { method: 'POST', body: JSON.stringify({ username, password }) }),

  register: (username: string, password: string) =>
    request<any>('/api/users/register/', { method: 'POST', body: JSON.stringify({ username, password }) }),

  logout: () =>
    request<any>('/api/users/logout/', { method: 'POST' }),

  // ---- Posts ----
  listPosts: () =>
    request<Post[]>('/api/posts/'),

  createPost: (plaintext: string) =>
    request<any>('/api/posts/', { method: 'POST', body: JSON.stringify({ plaintext }) }),

  // ---- Friends ----
  searchUsers: (q: string) =>
    request<string[]>(`/api/users/search/?q=${encodeURIComponent(q)}`),

  sendFriendRequest: (username: string) =>
    request<any>('/api/users/friends/requests/', { method: 'POST', body: JSON.stringify({ username }) }),

  listFriendRequests: () =>
    request<Array<{ id: number; from_user: string; to_user: string; status: string }>>('/api/users/friends/requests/'),

  acceptFriendRequest: (id: number) =>
    request<any>(`/api/users/friends/requests/${id}/accept/`, { method: 'POST' }),

  // ---- Messages ----
  inbox: () =>
    request<Array<{ username: string; last_message_snippet: string }>>('/api/messages/'),

  sendMessage: (to: string, plaintext: string) =>
    request<any>('/api/messages/send/', { method: 'POST', body: JSON.stringify({ to, plaintext }) }),
}
