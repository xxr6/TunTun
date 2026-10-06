import { defineStore } from 'pinia'
import { focusApi } from '@/api/focus'
import type { FocusSession } from '@/types/api'

export type FocusMode = 'pomodoro' | 'deep' | 'nap' | 'custom'

const PRESET_TOTAL: Record<Exclude<FocusMode, 'custom'>, number> = { pomodoro: 25 * 60, deep: 50 * 60, nap: 5 * 60 }
const BASE_TITLE = '囤囤 TUNTUN · 把知识一点点囤下来'

/** 放弃留痕阈值：专注不足 10 秒的不算一轮，避免误触产生垃圾会话 */
const ABANDON_MIN_MS = 10_000

/**
 * 专注计时核心（跨路由存活）：
 * - 墙钟计时：endAt 时间戳 + 每 tick 重算剩余，后台标签页节流/暂停恢复都不会漂移；
 * - 状态放在 Pinia store，切页面不杀会话（侧边栏迷你进度也读这里）；
 * - 放弃（重置/中途离开）调 createSession(completed=false) 留痕；
 * - 运行中同步 document.title，切走标签页也能看到进度。
 */
export const useFocusStore = defineStore('focus', {
  state: () => ({
    mode: 'pomodoro' as FocusMode,
    total: PRESET_TOTAL.pomodoro,
    remaining: PRESET_TOTAL.pomodoro,
    customMinutes: 45,
    running: false,
    paused: false,
    celebrating: false,
    startedAt: null as number | null,
    lastTickAt: null as number | null,
    endAt: null as number | null,
    focusedMs: 0,
    deckId: null as string | null,
    deckName: '',
    lastResult: null as FocusSession | null,
    lastError: '',
  }),
  getters: {
    /** 本次会话累计专注毫秒（含正在走的这一段） */
    elapsedMs(): number {
      return this.focusedMs + (this.running && this.lastTickAt ? Date.now() - this.lastTickAt : 0)
    },
    hasActiveSession(): boolean {
      return this.running || this.paused
    },
  },
  actions: {
    setMode(mode: FocusMode) {
      if (this.hasActiveSession) return
      this.mode = mode
      this.total = mode === 'custom' ? this.customMinutes * 60 : PRESET_TOTAL[mode]
      this.remaining = this.total
    },
    setCustom(minutes: number) {
      this.customMinutes = Math.min(240, Math.max(1, Math.round(minutes)))
      if (this.mode === 'custom' && !this.hasActiveSession) {
        this.total = this.customMinutes * 60
        this.remaining = this.total
      }
    },
    startSession(deckId: string | null, deckName: string) {
      if (this.running) return
      if (!this.paused) {
        // 全新一轮：重置累计
        this.startedAt = Date.now()
        this.focusedMs = 0
        this.deckId = deckId
        this.deckName = deckName
        this.remaining = this.total
      }
      this.lastTickAt = Date.now()
      this.endAt = Date.now() + this.remaining * 1000
      this.running = true
      this.paused = false
      this.celebrating = false
      this.lastResult = null
      this.lastError = ''
      this._requestNotify()
      ensureInterval(this)
      this.tick()
    },
    pause() {
      if (!this.running) return
      this.focusedMs += Date.now() - (this.lastTickAt ?? Date.now())
      this.lastTickAt = null
      this.endAt = null
      this.running = false
      this.paused = true
      this._syncTitle()
    },
    resume() {
      if (!this.paused) return
      this.startSession(this.deckId, this.deckName)
    },
    toggle() {
      if (this.running) this.pause()
      else if (this.paused) this.resume()
      else this.startSession(this.deckId, this.deckName)
    },
    /** 重置（=放弃当前轮）：留痕后清空状态 */
    reset() {
      this._abandon()
      this._clear()
    },
    /** 放弃当前轮：completed=false 留痕（后端不计入专注统计，但会话列表里有这条「痕迹」） */
    _abandon() {
      const elapsed = this.elapsedMs
      if (this.startedAt === null || elapsed < ABANDON_MIN_MS) return
      const now = new Date()
      focusApi
        .createSession({
          mode: this.mode,
          started_at: new Date(this.startedAt).toISOString(),
          ended_at: now.toISOString(),
          duration_seconds: Math.round(elapsed / 1000),
          completed: false,
          deck_id: this.deckId,
          deck_name: this.deckName,
        })
        .catch(() => {
          this.lastError = '这一轮没存上，时间丢了'
        })
    },
    _clear() {
      this.running = false
      this.paused = false
      this.celebrating = false
      this.startedAt = null
      this.lastTickAt = null
      this.endAt = null
      this.focusedMs = 0
      this.remaining = this.total
      this.deckId = null
      this.deckName = ''
      this._syncTitle()
    },
    tick() {
      if (!this.running || this.endAt === null) return
      const left = this.endAt - Date.now()
      this.remaining = Math.max(0, Math.ceil(left / 1000))
      this._syncTitle()
      if (left <= 0) this.finish()
    },
    async finish() {
      if (!this.running) return
      const ended = new Date()
      this.running = false
      this.paused = false
      this.lastTickAt = null
      this.endAt = null
      this.remaining = 0
      this._syncTitle()
      try {
        this.lastResult = (
          await focusApi.createSession({
            mode: this.mode,
            started_at: new Date(this.startedAt ?? Date.now()).toISOString(),
            ended_at: ended.toISOString(),
            duration_seconds: this.total,
            completed: true,
            deck_id: this.deckId,
            deck_name: this.deckName,
          })
        ).data
        this.celebrating = true
        this._celebrate()
      } catch {
        this.lastError = '这一轮没存上，点「再来一轮」重试'
        this.celebrating = true
      }
    },
    dismissCelebration() {
      this.celebrating = false
    },
    /** 庆祝：提示音 + 系统通知（页面在后台时才通知） */
    _celebrate() {
      this._chime()
      if ('Notification' in window && Notification.permission === 'granted' && document.hidden) {
        try {
          new Notification('专注完成 🍅', { body: '这一轮啃完了，休息一下或再来一轮' })
        } catch {
          /* 通知失败不影响庆祝 */
        }
      }
    },
    _requestNotify() {
      if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().catch(() => {})
      }
    },
    /** 两音小铃声：贴纸风的短促「叮咚」，用 WebAudio 合成，不依赖素材 */
    _chime() {
      try {
        const Ctx = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
        if (!Ctx) return
        const ctx = new Ctx()
        const play = (freq: number, at: number, dur = 0.16) => {
          const osc = ctx.createOscillator()
          const gain = ctx.createGain()
          osc.type = 'sine'
          osc.frequency.value = freq
          gain.gain.setValueAtTime(0.0001, ctx.currentTime + at)
          gain.gain.exponentialRampToValueAtTime(0.18, ctx.currentTime + at + 0.02)
          gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + at + dur)
          osc.connect(gain)
          gain.connect(ctx.destination)
          osc.start(ctx.currentTime + at)
          osc.stop(ctx.currentTime + at + dur + 0.05)
        }
        play(880, 0)
        play(1318.5, 0.14, 0.28)
        setTimeout(() => ctx.close().catch(() => {}), 1200)
      } catch {
        /* 无音频环境时静默 */
      }
    },
    _syncTitle() {
      if (this.running) {
        const m = String(Math.floor(this.remaining / 60)).padStart(2, '0')
        const s = String(this.remaining % 60).padStart(2, '0')
        document.title = `${m}:${s} 专注中 · 囤囤`
      } else {
        document.title = BASE_TITLE
      }
    },
  },
})

/* ── 全局唯一 interval + visibilitychange 校正：放在 store 定义外面，模块级共享 ── */
let timer: ReturnType<typeof setInterval> | null = null
let storeRef: ReturnType<typeof useFocusStore> | null = null

function ensureInterval(store: ReturnType<typeof useFocusStore>) {
  storeRef = store
  if (import.meta.env.DEV) (window as unknown as Record<string, unknown>).__focusStore = store
  if (timer) return
  timer = setInterval(() => storeRef?.tick(), 250)
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') storeRef?.tick()
  })
}
