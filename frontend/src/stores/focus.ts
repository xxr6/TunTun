import { defineStore } from 'pinia'
import { focusApi } from '@/api/focus'
import type { FocusSession } from '@/types/api'

export type FocusMode = 'pomodoro' | 'deep' | 'nap' | 'custom' | 'countup'

const PRESET_TOTAL: Record<Exclude<FocusMode, 'custom'>, number> = { pomodoro: 25 * 60, deep: 50 * 60, nap: 5 * 60, countup: 60 * 60 }
const BASE_TITLE = '囤囤 TUNTUN · 把知识一点点囤下来'

export function formatFocusClock(seconds: number): string {
  const whole = Math.max(0, Math.floor(seconds))
  const hours = Math.floor(whole / 3600)
  const minutes = Math.floor((whole % 3600) / 60)
  const secs = String(whole % 60).padStart(2, '0')
  return hours > 0
    ? `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${secs}`
    : `${String(Math.floor(whole / 60)).padStart(2, '0')}:${secs}`
}

/** 放弃留痕阈值：专注不足 10 秒的不算一轮，避免误触产生垃圾会话 */
const ABANDON_MIN_MS = 10_000
const STORAGE_PREFIX = 'zhistack.focus.v2.'
const SETTINGS_PREFIX = 'zhistack.focus.settings.'

function clampMinutes(value: unknown, fallback: number): number {
  const n = Number(value)
  return Number.isFinite(n) ? Math.max(1, Math.min(60, Math.round(n))) : fallback
}

/**
 * 专注计时核心（跨路由存活）：
 * - 墙钟计时：倒计时根据 endAt 重算，正向计时根据开始时间和累计时长重算；
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
    sessionId: null as string | null,
    ownerId: null as string | null,
    pendingSave: false,
    saving: false,
    shortBreakMinutes: 5,
    longBreakMinutes: 15,
    roundsBeforeLongBreak: 4,
    autoStartBreak: false,
    roundInCycle: 0,
    breakKind: 'short' as 'short' | 'long',
    lastWorkMode: 'pomodoro' as Exclude<FocusMode, 'nap'>,
    lastWorkDeckId: null as string | null,
    lastWorkDeckName: '',
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
    restore(userId: string) {
      this.ownerId = userId
      try {
        const settings = JSON.parse(localStorage.getItem(SETTINGS_PREFIX + userId) || '{}')
        this.shortBreakMinutes = clampMinutes(settings.shortBreakMinutes, 5)
        this.longBreakMinutes = clampMinutes(settings.longBreakMinutes, 15)
        this.roundsBeforeLongBreak = Math.max(2, Math.min(8, Number(settings.roundsBeforeLongBreak) || 4))
        this.autoStartBreak = settings.autoStartBreak === true
        this.roundInCycle = Math.max(0, Number(settings.roundInCycle) || 0)
        const saved = JSON.parse(localStorage.getItem(STORAGE_PREFIX + userId) || 'null')
        if (!saved || saved.v !== 2 || !saved.sessionId || !saved.startedAt || (saved.mode !== 'countup' && Date.now() - saved.startedAt > 24 * 3600_000)) {
          localStorage.removeItem(STORAGE_PREFIX + userId)
          return
        }
        if (!['pomodoro', 'deep', 'nap', 'custom', 'countup'].includes(saved.mode)) return
        this.mode = saved.mode
        this.total = Math.max(1, Number(saved.total) || PRESET_TOTAL.pomodoro)
        this.customMinutes = clampMinutes(saved.customMinutes, 45)
        this.startedAt = saved.startedAt
        this.lastTickAt = saved.lastTickAt ?? null
        this.endAt = saved.endAt ?? null
        this.focusedMs = Math.max(0, Number(saved.focusedMs) || 0)
        this.sessionId = saved.sessionId
        this.deckId = saved.deckId ?? null
        this.deckName = saved.deckName ?? ''
        this.lastWorkDeckId = saved.lastWorkDeckId ?? this.deckId
        this.lastWorkDeckName = saved.lastWorkDeckName ?? this.deckName
        this.breakKind = saved.breakKind === 'long' ? 'long' : 'short'
        this.lastWorkMode = ['pomodoro', 'deep', 'custom', 'countup'].includes(saved.lastWorkMode)
          ? saved.lastWorkMode : (saved.mode === 'nap' ? 'pomodoro' : saved.mode)
        this.pendingSave = saved.pendingSave === true
        this.running = saved.running === true && !this.pendingSave
        this.paused = saved.paused === true && !this.pendingSave
        this.remaining = this.mode === 'countup'
          ? Math.floor((this.focusedMs + (this.running && this.lastTickAt ? Math.max(0, Date.now() - this.lastTickAt) : 0)) / 1000)
          : this.running && this.endAt !== null
            ? Math.max(0, Math.ceil((this.endAt - Date.now()) / 1000))
            : Math.max(0, Number(saved.remaining) || 0)
        if (this.pendingSave) void this.finish()
        else if (this.running) { ensureInterval(this); this.tick() }
        this._syncTitle()
      } catch {
        localStorage.removeItem(STORAGE_PREFIX + userId)
      }
    },
    setBreakSettings(shortMinutes: number, longMinutes: number, rounds: number, autoStart: boolean) {
      this.shortBreakMinutes = clampMinutes(shortMinutes, 5)
      this.longBreakMinutes = clampMinutes(longMinutes, 15)
      this.roundsBeforeLongBreak = Math.max(2, Math.min(8, Math.round(rounds) || 4))
      this.autoStartBreak = autoStart
      this._persistSettings()
    },
    _persistSettings() {
      if (!this.ownerId) return
      localStorage.setItem(SETTINGS_PREFIX + this.ownerId, JSON.stringify({
        shortBreakMinutes: this.shortBreakMinutes, longBreakMinutes: this.longBreakMinutes,
        roundsBeforeLongBreak: this.roundsBeforeLongBreak, autoStartBreak: this.autoStartBreak,
        roundInCycle: this.roundInCycle,
      }))
    },
    _persist() {
      if (!this.ownerId) return
      const key = STORAGE_PREFIX + this.ownerId
      if (!this.sessionId || (!this.running && !this.paused && !this.pendingSave)) {
        localStorage.removeItem(key)
        return
      }
      localStorage.setItem(key, JSON.stringify({
        v: 2, sessionId: this.sessionId, mode: this.mode, total: this.total,
        remaining: this.remaining, customMinutes: this.customMinutes, running: this.running,
        paused: this.paused, pendingSave: this.pendingSave, startedAt: this.startedAt,
        lastTickAt: this.lastTickAt, endAt: this.endAt, focusedMs: this.focusedMs,
        deckId: this.deckId, deckName: this.deckName, breakKind: this.breakKind,
        lastWorkDeckId: this.lastWorkDeckId, lastWorkDeckName: this.lastWorkDeckName,
        lastWorkMode: this.lastWorkMode,
      }))
    },
    forgetLocal() {
      if (this.ownerId) localStorage.removeItem(STORAGE_PREFIX + this.ownerId)
      this._clear()
      this.ownerId = null
    },
    setMode(mode: FocusMode) {
      if (this.hasActiveSession || this.pendingSave) return
      this.mode = mode
      this.total = mode === 'custom' ? this.customMinutes * 60 : PRESET_TOTAL[mode]
      this.remaining = mode === 'countup' ? 0 : this.total
    },
    setCustom(minutes: number) {
      this.customMinutes = Math.min(240, Math.max(1, Math.round(minutes)))
      if (this.mode === 'custom' && !this.hasActiveSession) {
        this.total = this.customMinutes * 60
        this.remaining = this.total
      }
    },
    startSession(deckId: string | null, deckName: string) {
      if (this.running || this.pendingSave) return
      if (!this.paused) {
        // 全新一轮：重置累计
        this.sessionId = crypto.randomUUID()
        this.startedAt = Date.now()
        this.focusedMs = 0
        this.deckId = deckId
        this.deckName = deckName
        this.remaining = this.mode === 'countup' ? 0 : this.total
        if (this.mode !== 'nap') {
          this.lastWorkMode = this.mode
          this.lastWorkDeckId = deckId
          this.lastWorkDeckName = deckName
        }
      }
      this.lastTickAt = Date.now()
      this.endAt = this.mode === 'countup' ? null : Date.now() + this.remaining * 1000
      this.running = true
      this.paused = false
      this.celebrating = false
      this.lastResult = null
      this.lastError = ''
      this._requestNotify()
      ensureInterval(this)
      this.tick()
      this._persist()
    },
    startBreak() {
      if (this.hasActiveSession || this.pendingSave) return
      this.celebrating = false
      this.breakKind = this.roundInCycle > 0 && this.roundInCycle % this.roundsBeforeLongBreak === 0 ? 'long' : 'short'
      this.mode = 'nap'
      this.total = (this.breakKind === 'long' ? this.longBreakMinutes : this.shortBreakMinutes) * 60
      this.remaining = this.total
      this.startSession(null, '')
    },
    startNextFocus() {
      if (this.hasActiveSession || this.pendingSave) return
      this.celebrating = false
      this.setMode(this.lastWorkMode)
      this.startSession(this.lastWorkDeckId, this.lastWorkDeckName)
    },
    pause() {
      if (!this.running) return
      this.focusedMs += Date.now() - (this.lastTickAt ?? Date.now())
      if (this.mode === 'countup') this.remaining = Math.floor(this.focusedMs / 1000)
      this.lastTickAt = null
      this.endAt = null
      this.running = false
      this.paused = true
      this._syncTitle()
      this._persist()
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
    /** 打断并结束：保存已经专注的时间，保存失败时保留暂停状态以便重试。 */
    async interrupt(): Promise<FocusSession | null> {
      if (!this.hasActiveSession) return null
      if (this.running) this.pause()
      const elapsed = this.focusedMs
      if (this.startedAt === null) return null
      if (elapsed < 1000) {
        this._clear()
        return null
      }
      try {
        const result = (
          await focusApi.createSession({
            id: this.sessionId ?? undefined,
            mode: this.mode,
            started_at: new Date(this.startedAt).toISOString(),
            ended_at: new Date().toISOString(),
            duration_seconds: Math.max(1, Math.round(elapsed / 1000)),
            completed: false,
            interrupted: true,
            deck_id: this.deckId,
            deck_name: this.deckName,
          })
        ).data
        this.lastResult = result
        this.lastError = ''
        this._clear()
        return result
      } catch {
        this.lastError = '专注时间没存上，请重试；计时已暂停，记录还在'
        this._persist()
        throw new Error(this.lastError)
      }
    },
    /** 放弃当前轮：completed=false 留痕（后端不计入专注统计，但会话列表里有这条「痕迹」） */
    _abandon() {
      const elapsed = this.elapsedMs
      if (this.startedAt === null || elapsed < ABANDON_MIN_MS) return
      const now = new Date()
      focusApi
        .createSession({
          id: this.sessionId ?? undefined,
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
      this.sessionId = null
      this.pendingSave = false
      this.remaining = this.mode === 'countup' ? 0 : this.total
      this.deckId = null
      this.deckName = ''
      this._syncTitle()
      this._persist()
    },
    tick() {
      if (this.running && this.mode === 'countup') {
        this.remaining = Math.floor(this.elapsedMs / 1000)
        this._syncTitle()
        return
      }
      if (!this.running || this.endAt === null) return
      const left = this.endAt - Date.now()
      this.remaining = Math.max(0, Math.ceil(left / 1000))
      this._syncTitle()
      if (left <= 0) this.finish()
    },
    async finish() {
      if ((!this.running && !this.pendingSave) || this.saving) return
      this.saving = true
      const ended = new Date()
      this.running = false
      this.paused = false
      this.lastTickAt = null
      this.endAt = null
      this.remaining = 0
      this.pendingSave = true
      this._persist()
      this._syncTitle()
      try {
        this.lastResult = (
          await focusApi.createSession({
            id: this.sessionId ?? undefined,
            mode: this.mode,
            started_at: new Date(this.startedAt ?? Date.now()).toISOString(),
            ended_at: ended.toISOString(),
            duration_seconds: this.total,
            completed: true,
            deck_id: this.deckId,
            deck_name: this.deckName,
          })
        ).data
        this.pendingSave = false
        if (this.mode === 'pomodoro') {
          this.roundInCycle += 1
          this._persistSettings()
        }
        this._persist()
        if (this.mode === 'pomodoro' && this.autoStartBreak) {
          this._chime()
          this.startBreak()
        } else {
          this.celebrating = true
          this._celebrate()
        }
      } catch {
        this.lastError = '这一轮没存上，点「再来一轮」重试'
        this.celebrating = true
        this._persist()
      } finally {
        this.saving = false
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
        document.title = `${this.mode === 'countup' ? '+' : ''}${formatFocusClock(this.remaining)} ${this.mode === 'nap' ? '休息中' : '专注中'} · 囤囤`
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
