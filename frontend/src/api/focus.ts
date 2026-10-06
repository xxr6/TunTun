import { client } from './client'
import type { FocusSession, FocusSummary } from '@/types/api'

export const focusApi = {
  createSession(payload: {
    mode: string
    started_at: string
    ended_at: string
    duration_seconds: number
    completed: boolean
    deck_id?: string | null
    deck_name?: string
  }) {
    return client.post<FocusSession>('/focus/sessions', payload)
  },
  listSessions(limit = 10) {
    return client.get<FocusSession[]>('/focus/sessions', { params: { limit } })
  },
  summary() {
    return client.get<FocusSummary>('/focus/summary')
  },
}
