import { client } from './client'
import type { CardSelectionOut } from '@/types/api'

export const aiApi = {
  cardsFromSelection(payload: {
    document_id: string
    selection: string
    locator?: Record<string, unknown> | null
    target_deck_id?: string | null
    mode?: string
    max_cards?: number
  }) {
    return client.post<CardSelectionOut>('/ai/cards/from-selection', payload)
  },
}
