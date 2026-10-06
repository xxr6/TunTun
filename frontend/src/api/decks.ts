import { client } from './client'
import type { Deck } from '@/types/api'

export const decksApi = {
  list() {
    return client.get<Deck[]>('/decks')
  },
  create(payload: { name: string; parent_id?: string | null; description?: string }) {
    return client.post<Deck>('/decks', payload)
  },
  update(id: string, payload: Partial<Pick<Deck, 'name' | 'description'>>) {
    return client.patch<Deck>(`/decks/${id}`, payload)
  },
  remove(id: string) {
    return client.delete(`/decks/${id}`)
  },
}
