import { client } from './client'
import type { Card, CardList } from '@/types/api'

export const cardsApi = {
  list(params: { deck_id?: string; source_file_id?: string; tag?: string; state?: string; q?: string; limit?: number; offset?: number } = {}) {
    return client.get<CardList>('/cards', { params })
  },
  create(payload: {
    deck_id?: string | null
    card_type?: string
    front: string
    back?: string
    hint?: string | null
    source_file_id?: string | null
    source_locator?: Record<string, unknown> | null
    tags?: string[]
  }) {
    return client.post<Card>('/cards', payload)
  },
  update(id: string, payload: Partial<Card>) {
    return client.patch<Card>(`/cards/${id}`, payload)
  },
  remove(id: string) {
    return client.delete(`/cards/${id}`)
  },
}
