import { client } from './client'
import type { ForecastDay, ReviewAnswerOut, ReviewQueue } from '@/types/api'

export const reviewApi = {
  queue(deckId?: string, limit = 20) {
    return client.get<ReviewQueue>('/review/queue', { params: { deck_id: deckId, limit } })
  },
  answer(payload: { card_id: string; rating: number; duration_ms?: number }) {
    return client.post<ReviewAnswerOut>('/review/answer', payload)
  },
  undo(cardId: string) {
    return client.post(`/review/undo?card_id=${cardId}`)
  },
  forecast(days = 30) {
    return client.get<ForecastDay[]>('/review/forecast', { params: { days } })
  },
}
