<template>
  <div class="focus-page">
    <div class="focus-inner">
    <div class="rise">
      <div class="h-page">专注</div>
      <div class="h-sub">开始之前，先看看有没有到期的卡没啃</div>
    </div>

    <!-- 到期卡提醒 -->
    <div class="card pad rise" style="margin-top:16px"
         :style="dueError ? 'background:var(--berry-l)' : 'background:var(--orange-l)'" @click="goReview">
      <div class="row gap12" style="cursor:pointer">
        <div style="width:40px;height:40px;border-radius:13px;background:var(--paper);border:2px solid var(--line);display:flex;align-items:center;justify-content:center;flex:none;color:var(--orange-d)">
          <svg class="icon" style="width:19px;height:19px"><use href="#i-cards" /></svg>
        </div>
        <div style="flex:1;text-align:left">
          <div class="due-t">
            {{ dueError ? '没连上，到期卡数未知' : dueCount > 0 ? `还有 ${dueCount} 张卡到期` : '今天没有到期的卡了' }}
          </div>
          <div class="muted due-s">
            {{ dueError ? '稍后再试，不影响专注' : dueCount > 0 ? '先花几分钟啃掉，专注效果会更好' : '可以安心开始专注了' }}
          </div>
        </div>
        <button class="btn btn-primary" style="padding:9px 16px;font-size:13.5px" @click.stop="goReview">去复习</button>
      </div>
    </div>

    <!-- 这一轮啃什么：可选绑定卡组，把「专注」和「囤卡」接上 -->
    <div class="rise">
      <div class="card deck-line" style="margin-top:16px">
        <div class="deck-line-t">
          <svg class="icon" style="width:15px;height:15px;color:var(--grape-d)"><use href="#i-target" /></svg>
          这一轮啃什么（可选）
        </div>
        <select v-model="deckId" class="deck-select" :disabled="store.hasActiveSession" aria-label="选择这一轮专注的卡组">
          <option :value="null">不指定，纯粹囤时间</option>
          <option v-for="d in decks" :key="d.id" :value="d.id">{{ d.name }}</option>
        </select>
      </div>
    </div>

    <!-- 模式切换 -->
    <div class="rise">
      <div class="mode-tabs" style="margin-top:20px" role="group" aria-label="专注模式">
        <button v-for="m in MODES" :key="m.key" class="mode-btn" :class="{ on: store.mode === m.key }"
                :disabled="store.hasActiveSession" :aria-pressed="store.mode === m.key"
                @click="store.setMode(m.key)">
          {{ m.label }}<small v-if="m.min">{{ m.min }}</small>
        </button>
      </div>
      <div v-if="store.mode === 'custom' && !store.hasActiveSession" class="custom-row rise">
        <button class="step-btn" aria-label="减少 1 分钟" @click="store.setCustom(store.customMinutes - 1)">−</button>
        <input class="custom-input" type="number" min="1" max="240" :value="store.customMinutes"
               aria-label="自定义专注分钟数" @change="onCustomInput" />
        <span class="custom-unit">分钟</span>
        <button class="step-btn" aria-label="增加 1 分钟" @click="store.setCustom(store.customMinutes + 1)">+</button>
      </div>
    </div>

    <!-- 计时器 -->
    <div class="timer rise" :class="{ running: store.running, completed: store.celebrating }">
      <svg viewBox="0 0 300 300" role="progressbar"
           :aria-valuemin="0" :aria-valuemax="store.total" :aria-valuenow="store.remaining"
           aria-label="专注倒计时">
        <defs>
          <linearGradient id="focusGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="var(--orange)" />
            <stop offset="100%" stop-color="var(--ham)" />
          </linearGradient>
        </defs>
        <circle class="trk" cx="150" cy="150" r="134" fill="none" stroke-width="16" />
        <circle class="bar" cx="150" cy="150" r="134" fill="none" stroke-width="16"
                :stroke-dasharray="CIRC" :stroke-dashoffset="dashOffset" />
        <!-- 秒针：随剩余时间顺时针扫过一圈，暂停时冻结 -->
        <g class="needle" :style="{ transform: `rotate(${needleAngle}deg)` }" aria-hidden="true">
          <line x1="150" y1="150" x2="252" y2="150" stroke="var(--line)" stroke-width="4" stroke-linecap="round" />
        </g>
        <circle class="needle-hub" cx="150" cy="150" r="7" fill="var(--orange)" stroke="var(--line)" stroke-width="3" aria-hidden="true" />
      </svg>
      <div class="mid">
        <div class="tm" :class="{ on: store.running }">{{ fmt(store.remaining) }}</div>
        <div class="tl" aria-live="polite">{{ statusText }}</div>
      </div>
    </div>

    <!-- 控制 -->
    <div class="row gap12 rise" style="justify-content:center">
      <button class="btn btn-primary btn-lg" @click="onToggle">
        <svg class="icon"><use :href="store.running ? '#i-pause' : '#i-play'" /></svg>
        <span>{{ store.running ? '暂停' : store.paused ? '继续' : '开始' }}</span>
      </button>
      <button class="btn btn-ghost btn-lg" :disabled="!store.hasActiveSession" @click="onReset">
        <svg class="icon"><use href="#i-refresh" /></svg>重置
      </button>
    </div>

    <!-- 番茄罐 + 专注统计 -->
    <div class="focus-stat rise">
      <div class="fs">
        <div class="v" style="color:var(--orange-d)">{{ summary.today_count }}</div>
        <div class="l">今日番茄</div>
        <div class="jar-row" aria-hidden="true">
          <svg v-for="i in jarCount" :key="i" class="tomato" :style="{ animationDelay: (i * 60) + 'ms' }" viewBox="0 0 16 16">
            <circle cx="8" cy="9.5" r="6" fill="var(--berry)" stroke="var(--line)" stroke-width="1.4" />
            <path d="M8 4.5c-2.2-1.6-.6-3.2 0-3.8" fill="none" stroke="var(--mint-d)" stroke-width="1.6" stroke-linecap="round" />
            <circle cx="6.2" cy="8.4" r="1.1" fill="var(--berry-l)" stroke="none" />
          </svg>
          <span v-if="summary.today_count > 12" class="jar-more">+{{ summary.today_count - 12 }}</span>
        </div>
      </div>
      <div class="fs">
        <div class="v" style="color:var(--mint-d)">{{ fmtH(summary.today_seconds) }}</div>
        <div class="l">今日专注 · 目标 3h</div>
        <div class="goal-bar"><i :style="{ width: goalPct + '%' }"></i></div>
      </div>
      <div class="fs">
        <div class="v" style="color:var(--grape-d)">{{ fmtH(summary.week_seconds) }}</div>
        <div class="l">本周专注</div>
      </div>
    </div>
    </div>

    <!-- 完成庆祝弹层 -->
    <Transition name="celebrate">
      <div v-if="store.celebrating" class="celebrate-mask" role="dialog" aria-modal="true" aria-label="这一轮完成">
        <div class="card celebrate-card">
          <div class="celebrate-tomato" aria-hidden="true">
            <svg viewBox="0 0 64 64">
              <path d="M32 14c-5.5-4-1.5-8.5 0-9.5" fill="none" stroke="var(--mint-d)" stroke-width="4" stroke-linecap="round" />
              <path d="M26 6c-2.5 3-3.5 6-4 9" fill="none" stroke="var(--mint-d)" stroke-width="3.5" stroke-linecap="round" />
              <circle cx="32" cy="38" r="23" fill="var(--berry)" stroke="var(--line)" stroke-width="4" />
              <circle cx="24" cy="32" r="4.5" fill="var(--berry-l)" stroke="none" />
            </svg>
          </div>
          <h2>{{ store.lastResult ? '这一轮啃完了！' : '计时走完了，但记录没存上' }}</h2>
          <p class="celebrate-sub" aria-live="polite">
            <template v-if="store.lastResult">+1 番茄入罐 · 今天已经囤下 {{ summary.today_count }} 枚</template>
            <template v-else>{{ store.lastError || '稍后再试一次' }}</template>
          </p>
          <div v-if="newBadge" class="celebrate-badge">
            <svg class="icon"><use :href="newBadge.icon" /></svg>
            新成就「{{ newBadge.name }}」解锁！
          </div>
          <div class="celebrate-actions">
            <button class="btn btn-soft" @click="takeRest">
              <svg class="icon"><use href="#i-moon" /></svg>休息一下 · 打盹 5
            </button>
            <button class="btn btn-primary" @click="again">
              <svg class="icon"><use href="#i-play" /></svg>再来一轮
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
      message="走到的时长会记为一轮未完成，留着以后回顾。"
      confirm-text="重置"
      danger
      @confirm="doReset"
      @cancel="confirmReset = false"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { decksApi } from '@/api/decks'
import { focusApi } from '@/api/focus'
import { reviewApi } from '@/api/review'
import { statsApi } from '@/api/stats'
import { useFocusStore, type FocusMode } from '@/stores/focus'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import type { Deck, FocusSummary, StatsDashboard } from '@/types/api'

const router = useRouter()
const store = useFocusStore()

const MODES: { key: FocusMode; label: string; min: string }[] = [
  { key: 'pomodoro', label: '啃 25', min: '· 25 分钟' },
  { key: 'deep', label: '深啃 50', min: '· 50 分钟' },
  { key: 'nap', label: '打盹 5', min: '· 5 分钟' },
  { key: 'custom', label: '自定义', min: '' },
]

const decks = ref<Deck[]>([])
const deckId = ref<string | null>(null)
const summary = ref<FocusSummary>({ today_seconds: 0, week_seconds: 0, month_seconds: 0, today_count: 0 })
const dueCount = ref(0)
const dueError = ref(false)
const unlockedRef = ref<Set<string>>(new Set())
const newBadge = ref<StatsDashboard['achievements'][number] | null>(null)
const confirmReset = ref(false)

const CIRC = 2 * Math.PI * 134
const dashOffset = computed(() => CIRC * (1 - store.remaining / store.total))
/** 秒针角度：满时 0°，随剩余时间归零扫满一圈（暂停时冻结） */
const needleAngle = computed(() => (1 - store.remaining / store.total) * 360)
const goalPct = computed(() => Math.min(100, Math.round((summary.value.today_seconds / 10800) * 100)))
const jarCount = computed(() => Math.min(summary.value.today_count, 12))

const statusText = computed(() => {
  if (store.celebrating) return '这一轮完成，休息一下吧'
  if (store.running) return '专注中，别分心'
  if (store.paused) return '已暂停，随时继续'
  return '点击开始'
})

function fmt(s: number) {
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
}
function fmtH(s: number) {
  return s >= 3600 ? (s / 3600).toFixed(1) + 'h' : Math.round(s / 60) + 'min'
}

function onToggle() {
  if (!store.hasActiveSession) {
    // 把当前选择的卡组快照进这一轮会话
    store.deckId = deckId.value
    store.deckName = decks.value.find((d) => d.id === deckId.value)?.name ?? ''
  }
  store.toggle()
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
  store.reset()
}

function goReview() {
  router.push('/review')
}

/** 完成峰值：刷新汇总 + 检查新解锁成就 */
watch(
  () => store.celebrating,
  async (on) => {
    if (!on) return
    await loadSummary()
    newBadge.value = null
    try {
      const dash = (await statsApi.dashboard()).data
      const fresh = new Set(dash.achievements.filter((a) => a.unlocked).map((a) => a.name))
      const born = dash.achievements.find((a) => a.unlocked && !unlockedRef.value.has(a.name))
      unlockedRef.value = fresh
      if (born) newBadge.value = born
    } catch {
      /* 成就检查失败不阻塞庆祝 */
    }
  },
)

function takeRest() {
  store.dismissCelebration()
  store.setMode('nap')
  store.deckId = null
  store.deckName = ''
  store.startSession(null, '')
}

function again() {
  store.dismissCelebration()
  store.startSession(store.deckId, store.deckName)
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
/** 记一份成就基线：庆祝时对比出「这轮刚解锁」的成就 */
async function loadAchievementBaseline() {
  try {
    const dash = (await statsApi.dashboard()).data
    unlockedRef.value = new Set(dash.achievements.filter((a) => a.unlocked).map((a) => a.name))
  } catch {
    /* 忽略 */
  }
}

onMounted(() => {
  loadSummary()
  loadDue()
  loadDecks()
  loadAchievementBaseline()
})
</script>

<style scoped>
/* 与其他页面一致的三主题浅色底 */
.focus-page { position: relative; min-height: 100vh; }
.focus-inner { position: relative; z-index: 1; }

.pad { padding: 18px 20px; }

.due-t { font-size: 14px; font-weight: 800; }
.due-s { font-size: 12.5px; }

/* ── 卡组绑定行 ── */
.deck-line { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 18px; flex-wrap: wrap; }
.deck-line-t { display: flex; align-items: center; gap: 7px; font-size: 13.5px; font-weight: 750; }
.deck-select {
  font-family: inherit; font-size: 13.5px; font-weight: 700; color: var(--ink);
  background: var(--cream); border: 2.5px solid var(--line); border-radius: 11px;
  padding: 7px 11px; max-width: 320px; outline: none;
}
.deck-select:focus-visible { outline: 2.5px solid var(--line); outline-offset: 2px; }
.deck-select:disabled { opacity: 0.6; }

/* ── 模式切换 ── */
.mode-tabs { display: inline-flex; gap: 5px; padding: 5px; background: var(--warm); border: 2.5px solid var(--line); border-radius: 999px; }
.mode-btn {
  display: inline-flex; align-items: baseline; gap: 4px;
  padding: 8px 18px; border-radius: 999px; font-size: 13.5px; font-weight: 750;
  color: var(--ink2); background: none; border: none; cursor: pointer;
  font-family: inherit; transition: all 0.3s var(--ease);
}
.mode-btn small { font-size: 10.5px; font-weight: 650; color: var(--ink3); }
.mode-btn.on { background: var(--paper); color: var(--ink); box-shadow: var(--pop-sm); border: 2px solid var(--line); }
.mode-btn:disabled { cursor: not-allowed; opacity: 0.55; }
.mode-btn:disabled.on { box-shadow: none; }

/* ── 自定义时长 ── */
.custom-row { display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 12px; }
.step-btn {
  width: 34px; height: 34px; border-radius: 11px; font-size: 18px; font-weight: 800; line-height: 1;
  color: var(--ink); background: var(--paper); border: 2.5px solid var(--line); box-shadow: var(--pop-sm);
  cursor: pointer; font-family: inherit; transition: transform 0.15s var(--ease-out-quart);
}
.step-btn:active { transform: translate(2px, 2px); box-shadow: none; }
.custom-input {
  width: 64px; text-align: center; font-family: inherit; font-size: 16px; font-weight: 800;
  color: var(--ink); background: var(--cream); border: 2.5px solid var(--line); border-radius: 11px;
  padding: 6px 8px; font-variant-numeric: tabular-nums;
}
.custom-unit { font-size: 13px; font-weight: 700; color: var(--ink2); }

/* ── 计时器 ── */
.timer { position: relative; width: 300px; height: 300px; margin: 20px auto 8px; }
.timer svg { transform: rotate(-90deg); }
.trk { stroke: var(--hair); }
.bar {
  stroke: url(#focusGrad);
  stroke-linecap: round;
  transition: stroke-dashoffset 1s linear;
}
/* 秒针：平滑扫动，暂停时角度不再推进（冻结） */
.needle { transition: transform 0.3s linear; transform-origin: 150px 150px; }
.needle-hub { transform-box: fill-box; transform-origin: center; }
.timer.running .needle-hub { animation: hubTick 1s var(--ease) infinite; }
@keyframes hubTick {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.18); }
}
/* 运行中：环外圈微光呼吸 */
.timer.running { animation: ringGlow 2.4s ease-in-out infinite; }
@keyframes ringGlow {
  0%, 100% { filter: drop-shadow(0 0 0 transparent); }
  50% { filter: drop-shadow(0 0 14px rgba(255, 139, 74, 0.35)); }
}
/* 完成：整体轻脉冲，表示「这一轮干完了」 */
.timer.completed { animation: donePop 0.55s var(--ease-out-quart); }
@keyframes donePop {
  0% { transform: scale(1); }
  40% { transform: scale(1.045); }
  100% { transform: scale(1); }
}

.mid { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.tm { font-size: 58px; font-weight: 800; letter-spacing: -2px; line-height: 1; font-variant-numeric: tabular-nums; color: var(--ink); transition: color 0.3s var(--ease); }
.tm.on { color: var(--orange); }
/* 状态文案：--ink2 保证三主题对比度达标（原 --ink3 仅 2.7:1） */
.tl { font-size: 13px; color: var(--ink2); margin-top: 10px; font-weight: 700; }

.btn-lg { padding: 12px 24px; font-size: 15px; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; box-shadow: none; }
.btn:disabled:active { transform: none; }

/* ── 番茄罐 + 统计 ── */
.focus-stat { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 22px; }
@media (max-width: 560px) { .focus-stat { grid-template-columns: 1fr; } }
.fs { background: var(--paper); border: 2.5px solid var(--line); border-radius: var(--r-md); padding: 14px; box-shadow: var(--pop-sm); }
.fs .v { font-size: 20px; font-weight: 800; font-variant-numeric: tabular-nums; }
.fs .l { font-size: 12px; color: var(--ink2); margin-top: 2px; font-weight: 700; }
.goal-bar { height: 8px; border-radius: 99px; background: var(--warm); border: 2px solid var(--hairline); margin-top: 8px; overflow: hidden; }
.goal-bar i { display: block; height: 100%; background: var(--mint); border-radius: 99px; transition: width 0.6s var(--ease-out-quart); }

/* 番茄罐：贴纸小番茄一字排开 */
.jar-row { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; min-height: 16px; }
.tomato { width: 16px; height: 16px; animation: tomatoIn 0.45s var(--ease-out-quart) both; }
@keyframes tomatoIn {
  from { opacity: 0; transform: translateY(-8px) scale(0.4); }
  to { opacity: 1; transform: none; }
}
.jar-more { font-size: 11px; font-weight: 800; color: var(--ink3); line-height: 16px; }

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
.celebrate-tomato svg { width: 100%; height: 100%; }
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
