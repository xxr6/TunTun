<template>
  <div class="focus-page">
    <div class="focus-inner">
      <header class="fp-header rise">
        <h1 class="h-page fp-title-row">专注 <img class="fp-title-tomato" :src="tomatoWave" alt="" aria-hidden="true" /></h1>
        <p class="h-sub">留下一段专注的时间，给重要的事。</p>
      </header>

      <div class="fp-workspace">
        <section class="fp-main-card rise" aria-label="专注计时器">
          <div class="fp-card-heading"><span class="fp-heading-mark"></span><h2>{{ store.mode === 'nap' ? '休息时间' : store.mode === 'countup' ? '正向计时' : '专注时间' }}</h2></div>
          <div class="fp-timer-note" aria-hidden="true"><span>专注当下，慢慢变好。</span><img :src="tomatoTilt" alt="" /></div>
          <div class="fp-timer-zone">
            <div class="fp-blob fp-blob-a" aria-hidden="true"></div>
            <div class="fp-blob fp-blob-b" aria-hidden="true"></div>
            <div class="fp-timer" :class="{ running: store.running, completed: store.celebrating }" @click="onToggle">
              <svg class="fp-ring" viewBox="0 0 300 300" :role="store.mode === 'countup' ? 'timer' : 'progressbar'"
                   :aria-valuemin="store.mode === 'countup' ? undefined : 0"
                   :aria-valuemax="store.mode === 'countup' ? undefined : store.total"
                   :aria-valuenow="store.mode === 'countup' ? undefined : store.remaining"
                   :aria-label="store.mode === 'countup' ? `已专注 ${formatFocusClock(store.remaining)}` : '专注倒计时'">
                <defs>
                  <linearGradient id="focusGrad" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stop-color="var(--orange)" />
                    <stop offset="100%" stop-color="var(--ham)" />
                  </linearGradient>
                </defs>
                <circle class="fp-trk" cx="150" cy="150" r="138" fill="none" stroke-width="13" />
                <circle class="fp-bar" cx="150" cy="150" r="138" fill="none" stroke-width="13"
                        :stroke-dasharray="CIRC" :stroke-dashoffset="dashOffset" />
              </svg>
              <div class="fp-mid">
                <div class="fp-tm" :class="{ long: store.remaining >= 3600 }">{{ formatFocusClock(store.remaining) }}</div>
                <div class="fp-tl" aria-live="polite">{{ statusText }}</div>
              </div>
            </div>
          </div>
          <div class="fp-controls">
            <button class="fp-btn-warm fp-cta" @click="onToggle">
              <svg class="icon"><use :href="store.running ? '#i-pause' : '#i-play'" /></svg>
              <span>{{ store.mode === 'nap' ? (store.running ? '暂停休息' : store.paused ? '继续休息' : '开始休息') : store.mode === 'countup' ? (store.running ? '暂停计时' : store.paused ? '继续计时' : '开始计时') : (store.running ? '暂停专注' : store.paused ? '继续专注' : '开始专注') }}</span>
            </button>
            <button class="fp-interrupt" :disabled="!store.hasActiveSession || interrupting" @click="onInterrupt">
              {{ store.mode === 'countup' ? '结束并保存' : '打断并结束' }}
            </button>
            <button class="fp-reset" :disabled="!store.hasActiveSession" @click="onReset">
              <svg class="icon"><use href="#i-refresh" /></svg>重置
            </button>
          </div>
          <p v-if="interruptNotice" class="fp-interrupt-notice" role="status">{{ interruptNotice }}</p>
        </section>

        <aside class="fp-side rise">
          <section class="fp-side-card fp-task-card">
            <div class="fp-card-heading"><span class="fp-heading-mark"></span><h2>这次专注于</h2></div>
            <img class="fp-corner-mascot" :src="tomatoCup" alt="" aria-hidden="true" />
            <div class="fp-intent" :class="{ off: store.hasActiveSession || store.pendingSave }">
              <svg class="icon fp-intent-book" aria-hidden="true"><use href="#i-book" /></svg>
              <span v-if="store.hasActiveSession || store.pendingSave" class="fp-intent-current">{{ store.deckName || '不指定，纯粹留时间' }}</span>
              <select v-else v-model="targetChoice" class="fp-intent-select" aria-label="选择或自定义本次专注内容" @change="targetError = ''">
                <option value="">不指定，纯粹留时间</option>
                <option v-for="d in decks" :key="d.id" :value="d.id">{{ d.name }}</option>
                <option v-for="name in savedTopics" :key="name" :value="`saved:${name}`">{{ name }} · 常用</option>
                <option value="__custom__">新建自定义内容…</option>
              </select>
              <svg v-if="!store.hasActiveSession" class="icon fp-intent-chev" aria-hidden="true"><use href="#i-chev" /></svg>
            </div>
            <input v-if="targetChoice === '__custom__' && !store.hasActiveSession" v-model="customTarget"
                   class="fp-intent-custom" maxlength="120" placeholder="例如：读完第三章、准备面试" aria-label="自定义本次专注内容"
                   @input="targetError = ''" />
            <div v-if="targetChoice === '__custom__' && savedTopics.length && !store.hasActiveSession" class="fp-topic-history">
              <span>最近使用</span>
              <div v-for="name in savedTopics.slice(0, 5)" :key="name" class="fp-topic-history-row">
                <button type="button" @click="customTarget = name">{{ name }}</button>
                <button type="button" :aria-label="`移除常用内容 ${name}`" @click="forgetTopic(name)">×</button>
              </div>
            </div>
            <p v-if="targetError" class="fp-intent-error" role="alert">{{ targetError }}</p>
          </section>

          <section class="fp-side-card fp-mode-card">
            <div class="fp-card-heading"><span class="fp-heading-mark"></span><h2>专注模式</h2></div>
            <div class="fp-modes" role="group" aria-label="专注模式">
              <button v-for="m in MODES" :key="m.key" class="fp-mode" :class="[{ on: store.mode === m.key }, m.key]"
                      :disabled="store.hasActiveSession || store.pendingSave" :aria-pressed="store.mode === m.key"
                      @click="store.setMode(m.key)">
                <span class="fp-mode-icon" aria-hidden="true">
                  <img v-if="m.key === 'pomodoro'" :src="tomatoPeek" alt="" />
                  <svg v-else class="icon"><use :href="m.icon" /></svg>
                </span>
                <span class="fp-mode-copy"><b>{{ m.label }}</b><small v-if="m.min">{{ m.key === 'nap' ? `${store.shortBreakMinutes} 分钟` : m.min }}</small></span>
                <svg v-if="store.mode === m.key" class="icon fp-mode-check" aria-hidden="true"><use href="#i-check" /></svg>
              </button>
            </div>
            <div v-if="store.mode === 'custom' && !store.hasActiveSession" class="custom-row rise">
              <button class="step-btn" aria-label="减少 1 分钟" @click="store.setCustom(store.customMinutes - 1)">−</button>
              <input class="custom-input" type="number" min="1" max="240" :value="store.customMinutes"
                     aria-label="自定义专注分钟数" @change="onCustomInput" />
              <span class="custom-unit">分钟</span>
              <button class="step-btn" aria-label="增加 1 分钟" @click="store.setCustom(store.customMinutes + 1)">+</button>
            </div>
            <details v-if="store.mode === 'pomodoro'" class="fp-cycle-settings">
              <summary>番茄循环 · 第 {{ store.roundInCycle % store.roundsBeforeLongBreak + 1 }} / {{ store.roundsBeforeLongBreak }} 轮 <span>设置休息</span></summary>
              <div class="fp-cycle-fields">
                <label>短休息 <input type="number" min="1" max="60" :disabled="store.hasActiveSession" :value="store.shortBreakMinutes" @change="onBreakSetting('short', $event)" /> 分钟</label>
                <label>长休息 <input type="number" min="1" max="60" :disabled="store.hasActiveSession" :value="store.longBreakMinutes" @change="onBreakSetting('long', $event)" /> 分钟</label>
                <label>长休息间隔 <input type="number" min="2" max="8" :disabled="store.hasActiveSession" :value="store.roundsBeforeLongBreak" @change="onBreakSetting('rounds', $event)" /> 轮</label>
                <label class="fp-auto-break"><input type="checkbox" :disabled="store.hasActiveSession" :checked="store.autoStartBreak" @change="onBreakSetting('auto', $event)" /> 完成后自动开始休息</label>
              </div>
            </details>
          </section>

          <button v-if="!store.hasActiveSession && !store.celebrating" class="fp-quick-start btn btn-primary" @click="onToggle">选好了，开始{{ store.mode === 'nap' ? '休息' : store.mode === 'countup' ? '正向计时' : '专注' }} →</button>

          <div class="fp-reminder" :class="{ err: dueError }">
            <span class="fp-reminder-icon"><svg class="icon"><use href="#i-cards" /></svg></span>
            <span class="fp-reminder-text">
              <b>{{ dueError ? '到期卡暂时没加载到' : dueCount > 0 ? `还有 ${dueCount} 张到期卡片` : needsRepair > 0 ? `${needsRepair} 张卡待补全` : '今天没有到期卡片' }}</b>
              <small>{{ dueError ? '不影响开始专注' : dueCount > 0 ? '先复习，再专注也不错' : needsRepair > 0 ? '补上答案后才能复习' : '可以安心开始专注了' }}</small>
            </span>
            <button class="fp-reminder-link" @click="needsRepair > 0 && dueCount === 0 ? router.push('/decks') : goReview()">{{ needsRepair > 0 && dueCount === 0 ? '去补全' : '去复习' }} <svg class="icon"><use href="#i-chev" /></svg></button>
            <img class="fp-reminder-mascot" :src="tomatoWave" alt="" aria-hidden="true" />
          </div>
        </aside>
      </div>

      <div class="fp-stats rise" aria-label="专注统计">
        <button class="fp-stat" @click="goStats">
          <span class="fp-stat-ic tomato" aria-hidden="true"><img :src="tomatoPeek" alt="" /></span>
          <span class="fp-stat-copy"><b>今日番茄</b><strong>{{ summary.today_count }}<small>/ {{ POMODORO_GOAL }}</small></strong></span>
          <span class="fp-dots" aria-hidden="true"><i v-for="i in dotCount" :key="i" :class="{ on: i <= summary.today_count }"></i></span>
        </button>
        <button class="fp-stat" @click="goStats">
          <span class="fp-stat-ic mint" aria-hidden="true"><svg class="icon"><use href="#i-leaf" /></svg></span>
          <span class="fp-stat-copy"><b>今日专注 <small>· 目标 {{ Math.round((dash?.focus.today.goal ?? 10800) / 3600) }}h</small></b><strong>{{ todayMin }}<small>分钟</small></strong></span>
          <span class="fp-stat-progress" aria-hidden="true"><i :style="{ width: todayPct + '%' }"></i></span>
        </button>
        <button class="fp-stat" @click="goStats">
          <span class="fp-stat-ic grape" aria-hidden="true"><svg class="icon"><use href="#i-calendar" /></svg></span>
          <span class="fp-stat-copy"><b>本周专注</b><strong>{{ weekMin }}<small>分钟</small></strong></span>
          <span class="fp-week" aria-hidden="true"><span v-for="(d, i) in weekBars" :key="i" :class="{ today: d.today }" :style="{ height: d.h / 2 + 'px' }" :title="d.title"></span></span>
        </button>
      </div>
    </div>

    <!-- 完成庆祝弹层 -->
    <Transition name="celebrate">
      <div v-if="store.celebrating" class="celebrate-mask" role="dialog" aria-modal="true" aria-label="这一轮完成">
        <div class="card celebrate-card">
          <div class="celebrate-tomato" aria-hidden="true">
            <img :src="tomatoWave" alt="" />
          </div>
          <h2>{{ store.lastResult ? (store.mode === 'nap' ? '休息结束，继续下一轮吧' : '这一轮啃完了！') : '计时走完了，但记录没存上' }}</h2>
          <p class="celebrate-sub" aria-live="polite">
            <template v-if="store.lastResult">{{ store.mode === 'nap' ? '已休息好，可以继续专注。' : store.mode === 'pomodoro' ? `+1 番茄入罐 · 今天已完成 ${summary.today_count} 轮` : '这一段专注已保存。' }}</template>
            <template v-else>{{ store.lastError || '稍后再试一次' }}</template>
          </p>
          <div v-if="newBadge" class="celebrate-badge">
            <svg class="icon"><use :href="newBadge.icon" /></svg>
            新成就「{{ newBadge.name }}」解锁！
          </div>
          <div class="celebrate-actions">
            <button v-if="store.mode !== 'nap' && store.lastResult" class="btn btn-soft" @click="takeRest">
              <svg class="icon"><use href="#i-moon" /></svg>{{ nextBreakLabel }}
            </button>
            <button class="btn btn-primary" @click="again">
              <svg class="icon"><use href="#i-play" /></svg>{{ store.lastResult ? (store.mode === 'nap' ? '开始下一轮' : '再来一轮') : '重试保存' }}
            </button>
          </div>
          <button class="celebrate-close" @click="store.dismissCelebration()">收起</button>
        </div>
      </div>
    </Transition>

    <!-- 贴纸风二次确认：重置 -->
    <ConfirmDialog
      :visible="confirmReset"
      title="确定要重置这一轮？"
      :message="store.mode === 'countup' ? '正向计时会从 00:00 重新开始，已走过的时间不计入专注统计。' : '这轮会重新从头计时，已走过的时间不计入专注统计。'"
      confirm-text="重置"
      danger
      @confirm="doReset"
      @cancel="confirmReset = false"
    />
    <ConfirmDialog
      :visible="confirmInterrupt"
      :title="store.mode === 'countup' ? '结束并保存这次专注？' : '打断并结束这轮专注？'"
      :message="store.mode === 'countup' ? '已专注的时间会保存并计入今日、本周和本月；正向计时不会算作完成一颗番茄。' : '已专注的时间会保存，计入今日和本周时长，但不会算作完成一颗番茄。'"
      confirm-text="保存并结束"
      @confirm="doInterrupt"
      @cancel="confirmInterrupt = false"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { decksApi } from '@/api/decks'
import { authApi } from '@/api/auth'
import { focusApi } from '@/api/focus'
import { reviewApi } from '@/api/review'
import { statsApi } from '@/api/stats'
import { useFocusStore, formatFocusClock, type FocusMode } from '@/stores/focus'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import tomatoWave from '@/assets/mascots/tomato-wave.svg'
import tomatoCup from '@/assets/mascots/tomato-cup.svg'
import tomatoTilt from '@/assets/mascots/tomato-tilt.svg'
import tomatoPeek from '@/assets/mascots/tomato-peek.svg'
import type { Deck, FocusSummary, StatsDashboard } from '@/types/api'

const router = useRouter()
const route = useRoute()
const store = useFocusStore()

const MODES: { key: FocusMode; icon: string; label: string; min: string }[] = [
  { key: 'pomodoro', icon: '#i-tomato', label: '番茄', min: '25 分钟' },
  { key: 'deep', icon: '#i-leaf', label: '深度', min: '50 分钟' },
  { key: 'nap', icon: '#i-cup', label: '打盹', min: '5 分钟' },
  { key: 'custom', icon: '#i-gear', label: '自定义', min: '' },
  { key: 'countup', icon: '#i-timer', label: '正向计时', min: '不限时 · 手动结束' },
]

const POMODORO_GOAL = 4 // 每日番茄目标（颗）
const WEEK_DAYS = ['一', '二', '三', '四', '五', '六', '日']

const decks = ref<Deck[]>([])
const targetChoice = ref('')
const customTarget = ref('')
const targetError = ref('')
const savedTopics = ref<string[]>([])
const summary = ref<FocusSummary>({ today_seconds: 0, week_seconds: 0, month_seconds: 0, today_count: 0 })
const dash = ref<StatsDashboard | null>(null)
const dueCount = ref(0)
const needsRepair = ref(0)
const dueError = ref(false)
const unlockedRef = ref<Set<string>>(new Set())
const newBadge = ref<StatsDashboard['achievements'][number] | null>(null)
const confirmReset = ref(false)
const confirmInterrupt = ref(false)
const interrupting = ref(false)
const interruptNotice = ref('')

const CIRC = 2 * Math.PI * 138
const dashOffset = computed(() => CIRC * (store.mode === 'countup'
  ? 1 - (store.remaining % store.total) / store.total
  : 1 - store.remaining / store.total))
const nextBreakLabel = computed(() => {
  const long = store.roundInCycle > 0 && store.roundInCycle % store.roundsBeforeLongBreak === 0
  return `${long ? '长休息' : '短休息'} · ${long ? store.longBreakMinutes : store.shortBreakMinutes} 分钟`
})

/** 今日/本周专注分钟（完成和主动打断均计入，打盹除外） */
const todayMin = computed(() => Math.round((dash.value?.focus.today.sec ?? summary.value.today_seconds) / 60))
const weekMin = computed(() => Math.round((dash.value?.focus.week.sec ?? summary.value.week_seconds) / 60))
const todayPct = computed(() => dash.value?.focus.today.pct ?? Math.min(100, Math.round((summary.value.today_seconds / 10800) * 100)))
const dotCount = computed(() => Math.max(POMODORO_GOAL, Math.min(summary.value.today_count, 8)))

/** 本周 7 根小柱：dist_week 的 key 是 一二三四五六日 */
const weekBars = computed(() => {
  const dist = dash.value?.focus.dist_week ?? {}
  const todayIdx = (new Date().getDay() + 6) % 7
  const secs = WEEK_DAYS.map((label, i) => ({ label, sec: dist[label] ?? 0, today: i === todayIdx }))
  const max = Math.max(...secs.map((d) => d.sec), 1)
  return secs.map((d) => ({
    ...d,
    h: Math.max(6, Math.round((d.sec / max) * 40)),
    title: `周${d.label} · ${Math.round(d.sec / 60)} 分钟`,
  }))
})

const statusText = computed(() => {
  if (store.pendingSave) return '正在保存这一轮…'
  if (store.celebrating) return store.mode === 'nap' ? '休息完成' : '这一轮完成，休息一下吧'
  if (store.running) return store.mode === 'nap' ? '休息中，放松一下' : store.mode === 'countup' ? '正在累计专注时间' : '专注中，别分心'
  if (store.paused) return '已暂停，随时继续'
  return store.mode === 'countup' ? '从 00:00 开始' : '准备开始'
})

async function onToggle() {
  interruptNotice.value = ''
  if (store.pendingSave) { await store.finish(); return }
  if (!store.hasActiveSession) {
    if (targetChoice.value === '__custom__' && !customTarget.value.trim()) {
      targetError.value = '先写下这次要专注的内容'
      return
    }
    // 卡组或自定义内容都作为会话快照保存，统计按此名称聚合。
    const savedName = targetChoice.value.startsWith('saved:') ? targetChoice.value.slice(6) : ''
    store.deckId = targetChoice.value && targetChoice.value !== '__custom__' && !savedName ? targetChoice.value : null
    store.deckName = targetChoice.value === '__custom__'
      ? customTarget.value.trim()
      : (savedName || decks.value.find((d) => d.id === targetChoice.value)?.name || '')
    store.toggle()
    if (targetChoice.value === '__custom__' || savedName) {
      try {
        savedTopics.value = (await authApi.rememberFocusTopic(store.deckName)).data
      } catch {
        targetError.value = '专注已开始，但常用内容暂时没保存成功'
      }
    }
    return
  }
  store.toggle()
}

function onBreakSetting(field: 'short' | 'long' | 'rounds' | 'auto', event: Event) {
  const input = event.target as HTMLInputElement
  store.setBreakSettings(
    field === 'short' ? Number(input.value) : store.shortBreakMinutes,
    field === 'long' ? Number(input.value) : store.longBreakMinutes,
    field === 'rounds' ? Number(input.value) : store.roundsBeforeLongBreak,
    field === 'auto' ? input.checked : store.autoStartBreak,
  )
}

async function forgetTopic(name: string) {
  try {
    savedTopics.value = (await authApi.forgetFocusTopic(name)).data
  } catch {
    targetError.value = '移除失败，请稍后重试'
  }
}

function onCustomInput(e: Event) {
  store.setCustom(Number((e.target as HTMLInputElement).value) || 1)
}

function onReset() {
  if (!store.hasActiveSession) return
  confirmReset.value = true
}

function doReset() {
  confirmReset.value = false
  interruptNotice.value = ''
  store.reset()
}

function onInterrupt() {
  if (!store.hasActiveSession || interrupting.value) return
  confirmInterrupt.value = true
}

async function doInterrupt() {
  if (interrupting.value) return
  confirmInterrupt.value = false
  interrupting.value = true
  interruptNotice.value = ''
  try {
    const saved = await store.interrupt()
    interruptNotice.value = saved
      ? `已保存 ${Math.max(1, Math.round(saved.duration_seconds / 60))} 分钟，计入今日与本周。`
      : '本轮不足 1 秒，已结束。'
    await Promise.all([loadSummary(), loadDash()])
  } catch {
    interruptNotice.value = store.lastError || '保存失败，请重试。'
  } finally {
    interrupting.value = false
  }
}

function goReview() {
  router.push('/review')
}

function goStats() {
  router.push('/stats')
}

/** 完成峰值：刷新汇总 + 检查新解锁成就 */
watch(
  () => store.celebrating,
  async (on) => {
    if (!on) return
    await Promise.all([loadSummary(), loadDash()])
    newBadge.value = null
    try {
      const fresh = new Set((dash.value?.achievements ?? []).filter((a) => a.unlocked).map((a) => a.name))
      const born = (dash.value?.achievements ?? []).find((a) => a.unlocked && !unlockedRef.value.has(a.name))
      unlockedRef.value = fresh
      if (born) newBadge.value = born
    } catch {
      /* 成就检查失败不阻塞庆祝 */
    }
  },
)

function takeRest() {
  store.dismissCelebration()
  store.startBreak()
}

function again() {
  if (store.pendingSave) { void store.finish(); return }
  store.dismissCelebration()
  store.startNextFocus()
}

async function loadSummary() {
  try {
    summary.value = (await focusApi.summary()).data
  } catch {
    /* 汇总失败不阻塞页面 */
  }
}
async function loadDue() {
  dueError.value = false
  try {
    const res = await reviewApi.queue()
    dueCount.value = res.data.remaining_today
    needsRepair.value = res.data.needs_repair
  } catch {
    dueError.value = true
  }
}
async function loadDecks() {
  try {
    decks.value = (await decksApi.list()).data
  } catch {
    /* 卡组加载失败不阻塞专注 */
  }
}
/** 一次 dashboard：统计卡数据 + 成就基线（庆祝时对比出「这轮刚解锁」） */
async function loadDash() {
  try {
    dash.value = (await statsApi.dashboard()).data
    unlockedRef.value = new Set(dash.value.achievements.filter((a) => a.unlocked).map((a) => a.name))
  } catch {
    /* 忽略，卡片回落到 focus/summary 口径 */
  }
}

onMounted(() => {
  if (!store.hasActiveSession && typeof route.query.task === 'string' && route.query.task.trim()) {
    targetChoice.value = '__custom__'
    customTarget.value = route.query.task.trim().slice(0, 120)
  }
  loadSummary()
  loadDue()
  loadDecks()
  loadDash()
  authApi.focusTopics().then((res) => { savedTopics.value = res.data }).catch(() => {})
})
</script>

<style scoped>
/* 专注工作区：主计时器、侧边设置、底部概览 */
.focus-page { min-height: calc(100vh - 56px); }
.focus-inner { max-width: 1140px; margin: 0 auto; }
.fp-header { margin-bottom: 20px; }
.fp-title-row { display: flex; align-items: center; gap: 10px; margin: 0; }
.fp-title-tomato { width: 40px; height: 40px; flex: none; transform: rotate(5deg); }
.fp-header .h-sub { margin-top: 4px; }
.fp-workspace { display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(315px, 1fr); gap: 14px; align-items: start; }
.fp-main-card, .fp-side-card, .fp-reminder, .fp-stats {
  background: var(--paper); border: 2px solid var(--line); border-radius: 22px;
  box-shadow: var(--pop-sm);
}
.fp-main-card { min-width: 0; height: 620px; padding: 23px 28px 26px; display: flex; flex-direction: column; position: relative; }
.fp-card-heading { display: flex; align-items: center; gap: 10px; position: relative; z-index: 1; }
.fp-card-heading h2 { margin: 0; font-size: 17px; font-weight: 800; color: var(--ink); }
.fp-heading-mark { width: 5px; height: 23px; flex: none; border-radius: 99px; background: var(--orange); }
.fp-timer-note { position: absolute; right: 20px; top: 13px; display: flex; align-items: center; gap: 3px; color: var(--ink3); font-size: 11px; font-weight: 700; }
.fp-timer-note img { width: 47px; height: 47px; }
.fp-timer-zone { width: min(340px, 100%); aspect-ratio: 1; margin: 0; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); display: grid; place-items: center; }
.fp-blob { position: absolute; border-radius: 50%; z-index: 0; pointer-events: none; }
.fp-blob-a { width: 80px; height: 80px; left: -26px; top: 47%; background: var(--ham-l); opacity: .55; }
.fp-blob-b { width: 130px; height: 130px; right: -13px; bottom: 3%; background: var(--grape-l); opacity: .6; }
.fp-timer { width: 100%; aspect-ratio: 1; position: relative; z-index: 1; cursor: pointer; border-radius: 50%; }
.fp-timer::before {
  content: ''; position: absolute; inset: -10px; border: 2px solid var(--orange);
  border-radius: 50%; opacity: 0; pointer-events: none;
}
.fp-ring { display: block; width: 100%; height: 100%; transform: rotate(-90deg); }
.fp-trk { stroke: var(--orange-l); }
.fp-bar { stroke: url(#focusGrad); stroke-linecap: round; transition: stroke-dashoffset 1s linear; }
.fp-timer.running { animation: focusBreath 3s ease-in-out infinite; }
.fp-timer.running::before { animation: focusHalo 3s ease-in-out infinite; }
@keyframes focusBreath {
  0%, 100% { transform: scale(1); filter: drop-shadow(0 0 2px color-mix(in srgb, var(--orange) 15%, transparent)); }
  50% { transform: scale(1.025); filter: drop-shadow(0 0 18px color-mix(in srgb, var(--orange) 38%, transparent)); }
}
@keyframes focusHalo {
  0%, 100% { opacity: .08; transform: scale(.985); }
  50% { opacity: .42; transform: scale(1.035); }
}
.fp-timer.completed { animation: donePop .55s var(--ease-out-quart); }
@keyframes donePop { 40% { transform: scale(1.04); } }
@media (prefers-reduced-motion: reduce) {
  .fp-timer.running { animation: none; filter: drop-shadow(0 0 7px color-mix(in srgb, var(--orange) 30%, transparent)); }
  .fp-timer.running::before { animation: none; opacity: .3; }
}
.fp-mid { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; flex-direction: column; pointer-events: none; }
.fp-tm { color: var(--ink); font-size: clamp(52px, 5vw, 76px); font-weight: 850; letter-spacing: -3px; line-height: 1; font-variant-numeric: tabular-nums; }
.fp-tm.long { font-size: clamp(40px, 4.3vw, 62px); letter-spacing: -2px; }
.fp-tl { color: var(--ink2); font-size: 14px; font-weight: 700; margin-top: 12px; }
.fp-controls { display: flex; align-items: center; justify-content: center; gap: 12px; flex-wrap: wrap; margin-top: auto; }
.fp-btn-warm { display: inline-flex; align-items: center; justify-content: center; gap: 10px; padding: 13px 30px; border: 2px solid var(--line); border-radius: 15px; background: var(--orange); color: var(--onfill); box-shadow: var(--pop-sm); font: inherit; font-size: 16px; font-weight: 800; cursor: pointer; transition: transform .2s var(--ease), box-shadow .2s var(--ease); }
.fp-btn-warm:hover { transform: translateY(-2px); box-shadow: var(--pop); }
.fp-btn-warm .icon { width: 18px; height: 18px; }
.fp-cta { min-width: 185px; }
.fp-interrupt { padding: 10px 14px; border: 1.5px solid var(--line); border-radius: 12px; background: var(--paper); color: var(--ink); font: inherit; font-size: 14px; font-weight: 750; cursor: pointer; }
.fp-interrupt:hover:not(:disabled) { background: var(--orange-l); }
.fp-interrupt:disabled { opacity: .5; cursor: not-allowed; }
.fp-interrupt-notice { margin: 12px 0 0; color: var(--ink2); font-size: 13px; text-align: center; }
.fp-reset { display: inline-flex; align-items: center; gap: 7px; padding: 10px 3px; background: transparent; border: 0; color: var(--ink2); font: inherit; font-size: 14px; font-weight: 750; cursor: pointer; }
.fp-reset .icon { width: 17px; height: 17px; }
.fp-reset:disabled { opacity: .5; cursor: not-allowed; }
.fp-side { min-width: 0; display: flex; flex-direction: column; gap: 14px; }
.fp-side-card { padding: 22px 22px 20px; position: relative; min-width: 0; }
.fp-task-card { min-height: 139px; }
.fp-corner-mascot { position: absolute; right: 17px; top: 2px; width: 62px; height: 62px; pointer-events: none; }
.fp-intent { display: flex; align-items: center; gap: 10px; margin-top: 22px; padding: 12px 13px; min-width: 0; border: 1.5px solid var(--hairline); border-radius: 13px; background: var(--cream); }
.fp-intent.off { opacity: .55; }
.fp-intent-current { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; font-weight: 750; }
.fp-intent-custom { width: 100%; margin-top: 9px; padding: 10px 12px; border: 1.5px solid var(--hairline); border-radius: 11px; background: var(--paper); color: var(--ink); font: inherit; font-size: 13px; outline: none; }
.fp-intent-custom:focus { border-color: var(--orange); }
.fp-intent-error { margin: 7px 0 0; color: var(--berry); font-size: 12px; font-weight: 700; }
.fp-topic-history { margin-top: 9px; display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.fp-topic-history > span { width: 100%; color: var(--ink3); font-size: 11px; }
.fp-topic-history-row { display: inline-flex; max-width: 100%; align-items: center; border: 1px solid var(--hairline); border-radius: 99px; background: var(--cream); }
.fp-topic-history-row button { padding: 3px 7px; border: 0; background: transparent; color: var(--ink2); font: inherit; font-size: 11px; cursor: pointer; }
.fp-topic-history-row button:first-child { max-width: 150px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.fp-topic-history-row button:last-child { color: var(--berry); }
.fp-intent-book { width: 19px; height: 19px; color: var(--orange-d); flex: none; }
.fp-intent-select { flex: 1; min-width: 0; appearance: none; border: 0; outline: 0; background: transparent; color: var(--ink); font: inherit; font-size: 13px; font-weight: 750; cursor: pointer; text-overflow: ellipsis; }
.fp-intent-select:disabled { cursor: not-allowed; }
.fp-intent-chev { width: 15px; height: 15px; color: var(--ink3); flex: none; }
.fp-mode-card { flex: 1; min-height: 350px; padding: 18px 20px; }
.fp-modes { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-top: 16px; }
.fp-mode { position: relative; min-width: 0; display: flex; align-items: center; gap: 8px; padding: 8px 10px; min-height: 60px; text-align: left; border: 1.5px solid var(--hairline); border-radius: 14px; background: var(--cream); color: var(--ink); font: inherit; cursor: pointer; transition: transform .2s var(--ease), border-color .2s var(--ease); }
.fp-mode:hover:not(:disabled) { transform: translateY(-2px); border-color: var(--orange); }
.fp-mode.on { background: var(--orange-l); border-color: var(--orange-d); }
.fp-mode.deep { background: var(--mint-l); }
.fp-mode.nap { background: var(--grape-l); }
.fp-mode.countup { grid-column: 1 / -1; min-height: 58px; background: var(--warm); }
.fp-mode.countup .fp-mode-icon { color: var(--mint-d); }
.fp-mode:disabled { opacity: .55; cursor: not-allowed; }
.fp-mode-icon { width: 36px; height: 36px; flex: none; border-radius: 50%; display: grid; place-items: center; background: var(--paper); color: var(--orange-d); }
.fp-mode.deep .fp-mode-icon { color: var(--mint-d); }
.fp-mode.nap .fp-mode-icon { color: var(--grape-d); }
.fp-mode-icon svg, .fp-mode-icon img { width: 27px; height: 27px; }
.fp-mode-icon .icon { width: 22px; height: 22px; }
.fp-mode-copy { display: flex; flex-direction: column; min-width: 0; }
.fp-mode-copy b { font-size: 14px; white-space: nowrap; }
.fp-mode-copy small { margin-top: 3px; color: var(--ink2); font-size: 11px; white-space: nowrap; }
.fp-mode-check { position: absolute; right: 9px; top: 9px; width: 15px; height: 15px; color: var(--orange-d); }
.fp-cycle-settings { margin-top: 12px; border-top: 1px dashed var(--hairline); padding-top: 10px; color: var(--ink2); font-size: 12px; }
.fp-cycle-settings summary { cursor: pointer; font-weight: 800; color: var(--ink); }
.fp-cycle-settings summary span { color: var(--orange-d); margin-left: 5px; }
.fp-cycle-fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-top: 12px; }
.fp-cycle-fields label { display: flex; align-items: center; gap: 4px; font-weight: 700; }
.fp-cycle-fields input[type=number] { width: 40px; border: 1px solid var(--hairline); border-radius: 6px; padding: 3px; background: var(--paper); color: var(--ink); text-align: center; font: inherit; }
.fp-cycle-fields .fp-auto-break { grid-column: 1 / -1; }
.fp-quick-start { display: none; }
.custom-row { display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 14px; }
.step-btn { width: 32px; height: 32px; border: 1.5px solid var(--line); border-radius: 9px; background: var(--paper); color: var(--ink); font: inherit; font-size: 19px; cursor: pointer; }
.custom-input { width: 58px; padding: 5px 7px; text-align: center; border: 1.5px solid var(--line); border-radius: 9px; background: var(--cream); color: var(--ink); font: inherit; font-weight: 800; }
.custom-unit { color: var(--ink2); font-size: 12px; }
.fp-reminder { min-width: 0; display: flex; align-items: center; gap: 10px; padding: 13px 14px; background: var(--orange-l); }
.fp-reminder.err { background: var(--berry-l); }
.fp-reminder-icon { width: 34px; height: 34px; flex: none; border-radius: 10px; display: grid; place-items: center; background: var(--paper); color: var(--orange-d); }
.fp-reminder-icon .icon { width: 18px; height: 18px; }
.fp-reminder-text { display: flex; flex-direction: column; gap: 2px; min-width: 0; flex: 1; }
.fp-reminder-text b { font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.fp-reminder-text small { color: var(--ink2); font-size: 11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.fp-reminder-link { display: inline-flex; align-items: center; gap: 2px; flex: none; background: var(--paper); color: var(--orange-d); border: 1.5px solid var(--orange-d); border-radius: 99px; padding: 6px 9px; font: inherit; font-size: 11px; font-weight: 800; cursor: pointer; }
.fp-reminder-link .icon { width: 12px; height: 12px; }
.fp-reminder-mascot { width: 35px; height: 35px; flex: none; margin-left: -4px; }
.fp-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); margin-top: 14px; padding: 11px 8px; }
.fp-stat { display: flex; align-items: center; gap: 10px; min-width: 0; padding: 7px 14px; border: 0; border-right: 1.5px solid var(--hairline); background: transparent; color: var(--ink); text-align: left; font: inherit; cursor: pointer; }
.fp-stat:last-child { border-right: 0; }
.fp-stat:hover { background: var(--warm); border-radius: 12px; }
.fp-stat-ic { width: 42px; height: 42px; flex: none; display: grid; place-items: center; border: 1.5px solid var(--orange); border-radius: 50%; background: var(--orange-l); color: var(--orange-d); }
.fp-stat-ic.mint { border-color: var(--mint); background: var(--mint-l); color: var(--mint-d); }
.fp-stat-ic.grape { border-color: var(--grape); background: var(--grape-l); color: var(--grape-d); }
.fp-stat-ic svg, .fp-stat-ic img { width: 30px; height: 30px; }
.fp-stat-ic .icon { width: 21px; height: 21px; }
.fp-stat-copy { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.fp-stat-copy b { font-size: 12px; white-space: nowrap; }
.fp-stat-copy b small { color: var(--ink3); font-size: 10px; }
.fp-stat-copy strong { font-size: 26px; font-variant-numeric: tabular-nums; line-height: 1; }
.fp-stat-copy strong small { margin-left: 3px; font-size: 11px; font-weight: 700; color: var(--ink2); }
.fp-dots { margin-left: auto; display: flex; gap: 4px; align-self: flex-end; padding-bottom: 4px; }
.fp-dots i { width: 7px; height: 7px; border-radius: 50%; background: var(--orange-l); }
.fp-dots i.on { background: var(--orange); }
.fp-stat-progress { margin-left: auto; align-self: flex-end; width: 56px; height: 7px; border-radius: 99px; background: var(--mint-l); overflow: hidden; }
.fp-stat-progress i { display: block; height: 100%; border-radius: inherit; background: var(--mint); }
.fp-week { margin-left: auto; align-self: flex-end; display: flex; align-items: flex-end; gap: 3px; height: 22px; }
.fp-week span { width: 5px; min-height: 4px; border-radius: 3px; background: var(--grape-l); }
.fp-week span.today { background: var(--grape); }
@media (max-width: 1000px) {
  .fp-workspace { grid-template-columns: minmax(0, 1fr) minmax(290px, .8fr); }
  .fp-main-card { padding: 20px; }
  .fp-timer-zone { width: min(300px, 100%); }
  .fp-mode { gap: 6px; padding: 8px; }
  .fp-mode-icon { width: 34px; height: 34px; }
  .fp-mode-icon svg, .fp-mode-icon img { width: 25px; height: 25px; }
}
@media (max-width: 790px) {
  .fp-workspace { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .fp-side { display: contents; }
  .fp-task-card { order: 1; }
  .fp-mode-card { order: 2; }
  .fp-quick-start { order: 3; grid-column: 1 / -1; display: block; padding: 11px; }
  .fp-main-card { order: 4; grid-column: 1 / -1; height: auto; min-height: 540px; }
  .fp-reminder { order: 5; grid-column: 1 / -1; }
}
@media (max-width: 600px) {
  .fp-header { margin-bottom: 14px; }
  .fp-workspace { gap: 12px; }
  .fp-main-card { min-height: 520px; padding: 18px; }
  .fp-timer-note { display: none; }
  .fp-timer-zone { width: min(275px, 100%); }
  .fp-tm { font-size: 58px; }
  .fp-workspace { grid-template-columns: 1fr; }
  .fp-task-card, .fp-mode-card { grid-column: 1; }
  .fp-mode-card { order: 2; }
  .fp-side-card { padding: 18px; }
  .fp-stats { grid-template-columns: 1fr; padding: 4px 12px; }
  .fp-stat { border-right: 0; border-bottom: 1px solid var(--hairline); padding: 11px 4px; }
  .fp-stat:last-child { border-bottom: 0; }
}
@media (max-width: 380px) {
  .fp-main-card { min-height: 590px; }
  .fp-timer-zone { width: min(240px, calc(100% - 32px)); }
  .fp-modes { gap: 7px; }
  .fp-mode-copy b { font-size: 12px; }
  .fp-mode-copy small { font-size: 10px; }
}

/* ── 完成庆祝弹层 ── */
.celebrate-mask {
  position: fixed; inset: 0; z-index: 100;
  background: rgba(10, 7, 4, 0.45);
  display: flex; align-items: center; justify-content: center; padding: 20px;
}
.celebrate-card {
  position: relative; width: min(400px, 100%);
  padding: 30px 26px 24px; text-align: center; box-shadow: var(--pop-lg);
}
.celebrate-tomato { width: 74px; height: 74px; margin: 0 auto 10px; animation: tomatoPop 0.6s var(--ease-spring) both; }
.celebrate-tomato img { width: 100%; height: 100%; }
@keyframes tomatoPop {
  0% { transform: scale(0) rotate(-20deg); }
  60% { transform: scale(1.15) rotate(6deg); }
  100% { transform: scale(1) rotate(0); }
}
.celebrate-card h2 { font-size: 21px; font-weight: 800; letter-spacing: -0.4px; }
.celebrate-sub { color: var(--ink2); font-size: 13.5px; margin-top: 6px; font-weight: 650; }
.celebrate-badge {
  display: inline-flex; align-items: center; gap: 7px;
  margin-top: 12px; padding: 7px 14px; border-radius: 999px;
  background: var(--ham-l); border: 2px solid var(--line); box-shadow: var(--pop-sm);
  font-size: 13px; font-weight: 800; color: var(--ham-d);
  animation: badgeIn 0.5s var(--ease-out-quart) 0.25s both;
}
.celebrate-badge .icon { width: 15px; height: 15px; }
@keyframes badgeIn {
  from { opacity: 0; transform: translateY(10px) rotate(-3deg); }
  to { opacity: 1; transform: none; }
}
.celebrate-actions { display: flex; gap: 10px; justify-content: center; margin-top: 18px; flex-wrap: wrap; }
.celebrate-close {
  margin-top: 14px; font-family: inherit; font-size: 12.5px; font-weight: 700;
  color: var(--ink3); background: none; border: none; cursor: pointer;
}
.celebrate-close:hover { color: var(--ink); }

/* 弹层进出场 */
.celebrate-enter-active { transition: opacity 0.25s var(--ease-out); }
.celebrate-enter-active .celebrate-card { animation: cardIn 0.4s var(--ease-out-quart) both; }
.celebrate-leave-active { transition: opacity 0.18s ease; }
.celebrate-enter-from, .celebrate-leave-to { opacity: 0; }
@keyframes cardIn {
  from { opacity: 0; transform: translateY(18px) scale(0.96); }
  to { opacity: 1; transform: none; }
}
</style>
