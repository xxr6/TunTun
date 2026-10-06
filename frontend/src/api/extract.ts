import { client } from './client'
import type { Note, NoteDetail } from '@/types/api'

export const extractApi = {
  fromFile(documentId: string) {
    // 提炼是「切段 → 逐段调 LLM」的同步长任务，大文件很容易超过全局 60s 超时，
    // 单独放宽到 5 分钟，避免前端先于后端超时误报「提炼失败」
    return client.post<NoteDetail>('/extract/from-file', { document_id: documentId }, { timeout: 300000 })
  },
  listNotes() {
    return client.get<Note[]>('/extract/notes')
  },
  getNote(id: string) {
    return client.get<NoteDetail>(`/extract/notes/${id}`)
  },
  splitCandidates(noteId: string, candidateIds: string[], deckId: string) {
    return client.post(`/extract/notes/${noteId}/split-candidates`, {
      candidate_ids: candidateIds,
      deck_id: deckId,
    })
  },
}
