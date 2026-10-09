<template>
  <div>
    <!-- Hero -->
    <div class="hero rise">
      <div class="hero-inner">
        <div style="flex:1;min-width:260px">
          <span class="streak">
            <svg class="icon" style="width:14px;height:14px;color:var(--orange-d)"><use href="#i-flame" /></svg>
            连续 {{ streakDays }} 天
          </span>
          <h1 class="hero-h1">{{ greet }}，{{ heroTitle }}</h1>
          <p class="hero-p">{{ dueCount > 0 ? `先复习今天到期的 ${dueCount} 张卡，再安排一段专注时间。` : needsRepair > 0 ? `有 ${needsRepair} 张卡需要补全答案，修好后就能继续复习。` : '今天没有到期卡片，可以读点新内容或开始专注。' }}</p>
          <div class="row gap12 wrap" style="margin-top:16px">
            <button class="btn btn-lg" style="background:var(--paper)" @click="router.push(needsRepair > 0 && dueCount === 0 ? '/decks' : '/review')">
              <svg class="icon"><use href="#i-play" /></svg>{{ needsRepair > 0 && dueCount === 0 ? '补全卡片' : '开始复习' }}
            </button>
            <button class="btn btn-lg btn-soft" @click="router.push('/focus')">
              <svg class="icon"><use href="#i-timer" /></svg>进入专注
            </button>
          </div>
        </div>
        <div class="hero-ring">
          <svg width="150" height="150" viewBox="0 0 150 150">
            <circle cx="75" cy="75" r="64" fill="none" stroke="var(--hero-track)" stroke-width="14" />
            <circle cx="75" cy="75" r="64" fill="none" stroke="var(--hero-ink)" stroke-width="14"
                    stroke-linecap="round" :stroke-dasharray="CIRC" :stroke-dashoffset="ringOffset"
                    style="transition:stroke-dashoffset 1.1s var(--ease-out)" />
          </svg>
          <div class="ring-txt">
            <div class="num">{{ ringPct }}%</div>
            <div class="lbl">今日复习进度</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 统计卡 -->
    <div class="stat-grid">
      <div class="card stat rise" v-for="s in statCards" :key="s.label">
        <div class="lab"><svg class="icon" :style="{ color: s.color }"><use :href="s.icon" /></svg>{{ s.label }}</div>
        <div class="val" :style="{ color: s.color }">{{ s.value }}</div>
        <div class="foot">{{ s.foot }}</div>
      </div>
    </div>
    <div v-if="overviewError" class="stats-error">
      卡片和复习统计加载失败。<button @click="loadTodayStats">重试</button>
    </div>

    <div class="two-col">
      <!-- 左列 -->
      <div>
        <div class="card pad rise">
          <div class="row between" style="margin-bottom:4px">
            <div>
              <div class="h-sec">今日计划</div>
              <div class="h-sub">点一下圆圈完成，右边可删</div>
            </div>
            <span class="chip chip-m">{{ doneCount }} / {{ plans.length }} 已完成</span>
          </div>
          <div style="margin-top:8px">
            <div v-for="t in plans" :key="t.id" class="task" :class="{ done: t.done }">
              <div class="tick" @click="toggleTask(t)"><svg class="icon"><use href="#i-check" /></svg></div>
              <div style="flex:1;min-width:0" @click="toggleTask(t)">
                <div class="t-name">{{ t.title }}</div>
              </div>
              <button class="task-focus" :aria-label="`专注于 ${t.title}`" title="专注于这项计划" @click="router.push({ path: '/focus', query: { task: t.title } })"><svg class="icon"><use href="#i-timer" /></svg></button>
              <button class="task-del" aria-label="删除这一项" @click="removeTask(t)"><svg class="icon"><use href="#i-close" /></svg></button>
            </div>
            <div v-if="!plans.length" class="muted" style="font-size:13px">还没有计划，下面加一条。</div>
          </div>
          <div class="row gap8" style="margin-top:10px">
            <input v-model="newPlanTitle" class="plan-input" placeholder="加一条计划，比如「背 20 个词」"
                   @keyup.enter="addTask" aria-label="新计划标题" />
            <button class="btn btn-primary" style="padding:8px 14px;font-size:13.5px" :disabled="!newPlanTitle.trim()" @click="addTask">添加</button>
          </div>
        </div>

        <div class="card pad rise insight" style="margin-top:14px">
          <div class="row gap8" style="margin-bottom:6px">
            <svg class="icon" style="color:var(--orange-d)"><use href="#i-spark" /></svg>
            <div class="h-sec">今天的学习建议</div>
          </div>
          <div class="insight-row">
            <div class="ic" style="background:var(--orange-l);color:var(--orange-d)">
              <svg class="icon"><use href="#i-clock" /></svg>
            </div>
            <div>
              <div class="tt">选择适合自己的复习时间</div>
              <div class="dd">到期卡会出现在复习队列；完成后再读新资料，节奏更清楚。</div>
            </div>
          </div>
          <div class="insight-row">
            <div class="ic" style="background:var(--grape-l);color:var(--grape-d)">
              <svg class="icon"><use href="#i-brain" /></svg>
            </div>
            <div>
              <div class="tt">{{ dueCount > 0 ? `当前有 ${dueCount} 张到期卡` : needsRepair > 0 ? `${needsRepair} 张卡待补全` : '今天没有到期卡' }}</div>
              <div class="dd">{{ dueCount > 0 ? '可以先完成复习，再决定是否添加新卡。' : needsRepair > 0 ? '去卡组补上答案，这些卡才会进入复习队列。' : '想继续积累？从内容库打开资料，划词制作新卡。' }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右列 -->
      <div>
        <div class="card pad rise checkin-card">
          <div class="row between">
            <div>
              <div class="row gap8">
                <svg class="icon" style="color:var(--orange-d)"><use href="#i-calendar" /></svg>
                <span class="h-sec">每日签到</span>
              </div>
              <div class="h-sub">连续 {{ checkin.streak }} 天 · 累计 {{ checkin.total_days }} 天</div>
            </div>
            <button class="btn" :class="checkin.checked ? 'btn-checked' : 'btn-primary'" :disabled="checking" @click="doCheckin">
              {{ checking ? '…' : checkin.checked ? '已签到' : '签到' }}
            </button>
          </div>
          <div v-if="checkinNotice" class="checkin-notice">{{ checkinNotice }}</div>
          <div v-else-if="nextCheckinAch" class="checkin-next">还差 {{ nextCheckinAch.left }} 天解锁「{{ nextCheckinAch.name }}」</div>
          <div v-else class="checkin-next">签到成就全解锁 🎉</div>
        </div>

        <div class="card pad rise" style="margin-top:14px">
          <div class="h-sec" style="margin-bottom:8px">刚囤进来的</div>
          <div v-if="recentLoading" class="muted recent-message">正在加载最近内容…</div>
          <div v-else-if="recentItems.length" class="recent-list">
            <button v-for="item in recentItems" :key="`${item.kind}-${item.id}`" class="recent-row" @click="onOpenRecent(item)">
              <div class="recent-ic" :style="recentMeta(item).style">
                <svg class="icon" style="width:18px;height:18px"><use :href="recentMeta(item).icon" /></svg>
              </div>
              <div class="recent-content">
                <div class="recent-name">{{ item.title }}</div>
                <div class="recent-detail">{{ recentMeta(item).sub }} · {{ formatRecentTime(item.createdAt) }}</div>
              </div>
              <svg class="icon recent-arrow"><use href="#i-arrow" /></svg>
            </button>
            <button v-if="recentError" class="recent-retry" @click="loadRecent">部分内容暂时没加载到，点此重试</button>
          </div>
          <div v-else-if="recentError" class="recent-empty">
            <div class="muted">最近内容加载失败，请重试。</div>
            <button class="btn" @click="loadRecent">重新加载</button>
          </div>
          <div v-else class="recent-empty">
            <div class="muted">这里会显示最近上传的资料和新建的卡片。</div>
            <div class="row gap8 wrap">
              <button class="btn btn-primary" @click="router.push('/library')">上传第一份资料</button>
              <button class="btn" @click="router.push('/decks')">新建卡组</button>
            </div>
          </div>
        </div>

        <div class="card pad rise" style="margin-top:14px;background:linear-gradient(160deg,var(--ham-l),var(--paper))">
          <div class="row gap12" style="align-items:flex-start">
            <div style="width:40px;height:40px;border-radius:13px;background:var(--orange-l);color:var(--orange-d);border:2px solid var(--line);display:flex;align-items:center;justify-content:center;flex:none">
              <svg class="icon" style="width:19px;height:19px"><use href="#i-spark" /></svg>
            </div>
            <div style="flex:1">
              <div class="h-sec">小提醒</div>
              <p class="muted" style="font-size:13.5px;margin-top:6px;line-height:1.7">
                在阅读器里选中一段文字，几秒就能变成一张会按时回来的卡片。去试试划词成卡。
              </p>
              <button class="btn btn-primary" style="margin-top:12px;width:100%" @click="router.push('/library')">
                <svg class="icon"><use href="#i-arrow" /></svg>去处理
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { cardsApi } from '@/api/cards'
import { checkinApi } from '@/api/checkin'
import { filesApi } from '@/api/files'
import { focusApi } from '@/api/focus'
import { plansApi } from '@/api/plans'
import { reviewApi } from '@/api/review'
import { statsApi } from '@/api/stats'
import { useUserStore } from '@/stores/user'
import type { Card, CheckinStatus, FileItem, PlanTask } from '@/types/api'

const router = useRouter()
const userStore = useUserStore()

const CIRC = 2 * Math.PI * 64
const todayQueue = ref(0)
const todayReviews = ref(0)
const totalCards = ref(0)
const todayFocusH = ref('0h')
const overviewLoading = ref(true)
const overviewError = ref(false)
const streakDays = ref(1)
const recentFiles = ref<FileItem[]>([])
const recentCards = ref<Card[]>([])
const recentLoading = ref(true)
const recentError = ref(false)
const dueCount = ref(0)
const needsRepair = ref(0)

// ── 今日计划 ──
const plans = ref<PlanTask[]>([])
const newPlanTitle = ref('')
const doneCount = computed(() => plans.value.filter((t) => t.done).length)

// ── 每日签到 ──
const checkin = ref<CheckinStatus>({ checked: false, streak: 0, total_days: 0, month_days: 0, new_achievements: [] })
const checking = ref(false)
const checkinNotice = ref('')
const nextCheckinAch = computed(() => {
  const c = checkin.value
  if (c.streak < 7) return { name: '七日之约', left: 7 - c.streak }
  if (c.month_days < 21) return { name: '月满勤', left: 21 - c.month_days }
  if (c.total_days < 100) return { name: '百日常客', left: 100 - c.total_days }
  return null
})

const greet = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '早上好'
  if (h < 18) return '下午好'
  return '晚上好'
})
const heroTitle = computed(() =>
  todayQueue.value > 0 ? `还有 ${todayQueue.value} 张卡没啃完` : needsRepair.value > 0 ? `还有 ${needsRepair.value} 张卡待补全` : '今天的卡都啃完了'
)

const ringPct = computed(() => {
  const total = todayReviews.value + todayQueue.value
  return total > 0 ? Math.round((todayReviews.value / total) * 100) : 0
})
const ringOffset = computed(() => CIRC * (1 - ringPct.value / 100))

const statCards = computed(() => [
  { icon: '#i-flame', label: '连续天数', value: String(streakDays.value), foot: '天', color: 'var(--orange-d)' },
  { icon: '#i-clock', label: '今日专注', value: todayFocusH.value, foot: '目标 3h', color: 'var(--grape-d)' },
  { icon: '#i-brain', label: '囤了多少', value: overviewLoading.value ? '…' : overviewError.value ? '—' : totalCards.value.toLocaleString(), foot: '张卡片', color: 'var(--ham-d)' },
  { icon: '#i-target', label: '今日已复习', value: overviewLoading.value ? '…' : overviewError.value ? '—' : String(todayReviews.value), foot: '次', color: 'var(--mint-d)' },
])

type RecentItem =
  | { kind: 'file'; id: string; title: string; createdAt: string; file: FileItem }
  | { kind: 'card'; id: string; title: string; createdAt: string; card: Card }

const recentItems = computed<RecentItem[]>(() => [
  ...recentFiles.value.map((file): RecentItem => ({ kind: 'file', id: file.id, title: file.name, createdAt: file.created_at, file })),
  ...recentCards.value.map((card): RecentItem => ({ kind: 'card', id: card.id, title: cardPreview(card.front), createdAt: card.created_at, card })),
].sort((a, b) => Date.parse(b.createdAt) - Date.parse(a.createdAt)).slice(0, 2))

function cardPreview(front: string) {
  const firstLine = front.split(/\r?\n/).map((line) => line.trim()).find((line) => line && !/^[|:\-\s]+$/.test(line)) || ''
  const plain = firstLine
    .replace(/\{\{c\d+::([^}:]+)(?:::[^}]+)?\}\}/g, '$1')
    .replace(/!?\[([^\]]*)\]\([^)]+\)/g, '$1')
    .replace(/^[#>*\-\d.)\s]+/, '')
    .replace(/[|*_`]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  return plain.length > 36 ? `${plain.slice(0, 36)}…` : plain || '未命名卡片'
}

function recentMeta(item: RecentItem) {
  if (item.kind === 'card') return { icon: '#i-cards', style: { background: 'var(--mint-l)', color: 'var(--mint-d)' }, sub: '卡片' }
  const file = item.file
  const sub = file.doc_status === 'done' ? '资料' : file.doc_status === 'failed' ? '资料 · 解析失败' : '资料 · 处理中'
  return { icon: file.ext === 'pdf' ? '#i-doc' : '#i-book', style: { background: 'var(--grape-l)', color: 'var(--grape-d)' }, sub }
}
function formatRecentTime(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '刚刚'
  const days = Math.floor((Date.now() - date.getTime()) / 86400000)
  if (days <= 0) return '今天'
  if (days === 1) return '昨天'
  return `${date.getMonth() + 1}月${date.getDate()}日`
}
function onOpenRecent(item: RecentItem) {
  if (item.kind === 'card') return router.push({ path: '/decks', query: { deck: item.card.deck_id } })
  if (item.file.doc_status === 'done' && item.file.doc_id) return router.push({ path: '/reader', query: { doc: item.file.doc_id } })
  return router.push({ path: '/library', query: { file: item.file.id } })
}

async function loadRecent() {
  recentLoading.value = true
  const [files, cards] = await Promise.allSettled([filesApi.list({ all: true }), cardsApi.list({ limit: 10 })])
  recentFiles.value = files.status === 'fulfilled' ? files.value.data.filter((file) => !file.is_dir) : []
  recentCards.value = cards.status === 'fulfilled' ? cards.value.data.items : []
  recentError.value = files.status === 'rejected' || cards.status === 'rejected'
  recentLoading.value = false
}

/* ── 今日计划 CRUD ── */
async function loadPlans() {
  try {
    plans.value = (await plansApi.list()).data
  } catch {
    /* 忽略 */
  }
}
async function addTask() {
  const title = newPlanTitle.value.trim()
  if (!title) return
  try {
    const created = (await plansApi.create(title)).data
    plans.value.push(created)
    newPlanTitle.value = ''
  } catch {
    /* 忽略 */
  }
}
async function toggleTask(t: PlanTask) {
  try {
    const updated = (await plansApi.update(t.id, { done: !t.done })).data
    t.done = updated.done
  } catch {
    /* 忽略 */
  }
}
async function removeTask(t: PlanTask) {
  try {
    await plansApi.remove(t.id)
    plans.value = plans.value.filter((x) => x.id !== t.id)
  } catch {
    /* 忽略 */
  }
}

/* ── 每日签到 ── */
async function loadCheckin() {
  try {
    checkin.value = (await checkinApi.status()).data
    streakDays.value = checkin.value.streak || 1
  } catch {
    /* 忽略 */
  }
}
async function doCheckin() {
  if (checking.value || checkin.value.checked) return
  checking.value = true
  checkinNotice.value = ''
  try {
    const res = (await checkinApi.checkin()).data
    checkin.value = res
    if (res.new_achievements.length) {
      checkinNotice.value = `🎉 新成就「${res.new_achievements.join('、')}」解锁！`
    }
  } catch {
    /* 忽略 */
  } finally {
    checking.value = false
  }
}

async function loadTodayStats() {
  overviewLoading.value = true
  overviewError.value = false
  const [queue, overview, focus] = await Promise.allSettled([
    reviewApi.queue(), statsApi.overview(), focusApi.summary(),
  ])
  if (queue.status === 'fulfilled') {
    todayQueue.value = queue.value.data.remaining_today
    dueCount.value = queue.value.data.remaining_today
    needsRepair.value = queue.value.data.needs_repair
  }
  if (overview.status === 'fulfilled') {
    totalCards.value = overview.value.data.total_cards
    todayReviews.value = overview.value.data.today_reviews
  } else {
    overviewError.value = true
  }
  overviewLoading.value = false
  if (focus.status === 'fulfilled') {
    const seconds = focus.value.data.today_seconds
    todayFocusH.value = seconds >= 3600
      ? (seconds / 3600).toFixed(1) + 'h'
      : Math.round(seconds / 60) + 'min'
  }
}

onMounted(() => {
  loadPlans()
  loadCheckin()
  loadRecent()
  loadTodayStats()
})
</script>

<style scoped>
.hero {
  position: relative;
  overflow: hidden;
  padding: 20px 26px;
  background: linear-gradient(150deg, var(--hero-a), var(--hero-b));
  color: var(--hero-ink);
  border-radius: var(--r-lg);
  border: 2.5px solid var(--line);
  box-shadow: var(--pop);
}
.hero::after {
  content: '';
  position: absolute;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: var(--hero-hl);
  top: -120px;
  right: -80px;
}
.hero-inner {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}
.hero-h1 { margin-top: 8px; font-size: clamp(1.2rem, 2.4vw, 1.5rem); font-weight: 800; letter-spacing: -0.5px; line-height: 1.3; }
.hero-p { color: var(--hero-sub); font-size: 13.5px; margin-top: 5px; font-weight: 500; }
.hero .btn { padding: 10px 20px; font-size: 14px; }

/* 类名不能叫 .ring：会被 UnoCSS presetUno 当成 Tailwind 的 ring 工具类，生成 3px 蓝色 box-shadow */
.hero-ring { position: relative; width: 130px; height: 130px; flex: none; }
.hero-ring svg { transform: rotate(-90deg); width: 130px; height: 130px; }
.ring-txt { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.ring-txt .num { font-size: 27px; font-weight: 800; line-height: 1; color: var(--hero-ink); font-variant-numeric: tabular-nums; }
.ring-txt .lbl { font-size: 11.5px; font-weight: 800; color: var(--hero-sub); margin-top: 3px; }

.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 12px; }
@media (max-width: 760px) {
  .stat-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .hero-inner { flex-wrap: nowrap; gap: 8px; }
  .hero-inner > div:first-child { min-width: 0 !important; }
  .hero-ring, .hero-ring svg { width: 104px; height: 104px; }
  .hero-ring .num { font-size: 23px; }
}
@media (max-width: 440px) {
  .hero-ring { display: none; }
  .hero .btn { padding: 8px 12px; font-size: 12px; }
}
.stat { padding: 11px 14px; }
.stat .lab { font-size: 12px; color: var(--ink2); font-weight: 700; display: flex; align-items: center; gap: 6px; }
.stat .lab .icon { width: 14px; height: 14px; }
.stat .val { font-size: 22px; font-variant-numeric: tabular-nums; font-weight: 800; letter-spacing: -0.5px; margin-top: 4px; line-height: 1; }
.stat .foot { font-size: 11.5px; color: var(--ink3); margin-top: 3px; }
.stats-error { margin-top: 8px; color: var(--berry); font-size: 12px; }
.stats-error button { border: 0; padding: 0; background: none; color: inherit; font: inherit; font-weight: 800; text-decoration: underline; cursor: pointer; }

.two-col { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr); gap: 12px; margin-top: 12px; align-items: start; }
.two-col > div { min-width: 0; }
@media (max-width: 920px) { .two-col { grid-template-columns: minmax(0, 1fr); } }
.pad { padding: 14px 16px; }
.h-sec { font-size: 15px; font-weight: 800; }
.h-sub { color: var(--ink2); font-size: 12.5px; margin-top: 2px; }

.task { padding: 8px 12px; gap: 11px; }
.insight-row { padding: 8px 0; }

/* 今日计划：删除按钮 + 新建输入 */
.task-del {
  flex: none; width: 26px; height: 26px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  color: var(--ink3); background: none; border: 2px solid transparent; cursor: pointer;
  opacity: 0; transition: all 0.2s var(--ease);
}
.task-focus { width: 28px; height: 28px; flex: none; display: grid; place-items: center; border: 1px solid var(--hairline); border-radius: 8px; background: var(--cream); color: var(--orange-d); cursor: pointer; }
.task-focus .icon { width: 15px; height: 15px; }
.task-focus:hover { background: var(--orange-l); }
.task:hover .task-del { opacity: 1; }
.task-del:hover { color: var(--berry); border-color: var(--line); background: var(--paper); }
.task-del .icon { width: 14px; height: 14px; }
.plan-input {
  flex: 1; min-width: 0; font-family: inherit; font-size: 13.5px;
  color: var(--ink); background: var(--cream); border: 2.5px solid var(--line);
  border-radius: 11px; padding: 8px 12px; outline: none;
}
.plan-input:focus { border-color: var(--orange); }

/* 每日签到卡 */
.checkin-card { background: linear-gradient(160deg, var(--ham-l), var(--paper)); }
.btn-checked { background: var(--mint); color: var(--onfill); border-color: var(--line); cursor: default; }
.checkin-notice {
  margin-top: 10px; padding: 8px 12px; border-radius: 11px;
  background: var(--ham-l); border: 2px solid var(--line); box-shadow: var(--pop-sm);
  font-size: 13px; font-weight: 800; color: var(--ham-d);
  animation: riseIn 0.4s var(--ease-out-quart) both;
}
.checkin-next { margin-top: 9px; font-size: 12.5px; font-weight: 700; color: var(--ink3); }
.checkin-next b { color: var(--orange-d); }

.recent-row {
  display: flex; align-items: center; gap: 11px; padding: 6px 8px;
  width: 100%; min-width: 0; overflow: hidden; box-sizing: border-box; text-align: left; background: transparent; color: var(--ink); font: inherit;
  border-radius: 14px; border: 2px solid transparent; cursor: pointer;
  transition: all 0.28s var(--ease);
}
.recent-row:hover { background: var(--warm); border-color: var(--line); }
.recent-row:focus-visible { outline: 3px solid var(--orange); outline-offset: 2px; }
.recent-list { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.recent-content { flex: 1; min-width: 0; overflow: hidden; }
.recent-detail { font-size: 12px; color: var(--ink3); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.recent-arrow { width: 15px; height: 15px; color: var(--ink3); flex: none; }
.recent-empty { display: flex; flex-direction: column; align-items: flex-start; gap: 12px; padding: 7px 0 2px; font-size: 13px; }
.recent-message { font-size: 13px; padding: 8px 0; }
.recent-retry { border: 0; background: none; color: var(--orange-d); font: inherit; font-size: 12px; font-weight: 700; cursor: pointer; text-align: left; }
.recent-ic {
  width: 36px; height: 36px; border-radius: 12px; border: 2px solid var(--line);
  display: flex; align-items: center; justify-content: center; flex: none;
}
.recent-name { font-size: 13.5px; font-weight: 750; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
