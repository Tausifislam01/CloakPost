export type User = { id: number; username: string }
export type Post = { id: number; author: string; ciphertext: string; created_at: string }
export type FriendRequest = { id: number; from_user: string; to_user: string; status: 'pending' | 'accepted' | 'rejected' }
export type Message = { id: number; from_user: string; to_user: string; ciphertext: string; created_at: string }
