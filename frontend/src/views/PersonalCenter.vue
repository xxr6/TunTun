<template>
  <div class="pc-page">
    <div class="pc-inner">
    <!-- 头部：标题 + 退出登录 -->
    <div class="rise pc-head">
      <div>
        <div class="h-page pc-title-row">
          个人中心
          <svg class="pc-title-tomato" viewBox="0 0 64 64" aria-hidden="true"><use href="#m-tomato" /></svg>
        </div>
        <div class="h-sub">管理你的账号信息与学习偏好</div>
      </div>
      <button class="pc-logout" @click="confirmLogout = true">
        <svg class="icon"><use href="#i-exit" /></svg>退出登录
      </button>
    </div>

    <!-- 资料卡 + 主题卡 -->
    <div class="pc-top rise">
      <div class="card pc-pad pc-profile">
        <div class="pc-id-row">
          <button class="pc-avatar" :disabled="avatarBusy" aria-label="更换头像" @click="avatarInput?.click()">
            <img v-if="avatarUrl" :src="avatarUrl" alt="我的头像" />
            <svg v-else viewBox="0 0 64 64" aria-hidden="true"><use href="#m-tomato" /></svg>
            <span class="pc-avatar-edit" aria-hidden="true"><svg class="icon"><use href="#i-cam" /></svg></span>
          </button>
          <input ref="avatarInput" type="file" accept="image/png,image/jpeg,image/webp" style="display:none" @change="onAvatarPicked" />
          <div class="pc-id-tx">
            <div class="pc-name-row">
              <template v-if="!nameEditing">
                <span class="pc-name">{{ user?.username }}</span>
                <button class="pc-icon-btn" aria-label="修改名字" @click="startName">
                  <svg class="icon"><use href="#i-pen" /></svg>
                </button>
              </template>
              <template v-else>
                <input v-model="nameDraft" class="pc-name-input" maxlength="32" aria-label="新名字" @keyup.enter="saveName" />
                <button class="pc-mini-btn ok" aria-label="保存名字" @click="saveName"><svg class="icon"><use href="#i-check" /></svg></button>
                <button class="pc-mini-btn" aria-label="取消修改" @click="nameEditing = false"><svg class="icon"><use href="#i-close" /></svg></button>
              </template>
            </div>
            <div class="pc-tagline">让知识成为可复用的资产</div>
            <div v-if="nameErr || avatarErr" class="pc-err">{{ nameErr || avatarErr }}</div>
          </div>
        </div>

        <div class="pc-id-meta">
          <span class="pc-meta"><svg class="icon"><use href="#i-buddy" /></svg>学习者 · Lv.{{ level }}</span>
          <i class="pc-meta-div" aria-hidden="true"></i>
          <span class="pc-meta"><svg class="icon"><use href="#i-calendar" /></svg>加入 {{ joinDays }} 天</span>
          <i class="pc-meta-div" aria-hidden="true"></i>
          <span class="pc-meta"><svg class="icon"><use href="#i-flame" /></svg>连续签到 {{ checkin.streak }} 天</span>
        </div>

        <div class="pc-tz">
          <svg class="icon" aria-hidden="true"><use href="#i-clock" /></svg>
          <span class="pc-tz-label">时区</span>
          <select v-model="timezone" class="pc-tz-select" aria-label="时区" @change="saveTimezone">
            <option v-for="z in TIMEZONES" :key="z.value" :value="z.value">{{ z.label }}</option>
          </select>
          <span v-if="tzSaved" class="chip chip-m">已保存</span>
        </div>
      </div>

      <div class="card pc-pad pc-theme-card">
        <div class="h-sec">主题</div>
        <div class="pc-theme-sub">选择你喜欢的界面风格</div>
        <div class="pc-theme-now">
          <svg viewBox="0 0 64 64" aria-hidden="true"><use href="#m-tomato" /></svg>
          <span>当前主题：{{ THEME_META[themeIndex]?.label }}</span>
        </div>
        <div class="pc-themes">
          <button v-for="(m, i) in THEME_META" :key="m.key" class="pc-theme" :class="{ on: themeIndex === i }"
                  :aria-label="'切换到' + m.label" :aria-pressed="themeIndex === i" @click="setThemeByIndex(i)">
            <img :src="m.icon" alt="" />{{ m.label }}
          </button>
        </div>
        <div class="pc-theme-hint muted">也可以按 Shift + T 快速循环。</div>
      </div>
    </div>

    <!-- 专注四卡 -->
    <div class="pc-focus rise">
      <div v-for="c in focusCards" :key="c.key" class="pc-fc" :style="{ '--ac': c.ac, '--acl': c.acl }">
        <div class="pc-fc-h">
          <span class="pc-fc-ic" aria-hidden="true"><svg class="icon"><use :href="c.icon" /></svg></span>
          {{ c.label }}
        </div>
        <div class="pc-fc-v">{{ c.value }}<small>{{ c.unit }}</small></div>
        <div class="pc-fc-goal">
          <template v-if="c.goalKey">
            <template v-if="goalEditing === c.goalKey">
              <input v-model="goalDraft" class="pc-goal-input" type="number" step="0.5" min="0.2" :aria-label="'新的' + c.label + '目标（小时）'" @keyup.enter="saveGoal(c.goalKey)" />
              <span class="pc-goal-unit">小时</span>
              <button class="pc-mini-btn ok" aria-label="保存目标" @click="saveGoal(c.goalKey)"><svg class="icon"><use href="#i-check" /></svg></button>
              <button class="pc-mini-btn" aria-label="取消" @click="goalEditing = null"><svg class="icon"><use href="#i-close" /></svg></button>
            </template>
            <template v-else>
              <span>目标 {{ fmtGoal(c.goal) }} · {{ c.goalLabel }}</span>
              <button class="pc-goal-edit" :aria-label="'修改' + c.label + '目标'" @click="startGoal(c.goalKey!)">
                <svg class="icon"><use href="#i-pen" /></svg>
              </button>
            </template>
          </template>
          <template v-else>{{ c.sub }}</template>
        </div>
        <div class="pc-fc-bar" aria-hidden="true"><i :style="{ width: c.pct + '%' }"></i></div>
      </div>
    </div>

    <section id="my-badges" class="card pc-pad pc-badges rise" aria-labelledby="my-badges-title">
      <div class="pc-sec-h">
        <svg class="icon" aria-hidden="true"><use href="#i-star" /></svg>
        <h2 id="my-badges-title">我的徽章</h2>
        <span class="chip chip-o">{{ ownedBadges.length }} 枚已获得</span>
        <button class="pc-link pc-sec-right" @click="router.push('/stats#badge-title')">查看全部 <svg class="icon"><use href="#i-chev" /></svg></button>
      </div>
      <div v-if="ownedBadges.length" class="pc-badge-grid">
        <div v-for="badge in ownedBadges" :key="badge.name" class="pc-owned-badge">
          <img :src="badgeArt[badge.name]" :alt="`${badge.name}徽章`" loading="lazy" />
          <strong>{{ badge.name }}</strong>
          <small>{{ badge.group }} · {{ badge.rarity }}</small>
        </div>
      </div>
      <p v-else class="pc-empty">{{ dash ? '还没有获得徽章。去完成学习目标，第一枚很快就会到手。' : '正在加载徽章…' }}</p>
    </section>

    <!-- 底部两栏 -->
    <div class="pc-bottom rise">
      <div class="pc-col">
        <!-- 今日计划 -->
        <div class="card pc-pad">
          <div class="pc-sec-h">
            <svg class="icon" aria-hidden="true"><use href="#i-check" /></svg>
            今日计划
            <span class="chip chip-o">{{ planDone }} / {{ plans.length }} 已完成</span>
          </div>
          <div v-if="plans.length" class="pc-plan-list">
            <div v-for="t in plans" :key="t.id" class="task" :class="{ done: t.done }" @click="togglePlan(t)">
              <span class="tick"><svg class="icon"><use href="#i-check" /></svg></span>
              <span class="t-name">{{ t.title }}</span>
              <button class="pc-plan-del" aria-label="删除这条计划" @click.stop="delPlan(t)">
                <svg class="icon"><use href="#i-close" /></svg>
              </button>
            </div>
          </div>
          <p v-else class="pc-empty">还没有计划。点一下圆圈就算完成，下面的输入框随时加一条。</p>
          <div class="pc-plan-add">
            <input v-model="planDraft" maxlength="40" placeholder="比如「背 20 个词」" aria-label="新计划" @keyup.enter="addPlan" />
            <button class="pc-add-btn" @click="addPlan">添加</button>
          </div>
        </div>

        <!-- 为你定制的节奏 -->
        <div class="card pc-pad">
          <div class="pc-sec-h">
            <svg class="icon" aria-hidden="true"><use href="#i-spark" /></svg>
            为你定制的复习节奏
          </div>
          <button class="pc-rhythm" @click="router.push('/review')">
            <span class="pc-rhythm-ic a" aria-hidden="true"><svg class="icon"><use href="#i-tomato" /></svg></span>
            <span class="pc-rhythm-tx">
              <b>按你的节奏复习</b>
              <i>到期卡会进入复习队列，选择方便的时间完成即可</i>
            </span>
            <svg class="icon pc-chev" aria-hidden="true"><use href="#i-chev" /></svg>
          </button>
          <button class="pc-rhythm" @click="router.push(dueCount > 0 ? '/review' : '/decks')">
            <span class="pc-rhythm-ic b" aria-hidden="true"><svg class="icon"><use href="#i-leaf" /></svg></span>
            <span class="pc-rhythm-tx">
              <b>{{ dueCount > 0 ? `今天负载刚好 · 还有 ${dueCount} 张卡` : '今天负载偏轻' }}</b>
              <i>{{ dueCount > 0 ? '先啃卡再专注，心里更踏实' : '适合多囤几张新卡，不会顾不过来' }}</i>
            </span>
            <svg class="icon pc-chev" aria-hidden="true"><use href="#i-chev" /></svg>
          </button>
        </div>
      </div>

      <div class="pc-col">
        <!-- 每日签到 -->
        <div class="card pc-pad">
          <div class="pc-sec-h">
            <svg class="icon" aria-hidden="true"><use href="#i-calendar" /></svg>
            每日签到
            <span v-if="checkin.checked" class="chip chip-m pc-sec-right">已签到</span>
            <button v-else class="pc-add-btn sm pc-sec-right" @click="doCheckin">去签到</button>
          </div>
          <div class="pc-check-row">
            <b>连续 {{ checkin.streak }} 天</b>
            <span>累计 {{ checkin.total_days }} 天</span>
          </div>
          <div class="pc-check-sub">
            月签 {{ checkin.month_days }} 天<template v-if="checkin.month_days < 7">，就差 {{ 7 - checkin.month_days }} 天即「七日之约」</template>
          </div>
        </div>

        <!-- 刚进来的 -->
        <div class="card pc-pad">
          <div class="pc-sec-h">
            <svg class="icon" aria-hidden="true"><use href="#i-folder" /></svg>
            刚进来的
            <button class="pc-link pc-sec-right" @click="router.push('/library')">
              全部 <svg class="icon"><use href="#i-chev" /></svg>
            </button>
          </div>
          <div v-if="recent.length" class="pc-recent">
            <button v-for="f in recent" :key="f.id" class="pc-recent-row" @click="router.push('/library')">
              <span class="pc-recent-ic" :class="f.cls" aria-hidden="true"><svg class="icon"><use :href="f.icon" /></svg></span>
              <span class="pc-recent-tx">
                <b>{{ f.name }}</b>
                <i>{{ f.sub }}</i>
              </span>
            </button>
          </div>
          <p v-else class="pc-empty">内容库还空着，去传第一个文件吧。</p>
        </div>

        <!-- 小提醒 -->
        <div class="card pc-pad pc-tip-card">
          <div class="pc-sec-h">
            <svg class="icon" aria-hidden="true"><use href="#i-spark" /></svg>
            小提醒
          </div>
          <div class="pc-tip-row">
            <p>{{ dueCount > 0 ? `在阅读或复习中随手划一句，攒下的未啃卡别过夜，抽几分钟清一清。` : '在阅读器里选中一段文字，一秒生成一张卡片。' }}</p>
            <button class="pc-add-btn" @click="router.push(dueCount > 0 ? '/review' : '/reader')">
              {{ dueCount > 0 ? '去处理' : '去试试' }}
            </button>
          </div>
        </div>
      </div>
    </div>
    </div>

    <ConfirmDialog
      :visible="confirmLogout"
      title="退出登录？"
      message="下次回来需要重新登录，本地复习进度不会丢。"
      confirm-text="退出"
      danger
      @confirm="doLogout"
      @cancel="confirmLogout = false"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/api/auth'
import { checkinApi } from '@/api/checkin'
import { filesApi } from '@/api/files'
import { plansApi } from '@/api/plans'
import { reviewApi } from '@/api/review'
import { statsApi } from '@/api/stats'
import { badgeArt } from '@/lib/badges'
import { useUserStore } from '@/stores/user'
import { useTheme, THEME_META } from '@/composables/useTheme'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import type { CheckinStatus, PlanTask, StatsDashboard } from '@/types/api'

const router = useRouter()
const userStore = useUserStore()
const { index: themeIndex, setThemeByIndex } = useTheme()

const user = computed(() => userStore.user)
const timezone = ref('Asia/Shanghai')
const tzSaved = ref(false)
const confirmLogout = ref(false)

const dash = ref<StatsDashboard | null>(null)
const ownedBadges = computed(() => dash.value?.achievements.filter((badge) => badge.unlocked) ?? [])
const checkin = ref<CheckinStatus>({ checked: false, streak: 0, total_days: 0, month_days: 0, new_achievements: [] })
const dueCount = ref(0)

/* ── 名字 ── */
const nameEditing = ref(false)
const nameDraft = ref('')
const nameErr = ref('')
function startName() {
  nameDraft.value = user.value?.username ?? ''
  nameErr.value = ''
  nameEditing.value = true
}
async function saveName() {
  const name = nameDraft.value.trim()
  if (!name) {
    nameErr.value = '名字不能为空'
    return
  }
  if (name === user.value?.username) {
    nameEditing.value = false
    return
  }
  try {
    const res = (await authApi.update({ username: name })).data
    userStore.user = res
    nameEditing.value = false
    nameErr.value = ''
  } catch (e) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    nameErr.value = typeof msg === 'string' ? msg : '这个名字用不了，换一个试试'
  }
}

/* ── 头像 ── */
const avatarInput = ref<HTMLInputElement | null>(null)
const avatarUrl = ref<string | null>(null)
const avatarBusy = ref(false)
const avatarErr = ref('')
async function loadAvatar() {
  try {
    const res = await authApi.avatarBlob()
    const url = URL.createObjectURL(res.data)
    if (avatarUrl.value) URL.revokeObjectURL(avatarUrl.value)
    avatarUrl.value = url
    avatarErr.value = ''
  } catch {
    avatarUrl.value = null // 没传过头像 → 默认番茄
  }
}
async function onAvatarPicked(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = '' // 允许连续选同一张
  if (!file) return
  if (file.size > 2 * 1024 * 1024) {
    avatarErr.value = '头像别超过 2MB'
    return
  }
  avatarBusy.value = true
  avatarErr.value = ''
  try {
    const r = (await authApi.uploadAvatar(file)).data
    if (user.value) {
      userStore.user = { ...user.value, settings: { ...user.value.settings, avatar_v: r.avatar_v, avatar_ext: r.avatar_ext } }
    }
    await loadAvatar()
  } catch (err) {
    const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    avatarErr.value = typeof msg === 'string' ? msg : '上传没成功，换张图试试'
  } finally {
    avatarBusy.value = false
  }
}

/* ── 等级 / 加入天数 ── */
const level = computed(() => Math.min(9, 1 + Math.floor((dash.value?.metrics.cards_total ?? 0) / 100)))
const joinDays = computed(() => {
  const t = user.value?.created_at
  if (!t) return 1
  return Math.max(1, Math.floor((Date.now() - new Date(t).getTime()) / 86400000))
})

/* ── 专注目标 ── */
type GoalKey = 'today' | 'week' | 'month'
const goals = ref({ today: 3 * 3600, week: 20 * 3600, month: 80 * 3600 })
const goalEditing = ref<GoalKey | null>(null)
const goalDraft = ref('')
const goalErr = ref('')

function fmtGoal(sec: number) {
  const h = sec / 3600
  return Number.isInteger(h) ? `${h}h` : `${h.toFixed(1)}h`
}
function startGoal(key: GoalKey) {
  goalDraft.value = (goals.value[key] / 3600).toFixed(1)
  goalErr.value = ''
  goalEditing.value = key
}
async function saveGoal(key: GoalKey) {
  const h = Number.parseFloat(goalDraft.value)
  if (!Number.isFinite(h) || h <= 0) {
    goalErr.value = '要大于 0'
    return
  }
  const sec = Math.round(h * 3600)
  try {
    goals.value = (await authApi.updateGoals({ [key]: sec })).data
    goalEditing.value = null
    goalErr.value = ''
    dash.value = (await statsApi.dashboard()).data // 目标变了，重算进度
  } catch (err) {
    const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    goalErr.value = typeof msg === 'string' ? msg : '这个目标设不了'
  }
}

/* ── 专注四卡 ── */
const focusCards = computed(() => {
  const f = dash.value?.focus
  const ai = dash.value?.metrics.ai_calls_month ?? 0
  return [
    {
      key: 'today', icon: '#i-tomato', ac: 'var(--orange-d)', acl: 'var(--ham-l)',
      label: '今日专注', value: ((f?.today.sec ?? 0) / 3600).toFixed(1), unit: 'h',
      goalKey: 'today' as GoalKey, goal: goals.value.today, goalLabel: '今日目标',
      pct: Math.min(100, Math.round(((f?.today.sec ?? 0) / goals.value.today) * 100)),
      sub: '',
    },
    {
      key: 'week', icon: '#i-calendar', ac: 'var(--mint-d)', acl: 'var(--mint-l)',
      label: '本周专注', value: ((f?.week.sec ?? 0) / 3600).toFixed(1), unit: 'h',
      goalKey: 'week' as GoalKey, goal: goals.value.week, goalLabel: '周目标',
      pct: Math.min(100, Math.round(((f?.week.sec ?? 0) / goals.value.week) * 100)),
      sub: '',
    },
    {
      key: 'month', icon: '#i-target', ac: 'var(--grape-d)', acl: 'var(--grape-l)',
      label: '本月专注', value: ((f?.month.sec ?? 0) / 3600).toFixed(1), unit: 'h',
      goalKey: 'month' as GoalKey, goal: goals.value.month, goalLabel: '月目标',
      pct: Math.min(100, Math.round(((f?.month.sec ?? 0) / goals.value.month) * 100)),
      sub: '',
    },
    {
      key: 'ai', icon: '#i-bolt', ac: 'var(--sky)', acl: 'var(--sky-l)',
      label: 'AI 用量', value: String(ai), unit: '次',
      goalKey: null, goal: 0, goalLabel: '', pct: Math.min(100, Math.round((ai / 500) * 100)),
      sub: '本月使用 · 免费额度限内',
    },
  ]
})

/* ── 今日计划 ── */
const plans = ref<PlanTask[]>([])
const planDraft = ref('')
const planDone = computed(() => plans.value.filter((t) => t.done).length)
async function addPlan() {
  const title = planDraft.value.trim()
  if (!title) return
  try {
    const res = (await plansApi.create(title)).data
    plans.value = [...plans.value, res]
    planDraft.value = ''
  } catch {
    /* 忽略 */
  }
}
async function togglePlan(t: PlanTask) {
  try {
    const res = (await plansApi.update(t.id, { done: !t.done })).data
    plans.value = plans.value.map((p) => (p.id === t.id ? res : p))
  } catch {
    /* 忽略 */
  }
}
async function delPlan(t: PlanTask) {
  try {
    await plansApi.remove(t.id)
    plans.value = plans.value.filter((p) => p.id !== t.id)
  } catch {
    /* 忽略 */
  }
}

/* ── 刚进来的 ── */
const recent = ref<{ id: string; name: string; icon: string; cls: string; sub: string }[]>([])
function fileSub(f: { doc_status: string | null }) {
  if (f.doc_status === 'done') return '已解析 · 可成卡'
  if (f.doc_status === 'processing') return '解析中…'
  if (f.doc_status === 'failed') return '解析失败'
  return '已上传'
}
async function loadRecent() {
  try {
    const list = (await filesApi.list()).data
      .filter((f) => !f.is_dir)
      .sort((a, b) => +new Date(b.created_at) - +new Date(a.created_at))
      .slice(0, 3)
    const palette = ['a', 'b', 'c'] // grape / orange / mint
    recent.value = list.map((f, i) => ({
      id: f.id,
      name: f.name,
      icon: f.ext === 'md' ? '#i-md' : '#i-doc',
      cls: palette[i % 3],
      sub: fileSub(f),
    }))
  } catch {
    /* 忽略 */
  }
}

/* ── 签到 / 时区 / 登出 ── */
async function doCheckin() {
  try {
    checkin.value = (await checkinApi.checkin()).data
    dash.value = (await statsApi.dashboard()).data
  } catch {
    /* 忽略 */
  }
}
async function saveTimezone() {
  try {
    const res = (await authApi.update({ timezone: timezone.value })).data
    userStore.user = res
    tzSaved.value = true
    setTimeout(() => (tzSaved.value = false), 1800)
  } catch {
    /* 忽略 */
  }
}
async function doLogout() {
  confirmLogout.value = false
  await userStore.logout()
  router.push('/login')
}

const TIMEZONES = [
  { value: 'Asia/Shanghai', label: '北京时间 (UTC+8)' },
  { value: 'Asia/Hong_Kong', label: '香港 (UTC+8)' },
  { value: 'Asia/Tokyo', label: '东京 (UTC+9)' },
  { value: 'Asia/Seoul', label: '首尔 (UTC+9)' },
  { value: 'Asia/Singapore', label: '新加坡 (UTC+8)' },
  { value: 'UTC', label: '协调世界时 (UTC)' },
  { value: 'Europe/London', label: '伦敦 (UTC+0/+1)' },
  { value: 'Europe/Paris', label: '巴黎 (UTC+1/+2)' },
  { value: 'America/New_York', label: '纽约 (UTC-5/-4)' },
  { value: 'America/Los_Angeles', label: '洛杉矶 (UTC-8/-7)' },
  { value: 'Australia/Sydney', label: '悉尼 (UTC+10/+11)' },
]

onMounted(async () => {
  timezone.value = user.value?.timezone || 'Asia/Shanghai'
  loadAvatar()
  const [d, c, g, q, p] = await Promise.allSettled([
    statsApi.dashboard(), checkinApi.status(), authApi.goals(), reviewApi.queue(), plansApi.list(),
  ])
  if (d.status === 'fulfilled') dash.value = d.value.data
  if (c.status === 'fulfilled') checkin.value = c.value.data
  if (g.status === 'fulfilled') goals.value = g.value.data
  if (q.status === 'fulfilled') dueCount.value = q.value.data.remaining_today
  if (p.status === 'fulfilled') plans.value = p.value.data
  loadRecent()
})
</script>

<style scoped>
.pc-page { position: relative; min-height: 100vh; }
.pc-inner { position: relative; z-index: 1; max-width: 1080px; margin: 0 auto; }
.pc-pad { padding: 18px 20px; }

/* ── 头部 ── */
.pc-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.pc-title-row { display: flex; align-items: center; gap: 10px; }
.pc-title-tomato { width: 34px; height: 34px; transform: rotate(6deg); animation: pcSway 3.4s ease-in-out infinite; transform-origin: 50% 90%; }
@keyframes pcSway {
  0%, 100% { transform: rotate(4deg) translateY(0); }
  50% { transform: rotate(-3deg) translateY(-2px); }
}
.pc-logout {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 9px 16px; border-radius: 999px; font-family: inherit;
  font-size: 13.5px; font-weight: 800; color: var(--orange-d);
  background: var(--paper); border: 2px solid color-mix(in srgb, var(--orange-d) 45%, transparent);
  box-shadow: 0 3px 0 color-mix(in srgb, var(--orange-d) 16%, transparent);
  cursor: pointer; transition: transform 0.15s var(--ease-out-quart), box-shadow 0.15s var(--ease-out-quart);
}
.pc-logout:hover { transform: translateY(-2px); }
.pc-logout:active { transform: translateY(2px); box-shadow: none; }
.pc-logout .icon { width: 15px; height: 15px; stroke-width: 2.2; }

/* ── 顶部两卡 ── */
.pc-top { display: grid; grid-template-columns: 1.25fr 1fr; gap: 14px; margin-top: 16px; align-items: stretch; }
@media (max-width: 880px) { .pc-top { grid-template-columns: 1fr; } }

/* 资料卡 */
.pc-id-row { display: flex; align-items: center; gap: 16px; }
.pc-avatar {
  position: relative; width: 68px; height: 68px; flex: none; padding: 0;
  border-radius: 22px; background: var(--cream); border: 2.5px solid var(--line);
  box-shadow: var(--pop-sm); cursor: pointer; overflow: hidden;
  display: flex; align-items: center; justify-content: center;
  transition: transform 0.2s var(--ease-out-quart);
}
.pc-avatar:hover { transform: rotate(-3deg) scale(1.03); }
.pc-avatar:disabled { opacity: 0.6; cursor: wait; }
.pc-avatar img { width: 100%; height: 100%; object-fit: cover; }
.pc-avatar > svg { width: 54px; height: 54px; }
.pc-avatar-edit {
  position: absolute; right: -1px; bottom: -1px; width: 24px; height: 24px;
  border-radius: 10px 0 0 0; background: var(--orange); border-top: 2px solid var(--line); border-left: 2px solid var(--line);
  color: var(--onfill); display: flex; align-items: center; justify-content: center;
}
.pc-avatar-edit .icon { width: 12px; height: 12px; stroke-width: 2.6; }
.pc-id-tx { flex: 1; min-width: 0; }
.pc-name-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.pc-name { font-size: 20px; font-weight: 800; letter-spacing: -0.4px; }
.pc-icon-btn {
  width: 28px; height: 28px; border-radius: 10px; padding: 0;
  border: 2px solid var(--hairline); background: var(--cream); color: var(--ink2);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all 0.2s var(--ease);
}
.pc-icon-btn:hover { color: var(--orange-d); border-color: var(--orange-d); transform: rotate(-8deg); }
.pc-icon-btn .icon { width: 13px; height: 13px; }
.pc-name-input {
  width: 200px; max-width: 100%; font-family: inherit; font-size: 16px; font-weight: 800;
  color: var(--ink); background: var(--cream); border: 2.5px solid var(--orange-d);
  border-radius: 11px; padding: 6px 10px; outline: none;
}
.pc-mini-btn {
  width: 30px; height: 30px; border-radius: 10px; padding: 0; flex: none;
  border: 2px solid var(--line); background: var(--paper); color: var(--ink2);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  box-shadow: var(--pop-sm); transition: all 0.15s var(--ease-out-quart);
}
.pc-mini-btn:active { transform: translate(2px, 2px); box-shadow: none; }
.pc-mini-btn.ok { background: var(--mint); color: var(--onfill); }
.pc-mini-btn .icon { width: 13px; height: 13px; stroke-width: 2.8; }
.pc-tagline { font-size: 13px; color: var(--ink2); margin-top: 3px; font-weight: 650; }
.pc-err { font-size: 12px; color: var(--berry); font-weight: 700; margin-top: 4px; }

.pc-id-meta {
  display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
  margin-top: 16px; padding: 10px 14px;
  background: var(--warm); border: 2px solid var(--hairline); border-radius: 14px;
}
.pc-meta { display: inline-flex; align-items: center; gap: 6px; font-size: 12.5px; font-weight: 750; color: var(--ink2); white-space: nowrap; }
.pc-meta .icon { width: 14px; height: 14px; color: var(--orange-d); }
.pc-meta-div { width: 2px; height: 16px; background: var(--hairline); border-radius: 2px; }

.pc-tz { display: flex; align-items: center; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
.pc-tz .icon { width: 14px; height: 14px; color: var(--ink3); }
.pc-tz-label { font-size: 12.5px; font-weight: 750; color: var(--ink2); }
.pc-tz-select {
  flex: 1; min-width: 180px; max-width: 320px; font-family: inherit; font-size: 13px; font-weight: 700;
  color: var(--ink); background: var(--cream); border: 2px solid var(--hairline);
  border-radius: 11px; padding: 6px 10px; outline: none;
}

/* 主题卡 */
.pc-theme-card { display: flex; flex-direction: column; }
.pc-theme-sub { font-size: 12.5px; color: var(--ink2); margin-top: 2px; font-weight: 650; }
.pc-theme-now {
  display: inline-flex; align-items: center; gap: 8px; align-self: flex-start;
  margin-top: 12px; padding: 7px 13px 7px 9px; border-radius: 999px;
  background: var(--orange-l); border: 2px solid color-mix(in srgb, var(--orange-d) 40%, transparent);
  font-size: 12.5px; font-weight: 800; color: var(--orange-d);
}
.pc-theme-now svg { width: 20px; height: 20px; }
.pc-themes { display: flex; gap: 9px; margin-top: 12px; flex-wrap: wrap; }
.pc-theme {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 9px 15px 9px 10px; border-radius: 16px; font-family: inherit;
  font-size: 13px; font-weight: 750; color: var(--ink2);
  background: var(--cream); border: 2px solid var(--hairline); cursor: pointer;
  transition: all 0.2s var(--ease);
}
.pc-theme img { width: 24px; height: 24px; border-radius: 8px; border: 2px solid var(--line); object-fit: cover; }
.pc-theme:hover { transform: translateY(-2px); }
.pc-theme.on {
  color: var(--orange-d); background: var(--orange-l);
  border-color: color-mix(in srgb, var(--orange-d) 50%, transparent);
  box-shadow: 0 3px 0 color-mix(in srgb, var(--orange-d) 18%, transparent);
}
.pc-theme-hint { font-size: 11.5px; margin-top: auto; padding-top: 12px; }

/* ── 专注四卡 ── */
.pc-focus { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 14px; }
@media (max-width: 980px) { .pc-focus { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 560px) { .pc-focus { grid-template-columns: 1fr; } }
.pc-fc {
  position: relative; border-radius: 18px; padding: 14px 16px 13px;
  background: var(--acl); border: 2px solid color-mix(in srgb, var(--ac) 34%, transparent);
  display: flex; flex-direction: column;
}
.pc-fc-h { display: flex; align-items: center; gap: 8px; font-size: 12.5px; font-weight: 800; color: var(--ink); }
.pc-fc-ic {
  width: 26px; height: 26px; flex: none; border-radius: 9px;
  background: var(--paper); border: 2px solid color-mix(in srgb, var(--ac) 38%, transparent);
  color: var(--ac); display: flex; align-items: center; justify-content: center;
}
.pc-fc-ic .icon { width: 13px; height: 13px; }
.pc-fc-v { font-size: 27px; font-weight: 800; letter-spacing: -0.5px; margin-top: 7px; line-height: 1.1; font-variant-numeric: tabular-nums; color: var(--ink); }
.pc-fc-v small { font-size: 12px; font-weight: 700; color: var(--ink3); margin-left: 4px; letter-spacing: 0; }
.pc-fc-goal {
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
  font-size: 11.5px; font-weight: 700; color: var(--ink2); margin-top: 3px; min-height: 24px;
}
.pc-goal-edit {
  width: 22px; height: 22px; border-radius: 8px; padding: 0; border: none;
  background: none; color: var(--ink3); cursor: pointer;
  display: inline-flex; align-items: center; justify-content: center;
  transition: all 0.2s var(--ease);
}
.pc-goal-edit:hover { color: var(--ac); transform: rotate(-8deg) scale(1.1); }
.pc-goal-edit .icon { width: 12px; height: 12px; }
.pc-goal-input {
  width: 64px; font-family: inherit; font-size: 12.5px; font-weight: 800;
  color: var(--ink); background: var(--paper); border: 2px solid var(--ac);
  border-radius: 8px; padding: 3px 7px; outline: none;
}
.pc-goal-unit { font-size: 11px; }
.pc-fc-bar {
  height: 7px; border-radius: 99px; margin-top: 10px;
  background: color-mix(in srgb, var(--ac) 16%, transparent); overflow: hidden;
}
.pc-fc-bar i { display: block; height: 100%; border-radius: 99px; background: var(--ac); transition: width 0.6s var(--ease-out-quart); }

/* 我的徽章 */
.pc-badges { margin-top: 14px; scroll-margin-top: 22px; }
.pc-badges .pc-sec-h h2 { margin: 0; font-size: inherit; }
.pc-badge-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(128px, 1fr)); gap: 12px; margin-top: 14px; }
.pc-owned-badge {
  min-width: 0; display: flex; flex-direction: column; align-items: center;
  padding: 12px 8px; text-align: center; border-radius: 16px;
  border: 1.5px solid var(--hairline); background: var(--cream);
}
.pc-owned-badge img { width: 100%; max-width: 108px; aspect-ratio: 1; object-fit: contain; }
.pc-owned-badge strong { margin-top: 5px; font-size: 13px; color: var(--ink); }
.pc-owned-badge small { margin-top: 3px; font-size: 11px; color: var(--ink3); }

/* ── 底部两栏 ── */
.pc-bottom { display: grid; grid-template-columns: 1.15fr 1fr; gap: 14px; margin-top: 14px; align-items: start; }
@media (max-width: 880px) { .pc-bottom { grid-template-columns: 1fr; } }
.pc-col { display: flex; flex-direction: column; gap: 14px; min-width: 0; }

.pc-sec-h { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 800; letter-spacing: -0.2px; }
.pc-sec-h > .icon { width: 16px; height: 16px; color: var(--orange-d); }
.pc-sec-right { margin-left: auto; }
.pc-link {
  display: inline-flex; align-items: center; gap: 3px; padding: 0;
  border: none; background: none; font-family: inherit;
  font-size: 12.5px; font-weight: 800; color: var(--orange-d); cursor: pointer;
}
.pc-link .icon { width: 12px; height: 12px; stroke-width: 2.6; }
.pc-link:hover { text-decoration: underline; }

.pc-empty { font-size: 12.5px; color: var(--ink3); margin-top: 10px; font-weight: 650; line-height: 1.7; }

/* 今日计划 */
.pc-plan-list { margin-top: 10px; display: flex; flex-direction: column; gap: 2px; }
.pc-plan-del {
  margin-left: auto; width: 24px; height: 24px; border-radius: 8px; padding: 0;
  border: none; background: none; color: var(--ink3); cursor: pointer;
  display: flex; align-items: center; justify-content: center; opacity: 0;
  transition: all 0.2s var(--ease);
}
.task:hover .pc-plan-del { opacity: 1; }
.pc-plan-del:hover { color: var(--berry); background: var(--berry-l); }
.pc-plan-del .icon { width: 11px; height: 11px; }
.pc-plan-add { display: flex; gap: 8px; margin-top: 12px; }
.pc-plan-add input {
  flex: 1; min-width: 0; font-family: inherit; font-size: 13px; font-weight: 650;
  color: var(--ink); background: var(--cream); border: 2px solid var(--hairline);
  border-radius: 12px; padding: 9px 12px; outline: none; transition: border-color 0.2s;
}
.pc-plan-add input:focus { border-color: var(--orange-d); }
.pc-add-btn {
  flex: none; padding: 9px 18px; border-radius: 12px; font-family: inherit;
  font-size: 13px; font-weight: 800; color: var(--onfill);
  background: linear-gradient(180deg, color-mix(in srgb, var(--orange) 78%, var(--ham)), var(--orange));
  border: 2px solid var(--line); box-shadow: 0 3px 0 color-mix(in srgb, var(--orange-d) 42%, transparent);
  cursor: pointer; transition: transform 0.15s var(--ease-out-quart), box-shadow 0.15s var(--ease-out-quart);
}
.pc-add-btn:active { transform: translateY(3px); box-shadow: none; }
.pc-add-btn.sm { padding: 6px 13px; font-size: 12px; border-radius: 10px; }

/* 节奏卡 */
.pc-rhythm {
  display: flex; align-items: center; gap: 12px; width: 100%; text-align: left;
  margin-top: 10px; padding: 11px 12px; border-radius: 14px; font-family: inherit;
  background: none; border: 2px solid transparent; cursor: pointer;
  transition: all 0.25s var(--ease);
}
.pc-rhythm:hover { background: var(--warm); border-color: var(--line); transform: translateX(3px); }
.pc-rhythm-ic {
  width: 38px; height: 38px; flex: none; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
}
.pc-rhythm-ic.a { background: var(--orange-l); color: var(--orange-d); }
.pc-rhythm-ic.b { background: var(--mint-l); color: var(--mint-d); }
.pc-rhythm-ic .icon { width: 16px; height: 16px; }
.pc-rhythm-tx { flex: 1; min-width: 0; }
.pc-rhythm-tx b { display: block; font-size: 13.5px; font-weight: 800; }
.pc-rhythm-tx i { display: block; font-style: normal; font-size: 12px; color: var(--ink2); margin-top: 2px; font-weight: 650; line-height: 1.5; }
.pc-chev { width: 14px; height: 14px; color: var(--ink3); flex: none; }

/* 签到 */
.pc-check-row { display: flex; align-items: baseline; gap: 10px; margin-top: 12px; }
.pc-check-row b { font-size: 24px; font-weight: 800; letter-spacing: -0.5px; font-variant-numeric: tabular-nums; }
.pc-check-row span { font-size: 12.5px; font-weight: 700; color: var(--ink2); }
.pc-check-sub { font-size: 12px; color: var(--ink3); margin-top: 3px; font-weight: 650; }

/* 刚进来的 */
.pc-recent { margin-top: 10px; display: flex; flex-direction: column; gap: 4px; }
.pc-recent-row {
  display: flex; align-items: center; gap: 11px; padding: 8px 10px; text-align: left;
  border-radius: 12px; border: 2px solid transparent; background: none; font-family: inherit; cursor: pointer;
  transition: all 0.22s var(--ease);
}
.pc-recent-row:hover { background: var(--warm); border-color: var(--line); }
.pc-recent-ic {
  width: 34px; height: 34px; flex: none; border-radius: 12px;
  border: 2px solid var(--line); display: flex; align-items: center; justify-content: center;
}
.pc-recent-ic.a { background: var(--grape-l); color: var(--grape-d); }
.pc-recent-ic.b { background: var(--orange-l); color: var(--orange-d); }
.pc-recent-ic.c { background: var(--mint-l); color: var(--mint-d); }
.pc-recent-ic .icon { width: 15px; height: 15px; }
.pc-recent-tx { flex: 1; min-width: 0; }
.pc-recent-tx b { display: block; font-size: 13px; font-weight: 750; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pc-recent-tx i { display: block; font-style: normal; font-size: 11.5px; color: var(--ink3); margin-top: 1px; font-weight: 650; }

/* 小提醒 */
.pc-tip-card { background: linear-gradient(160deg, var(--ins-a), var(--ins-b)); }
.pc-tip-row { display: flex; align-items: center; gap: 12px; margin-top: 10px; }
.pc-tip-row p { flex: 1; font-size: 12.5px; color: var(--ink2); font-weight: 650; line-height: 1.7; margin: 0; }
</style>
