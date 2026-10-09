import { defineStore } from 'pinia'
import { extractApi } from '@/api/extract'
import type { NoteDetail } from '@/types/api'

let stepTimers: ReturnType<typeof setTimeout>[] = []
let runVersion = 0

function clearStepTimers() {
  stepTimers.forEach(clearTimeout)
  stepTimers = []
}

export const useExtractStore = defineStore('extract', {
  state: () => ({
    sourceDocId: null as string | null,
    currentNote: null as NoteDetail | null,
    selectedIds: [] as string[],
    viewMode: 'read' as 'read' | 'source',
    loading: false,
    stepIdx: -1,
    err: '',
  }),
  actions: {
    async run(docId: string | null) {
      if (!docId || this.loading) return
      const version = ++runVersion
      clearStepTimers()
      this.loading = true
      this.err = ''
      this.currentNote = null
      this.selectedIds = []
      this.viewMode = 'read'
      this.stepIdx = 0

      // 前三步是界面引导；AI 阶段等待接口的真实完成结果。
      for (const [index, delay] of [700, 1600, 2300].entries()) {
        stepTimers.push(setTimeout(() => {
          if (version === runVersion) this.stepIdx = index + 1
        }, delay))
      }

      try {
        const res = await extractApi.fromFile(docId)
        if (version !== runVersion) return
        clearStepTimers()
        this.currentNote = res.data
        this.selectedIds = res.data.candidates
          .filter((candidate) => candidate.confidence >= 0.8 && !candidate.card_id)
          .map((candidate) => candidate.id)
        this.stepIdx = 5
        stepTimers.push(setTimeout(() => {
          if (version === runVersion) this.loading = false
        }, 450))
      } catch (error: any) {
        if (version !== runVersion) return
        clearStepTimers()
        this.stepIdx = -1
        this.loading = false
        this.err = error?.response?.data?.message || '提炼失败'
      }
    },
    resetSession() {
      ++runVersion
      clearStepTimers()
      this.$reset()
    },
  },
})
