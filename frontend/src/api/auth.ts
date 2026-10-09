import { client } from './client'
import type { TokenPair, User } from '@/types/api'

export interface FocusGoals {
  today: number
  week: number
  month: number
}

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
  update(payload: { timezone?: string; username?: string }) {
    return client.patch<User>('/auth/me', payload)
  },
  logout(refresh_token: string) {
    return client.post('/auth/logout', { refresh_token })
  },
  /** 头像：上传后返回新版本号；读取走 blob（img 标签带不了 Authorization 头） */
  uploadAvatar(file: File) {
    const fd = new FormData()
    fd.append('file', file)
    return client.post<{ avatar_v: number; avatar_ext: string }>('/auth/me/avatar', fd)
  },
  avatarBlob() {
    return client.get<Blob>('/auth/me/avatar', { responseType: 'blob' })
  },
  /** 专注目标（秒），三档互相独立 */
  goals() {
    return client.get<FocusGoals>('/auth/me/goals')
  },
  updateGoals(payload: Partial<FocusGoals>) {
    return client.patch<FocusGoals>('/auth/me/goals', payload)
  },
  focusTopics() {
    return client.get<string[]>('/auth/me/focus-topics')
  },
  rememberFocusTopic(label: string) {
    return client.post<string[]>('/auth/me/focus-topics', { label })
  },
  forgetFocusTopic(label: string) {
    return client.delete<string[]>('/auth/me/focus-topics', { data: { label } })
  },
}
