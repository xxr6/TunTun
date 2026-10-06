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
          <p class="hero-p">你的记忆黄金时段是晚上 8 点到 10 点，先把今天到期的啃掉</p>
          <div class="row gap12 wrap" style="margin-top:16px">
            <button class="btn btn-lg" style="background:var(--paper)" @click="router.push('/review')">
              <svg class="icon"><use href="#i-play" /></svg>开始复习
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
            <div class="lbl">今日计划</div>
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
            <div class="h-sec">为你适配的学习节奏</div>
          </div>
          <div class="insight-row">
            <div class="ic" style="background:var(--orange-l);color:var(--orange-d)">
              <svg class="icon"><use href="#i-clock" /></svg>
            </div>
            <div>
              <div class="tt">黄金复习时段：20:00 - 22:00</div>
              <div class="dd">这个时段你的正确率比其他时段高 11%，新卡已经被优先安排在这里</div>
            </div>
          </div>
          <div class="insight-row">
            <div class="ic" style="background:var(--grape-l);color:var(--grape-d)">
              <svg class="icon"><use href="#i-brain" /></svg>
            </div>
            <div>
              <div class="tt">今天负载{{ dueCount > 20 ? '偏重' : '偏轻' }}，{{ dueCount > 20 ? '按队列慢慢啃' : '可以加量' }}</div>
              <div class="dd">当前到期 {{ dueCount }} 张{{ dueCount > 20 ? '，先啃最旧的一批' : '，现在多拆几张新卡不会噎着' }}</div>
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
          <div class="row between" style="margin-bottom:10px">
            <div class="h-sec">刚囤进来的</div>
            <button class="btn btn-ghost" style="padding:6px 13px;font-size:13px" @click="router.push('/library')">
              全部<svg class="icon"><use href="#i-arrow" /></svg>
            </button>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px">
            <div v-for="(f, i) in recentFiles" :key="f.id" class="recent-row" @click="onOpenFile(f)">
              <div class="recent-ic" :style="{ background: fileMeta(i, f).bg, color: fileMeta(i, f).fg }">
                <svg class="icon" style="width:18px;height:18px"><use :href="fileMeta(i, f).icon" /></svg>
              </div>
              <div style="flex:1;min-width:0">
                <div class="recent-name">{{ f.name }}</div>
                <div class="muted" style="font-size:12px">{{ fileMeta(i, f).sub }}</div>
              </div>
            </div>
            <div v-if="!recentFiles.length" class="muted" style="font-size:13px">还没有文件，去内容库上传一份。</div>
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
import type { CheckinStatus, FileItem, PlanTask } from '@/types/api'

const router = useRouter()
const userStore = useUserStore()

const CIRC = 2 * Math.PI * 64
const todayQueue = ref(0)
const todayReviews = ref(0)
const totalCards = ref(0)
const todayFocusH = ref('0h')
const streakDays = ref(1)
const recentFiles = ref<FileItem[]>([])
const dueCount = ref(0)

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
  todayQueue.value > 0 ? `还有 ${todayQueue.value} 张卡没啃完` : '今天的卡都啃完了'
)

const ringPct = computed(() => {
  const total = todayReviews.value + todayQueue.value
  return total > 0 ? Math.round((todayReviews.value / total) * 100) : 0
})
const ringOffset = computed(() => CIRC * (1 - ringPct.value / 100))

const statCards = computed(() => [
  { icon: '#i-flame', label: '连续天数', value: String(streakDays.value), foot: '天', color: 'var(--orange-d)' },
  { icon: '#i-clock', label: '今日专注', value: todayFocusH.value, foot: '目标 3h', color: 'var(--grape-d)' },
  { icon: '#i-brain', label: '囤了多少', value: totalCards.value.toLocaleString(), foot: '张卡片', color: 'var(--ham-d)' },
  { icon: '#i-target', label: '今日已复习', value: String(todayReviews.value), foot: '次', color: 'var(--mint-d)' },
])

const FILE_COLORS = ['var(--grape-l)|var(--grape-d)|#i-doc', 'var(--orange-l)|var(--orange-d)|#i-book', 'var(--mint-l)|var(--mint-d)|#i-code']
function fileMeta(i: number, f: FileItem) {
  const [bg, fg, icon] = (FILE_COLORS[i % 3]).split('|')
  const sub = f.doc_status === 'done' ? '已解析，可划词成卡' : f.doc_status === 'failed' ? '解析失败，可重试' : '解析中…'
  return { bg, fg, icon, sub }
}
function onOpenFile(f: FileItem) {
  if (f.doc_id) router.push(`/reader/${f.doc_id}`)
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

onMounted(async () => {
  loadPlans()
  loadCheckin()
  try {
    const [q, o, focus, files] = await Promise.all([
      reviewApi.queue(), statsApi.overview(), focusApi.summary(), filesApi.list(),
    ])
    todayQueue.value = q.data.remaining_today
    dueCount.value = q.data.remaining_today
    totalCards.value = o.data.total_cards
    todayReviews.value = o.data.today_reviews
    todayFocusH.value = focus.data.today_seconds >= 3600
      ? (focus.data.today_seconds / 3600).toFixed(1) + 'h'
      : Math.round(focus.data.today_seconds / 60) + 'min'
    recentFiles.value = files.data.filter((f) => !f.is_dir).slice(0, 3)
  } catch {
    /* 数据加载失败不阻塞渲染 */
  }
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
.stat { padding: 11px 14px; }
.stat .lab { font-size: 12px; color: var(--ink2); font-weight: 700; display: flex; align-items: center; gap: 6px; }
.stat .lab .icon { width: 14px; height: 14px; }
.stat .val { font-size: 22px; font-variant-numeric: tabular-nums; font-weight: 800; letter-spacing: -0.5px; margin-top: 4px; line-height: 1; }
.stat .foot { font-size: 11.5px; color: var(--ink3); margin-top: 3px; }

.two-col { display: grid; grid-template-columns: 1.35fr 1fr; gap: 12px; margin-top: 12px; align-items: start; }
@media (max-width: 920px) { .two-col { grid-template-columns: 1fr; } }
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
  border-radius: 14px; border: 2px solid transparent; cursor: pointer;
  transition: all 0.28s var(--ease);
}
.recent-row:hover { background: var(--warm); border-color: var(--line); }
.recent-ic {
  width: 36px; height: 36px; border-radius: 12px; border: 2px solid var(--line);
  display: flex; align-items: center; justify-content: center; flex: none;
}
.recent-name { font-size: 13.5px; font-weight: 750; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
