import { client } from './client'
import type { TokenPair, User } from '@/types/api'

export const authApi = {
  register(payload: { email: string; username: string; password: string }) {
    return client.post<TokenPair>('/auth/register', payload)
  },
  login(payload: { account: string; password: string }) {
    return client.post<TokenPair>('/auth/login', payload)
  },
  me() {
    return client.get<User>('/auth/me')
  },
  update(payload: { timezone?: string }) {
    return client.patch<User>('/auth/me', payload)
  },
  logout(refresh_token: string) {
    return client.post('/auth/logout', { refresh_token })
  },
}
