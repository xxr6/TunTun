<template>
  <div class="stats-page">
    <header class="stats-head rise">
      <div>
        <h1 class="h-page">统计</h1>
        <p class="h-sub">看看时间花在哪里，也看看知识积累了多少。</p>
      </div>
      <button class="btn" :disabled="loading" @click="loadData">{{ loading ? '刷新中…' : '刷新数据' }}</button>
    </header>

    <div v-if="loading && !dash" class="card stats-state" role="status">正在整理你的学习记录…</div>
    <div v-else-if="error && !dash" class="card stats-state" role="alert">
      <p>{{ error }}</p><button class="btn btn-primary" @click="loadData">重试</button>
    </div>
    <template v-else-if="dash">
      <section aria-label="专注时长">
        <div class="stats-section-head"><h2 class="h-sec">专注时间</h2><span>点选时段，查看相应内容占比</span></div>
        <div class="period-grid">
          <button v-for="p in periods" :key="p.key" class="card period-card" type="button"
                  :class="{ selected: period === p.key }" :aria-pressed="period === p.key" @click="period = p.key">
            <span class="period-label">{{ p.label }} <span aria-hidden="true">{{ p.icon }}</span></span>
            <strong>{{ formatDuration(dash.focus[p.key].sec) }}</strong>
            <span class="period-goal">目标 {{ formatDuration(dash.focus[p.key].goal) }} · {{ goalPercent(dash.focus[p.key]) }}</span>
            <span class="period-progress" aria-hidden="true"><i :style="{ width: `${dash.focus[p.key].sec > 0 ? Math.max(2, Math.min(100, dash.focus[p.key].pct)) : 0}%` }"></i></span>
          </button>
        </div>
      </section>

      <section class="card topic-panel rise" aria-labelledby="topic-title">
        <div class="topic-head">
          <div><h2 id="topic-title" class="h-sec">专注内容占比</h2><p>{{ activePeriod.label }}共 {{ formatDuration(activeBlock.sec) }} · {{ comparisonText }}</p></div>
        </div>
        <div v-if="topicSlices.length" class="topic-content">
          <div class="topic-chart-wrap">
            <VChart class="topic-chart" :option="pieOption" :init-options="{ renderer: 'svg' }" autoresize role="img" :aria-label="`${activePeriod.label}专注内容时间占比图`" />
            <div class="topic-chart-center" aria-hidden="true"><strong>{{ formatDuration(activeBlock.sec) }}</strong><small>{{ activePeriod.label }}专注</small></div>
          </div>
          <ol class="topic-list">
            <li v-for="(item, index) in topicSlices" :key="item.name">
              <span class="topic-name"><i :style="{ background: pieColors[index % pieColors.length] }"></i><span :title="item.name">{{ item.name }}</span></span>
              <span class="topic-time">{{ formatTopicDuration(item.sec) }}</span>
              <strong>{{ percentage(item.sec) }}%</strong>
            </li>
          </ol>
        </div>
        <div v-else class="topic-empty">
          <strong>{{ activePeriod.label }}还没有专注记录</strong>
          <p>选一个卡组或写下专注内容，完成一轮后就能看到时间分布。</p>
          <button class="btn btn-primary" @click="router.push('/focus')">开始专注</button>
        </div>
        <p v-if="topicSlices.length" class="topic-note">{{ topicHint }}</p>
        <p v-if="focusStore.hasActiveSession" class="topic-note">正在进行的这一轮，会在结束并保存后计入统计。</p>
      </section>

      <section class="review-overview rise" aria-label="学习概览">
        <div class="stats-section-head"><h2 class="h-sec">学习概览</h2><span>和专注时间分开看，避免把不同指标混在一起</span></div>
        <div class="learning-grid">
          <div class="card learning-card"><span>累计复习</span><strong>{{ dash.metrics.total_reviews.toLocaleString() }}</strong><small>次</small></div>
          <div class="card learning-card"><span>近 30 天正确率</span><strong>{{ dash.metrics.accuracy_30d }}%</strong><small>按复习评分计算</small></div>
          <div class="card learning-card"><span>卡片库存</span><strong>{{ dash.metrics.cards_total.toLocaleString() }}</strong><small>张</small></div>
          <div class="card learning-card"><span>未来 7 天到期</span><strong>{{ dueNextWeek }}</strong><small>张 · <button @click="router.push('/review')">去复习 →</button></small></div>
        </div>
      </section>

      <section ref="badgeSection" class="badge-section rise" :class="{ 'is-visible': badgesVisible }" aria-labelledby="badge-title">
        <div class="stats-section-head"><h2 id="badge-title" class="h-sec">徽章收藏</h2><span>{{ unlockedCount }} / {{ dash.achievements.length }} 已解锁 · 点击徽章查看进度</span></div>
        <div class="badge-filters" role="group" aria-label="按主题筛选徽章">
          <button v-for="group in badgeGroups" :key="group" type="button" :class="{ active: badgeGroup === group }"
                  :aria-pressed="badgeGroup === group" @click="badgeGroup = group">{{ group }}</button>
        </div>
        <div :key="badgeGroup" class="badge-grid">
          <button v-for="(a, index) in visibleBadges" :key="a.name" type="button" class="badge-card card"
                  :style="{ '--badge-order': Math.min(index, 11) }"
                  :class="{ earned: a.unlocked }" :aria-label="`${a.name}，${a.unlocked ? '已解锁' : `进度 ${a.progress} / ${a.target}`}`"
                  @click="selectedBadge = a">
            <span class="badge-art"><img :src="badgeArt[a.name]" :alt="`${a.name}徽章`" loading="lazy" /></span>
            <strong>{{ a.name }}</strong>
            <span class="badge-card-bottom"><small>{{ a.group }} · {{ a.rarity }}</small><small>{{ a.unlocked ? '已获得' : `${a.progress}/${a.target}` }}</small></span>
          </button>
        </div>
      </section>

      <details class="card more-stats rise">
        <summary>更多学习记录 <span>复习热力图 · 卡组进展</span></summary>
        <div class="more-body">
          <section v-if="heatWeeks.length" class="more-section">
            <h3>最近 12 周复习</h3>
            <div class="heatmap" aria-label="最近 12 周复习热力图">
              <div v-for="(week, wi) in heatWeeks" :key="wi" class="heat-week">
                <span v-for="cell in week" :key="cell.date" class="heat-cell" :class="`heat-${heatLevel(cell.count)}`"
                      :title="`${cell.date} · ${cell.count} 次复习`"></span>
              </div>
            </div>
          </section>
          <section class="more-section">
            <h3>卡组进展</h3>
            <p v-if="!dash.deck_health.length" class="muted">还没有可以统计的卡组。</p>
            <div v-for="deck in dash.deck_health" :key="deck.name" class="deck-health">
              <span>{{ deck.name }}</span><span class="health-track"><i :style="{ width: `${deck.pct}%` }"></i></span><b>{{ deck.pct }}%</b>
            </div>
            <p v-if="dash.deck_health.length" class="muted">百分比表示已进入长期复习的卡片比例。</p>
          </section>
        </div>
      </details>
      <p class="stats-footnote">专注统计包含完整结束与打断后保存的时长；重置和打盹不计入。时间按会话开始日期归属。</p>
      <p v-if="error" class="stats-footnote" role="status">{{ error }}</p>
    </template>
    <Transition name="badge-detail">
    <div v-if="selectedBadge" class="badge-dialog-backdrop" @click.self="selectedBadge = null">
      <div class="badge-dialog card" role="dialog" aria-modal="true" :aria-label="`${selectedBadge.name}徽章详情`">
        <button class="badge-dialog-close" type="button" aria-label="关闭徽章详情" @click="selectedBadge = null">×</button>
        <img :class="{ locked: !selectedBadge.unlocked }" :src="badgeArt[selectedBadge.name]" :alt="`${selectedBadge.name}徽章`" />
        <span class="badge-dialog-group">{{ selectedBadge.group }} · {{ selectedBadge.rarity }}徽章</span>
        <h2>{{ selectedBadge.name }}</h2>
        <p>{{ selectedBadge.desc }}</p>
        <strong :class="{ unlocked: selectedBadge.unlocked }">{{ selectedBadge.unlocked ? '✦ 已解锁' : `进度 ${selectedBadge.progress} / ${selectedBadge.target}` }}</strong>
        <span v-if="!selectedBadge.unlocked" class="badge-dialog-progress"><i :style="{ width: `${Math.min(100, selectedBadge.progress / selectedBadge.target * 100)}%` }"></i></span>
      </div>
    </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { PieChart } from 'echarts/charts'
import { SVGRenderer } from 'echarts/renderers'
import { reviewApi } from '@/api/review'
import { statsApi } from '@/api/stats'
import { useFocusStore } from '@/stores/focus'
import { badgeArt, type Badge } from '@/lib/badges'
import type { FocusBlock, StatsDashboard } from '@/types/api'

use([PieChart, SVGRenderer])

type Period = 'today' | 'week' | 'month'
const periods: { key: Period; label: string; short: string; icon: string }[] = [
  { key: 'today', label: '今日专注', short: '今日', icon: '☀' },
  { key: 'week', label: '本周专注', short: '本周', icon: '✦' },
  { key: 'month', label: '本月专注', short: '本月', icon: '◷' },
]
const pieColors = ['#f49b54', '#7f73d9', '#56b899', '#f2c46d', '#68a5d9', '#d9859f', '#aea7a1']
const router = useRouter()
const focusStore = useFocusStore()
const dash = ref<StatsDashboard | null>(null)
const period = ref<Period>('today')
const loading = ref(false)
const error = ref('')
const heatmap = ref<{ date: string; count: number }[]>([])
const forecast = ref<{ date: string; count: number }[]>([])
const badgeGroup = ref('全部')
const selectedBadge = ref<Badge | null>(null)
const badgeSection = ref<HTMLElement | null>(null)
const badgesVisible = ref(false)
let badgeObserver: IntersectionObserver | null = null
const badgeGroups = ['全部', '坚持', '积累', '专注', '番茄钟', '提炼', '学习', '签到']

const activePeriod = computed(() => periods.find((p) => p.key === period.value)!)
const emptyBlock: FocusBlock = { sec: 0, goal: 0, pct: 0, prev_pct: null }
const activeBlock = computed(() => dash.value?.focus[period.value] ?? emptyBlock)
const allTopics = computed(() => dash.value?.focus.topics?.[period.value] ?? [])
const topicSlices = computed(() => {
  const values = allTopics.value.filter((item) => item.sec > 0)
  if (values.length <= 6) return values
  return [...values.slice(0, 6), { name: '其他内容', sec: values.slice(6).reduce((sum, item) => sum + item.sec, 0) }]
})
const pieOption = computed(() => ({
  color: pieColors,
  animationDuration: 600,
  animationDurationUpdate: 380,
  series: [{
    type: 'pie' as const, radius: ['62%', '82%'], center: ['50%', '50%'],
    avoidLabelOverlap: true, label: { show: false }, labelLine: { show: false },
    emphasis: { scale: true, scaleSize: 5 },
    data: topicSlices.value.map((item) => ({ name: item.name, value: item.sec })),
  }],
}))
const comparisonText = computed(() => {
  if (activeBlock.value.sec === 0) return '本时段尚无专注记录'
  const diff = activeBlock.value.prev_pct
  if (diff === null) return '暂无上期可比记录'
  const previous = period.value === 'today' ? '昨天' : period.value === 'week' ? '上周' : '上月'
  if (diff === 0) return `与${previous}持平`
  return `比${previous}${diff > 0 ? '多' : '少'} ${Math.abs(diff)}%`
})
const topicHint = computed(() => {
  const unnamed = allTopics.value.find((item) => item.name === '未指定')?.sec ?? 0
  if (unnamed > 0) return `其中 ${formatDuration(unnamed)} 未指定内容。下次专注时可以选卡组或写下目标，让分布更有参考价值。`
  return '图中按专注内容汇总；相同名称会合并，超过六项时其余归入“其他内容”。'
})
const dueNextWeek = computed(() => forecast.value.slice(0, 7).reduce((sum, item) => sum + item.count, 0))
const unlockedCount = computed(() => dash.value?.achievements.filter((a) => a.unlocked).length ?? 0)
const visibleBadges = computed(() => (dash.value?.achievements ?? []).filter((a) => badgeGroup.value === '全部' || a.group === badgeGroup.value))
const heatWeeks = computed(() => {
  const weeks: typeof heatmap.value[] = []
  for (let i = 0; i < heatmap.value.length; i += 7) weeks.push(heatmap.value.slice(i, i + 7))
  return weeks
})


function formatDuration(sec: number) {
  if (sec <= 0) return '0 分钟'
  if (sec < 60) return `${sec} 秒`
  const roundedMinutes = Math.round(sec / 60)
  const hours = Math.floor(roundedMinutes / 60)
  const minutes = roundedMinutes % 60
  if (!hours) return `${minutes} 分钟`
  return minutes ? `${hours} 小时 ${minutes} 分` : `${hours} 小时`
}
function formatTopicDuration(sec: number) {
  if (sec < 60) return `${sec} 秒`
  const minutes = Math.floor(sec / 60)
  const seconds = sec % 60
  return seconds ? `${minutes} 分 ${seconds} 秒` : `${minutes} 分钟`
}
function goalPercent(block: FocusBlock) {
  if (block.sec > 0 && block.pct === 0) return '<1%'
  return `${block.pct}%`
}
function percentage(sec: number) {
  return activeBlock.value.sec > 0 ? Math.round(sec / activeBlock.value.sec * 100) : 0
}
function heatLevel(count: number) {
  if (count <= 0) return 0
  if (count <= 2) return 1
  if (count <= 5) return 2
  if (count <= 9) return 3
  return 4
}
async function loadData() {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    const supplemental = Promise.allSettled([statsApi.heatmap(), reviewApi.forecast(14)])
    dash.value = (await statsApi.dashboard()).data
    await nextTick()
    observeBadges()
    if (window.location.hash === '#badge-title') badgeSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    const [heatResult, forecastResult] = await supplemental
    if (heatResult.status === 'fulfilled') heatmap.value = heatResult.value.data
    if (forecastResult.status === 'fulfilled') forecast.value = forecastResult.value.data
  } catch {
    error.value = '统计暂时没有加载成功，请稍后重试。'
  } finally {
    loading.value = false
  }
}
function observeBadges() {
  if (!badgeSection.value || badgesVisible.value) return
  if (!('IntersectionObserver' in window)) { badgesVisible.value = true; return }
  badgeObserver?.disconnect()
  badgeObserver = new IntersectionObserver((entries) => {
    if (entries.some((entry) => entry.isIntersecting)) {
      badgesVisible.value = true
      badgeObserver?.disconnect()
      badgeObserver = null
    }
  }, { threshold: 0.08, rootMargin: '0px 0px -24px 0px' })
  badgeObserver.observe(badgeSection.value)
}
function onBadgeKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') selectedBadge.value = null
}
onMounted(() => { loadData(); window.addEventListener('keydown', onBadgeKeydown) })
onUnmounted(() => { badgeObserver?.disconnect(); window.removeEventListener('keydown', onBadgeKeydown) })
</script>

<style scoped>
.stats-page { max-width: 1160px; margin: 0 auto; padding-bottom: 36px; }
.stats-head, .stats-section-head, .topic-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.stats-head { margin-bottom: 24px; }
.stats-head .h-sub { margin-top: 4px; }
.h-sec { font-size: 18px; font-weight: 850; }
.stats-section-head { margin: 0 0 12px; }
.stats-section-head span, .topic-head p, .muted { color: var(--ink3); font-size: 12px; }
.stats-state { min-height: 160px; padding: 30px; display: flex; align-items: center; justify-content: center; gap: 12px; color: var(--ink2); }
.period-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
.period-card { min-width: 0; display: flex; flex-direction: column; align-items: stretch; text-align: left; padding: 18px 20px; font: inherit; color: var(--ink); cursor: pointer; transition: transform .25s var(--ease-out-quart), border-color .25s ease, background .25s ease; }
.period-card:hover { transform: translateY(-3px); }
.period-card.selected { border-color: var(--orange-d); background: var(--orange-l); }
.period-card:focus-visible, .period-switch button:focus-visible { outline: 3px solid var(--orange); outline-offset: 3px; }
.period-label { display: flex; justify-content: space-between; color: var(--ink2); font-size: 13px; font-weight: 800; }
.period-label span { color: var(--orange-d); }
.period-card strong { margin-top: 8px; font-size: clamp(22px, 2.3vw, 31px); line-height: 1.2; white-space: nowrap; }
.period-goal { margin-top: 5px; color: var(--ink3); font-size: 11px; }
.period-progress { height: 8px; margin-top: 15px; border-radius: 99px; background: var(--warm); overflow: hidden; }
.period-progress i { display: block; height: 100%; border-radius: inherit; background: var(--orange); transition: width .45s ease; }
.topic-panel { margin-top: 16px; padding: 22px 24px 16px; }
.topic-head p { margin-top: 4px; }
.period-switch { display: inline-flex; gap: 3px; padding: 4px; border: 1.5px solid var(--hairline); border-radius: 12px; background: var(--cream); }
.period-switch button { padding: 6px 12px; border: 0; border-radius: 8px; background: transparent; color: var(--ink2); font: inherit; font-size: 12px; font-weight: 800; cursor: pointer; }
.period-switch button.on { background: var(--orange); color: var(--onfill); }
.topic-content { display: grid; grid-template-columns: minmax(220px, .8fr) minmax(0, 1.2fr); align-items: center; gap: 22px; }
.topic-chart-wrap { position: relative; height: 270px; }
.topic-chart { width: 100%; height: 100%; }
.topic-chart-center { position: absolute; top: 50%; left: 50%; display: flex; flex-direction: column; align-items: center; transform: translate(-50%, -50%); pointer-events: none; white-space: nowrap; }
.topic-chart-center strong { font-size: 20px; font-weight: 850; }
.topic-chart-center small { color: var(--ink3); font-size: 11px; }
.topic-list { list-style: none; min-width: 0; }
.topic-list li { display: grid; grid-template-columns: minmax(0, 1fr) auto 44px; align-items: center; gap: 10px; padding: 11px 0; border-bottom: 1px solid var(--hairline); font-size: 12px; }
.topic-list li:last-child { border-bottom: 0; }
.topic-name { display: flex; align-items: center; min-width: 0; gap: 9px; font-weight: 750; }
.topic-name i { width: 11px; height: 11px; flex: none; border-radius: 50%; }
.topic-name span { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.topic-time { color: var(--ink2); white-space: nowrap; }
.topic-list strong { text-align: right; font-variant-numeric: tabular-nums; }
.topic-note { margin-top: 7px; color: var(--ink3); font-size: 11px; }
.topic-empty { padding: 25px 12px; text-align: center; }
.topic-empty strong { font-size: 16px; }
.topic-empty p { margin: 6px 0 16px; color: var(--ink2); font-size: 12px; }
.review-overview { margin-top: 26px; }
.learning-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.learning-card { display: flex; flex-direction: column; padding: 16px 18px; }
.learning-card span { color: var(--ink2); font-size: 12px; font-weight: 800; }
.learning-card strong { margin-top: 4px; font-size: 27px; line-height: 1.2; }
.learning-card small { color: var(--ink3); font-size: 11px; }
.learning-card small button { border: 0; background: transparent; color: var(--orange-d); font: inherit; font-weight: 800; cursor: pointer; }
.badge-section { margin-top: 28px; scroll-margin-top: 20px; }
.badge-filters { display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 13px; }
.badge-filters button { border: 1.5px solid var(--hairline); border-radius: 99px; background: var(--paper); color: var(--ink2); padding: 7px 13px; font: inherit; font-size: 12px; font-weight: 750; cursor: pointer; }
.badge-filters button.active { border-color: var(--orange-d); background: var(--orange-l); color: var(--ink); }
.badge-filters button:focus-visible, .badge-card:focus-visible, .badge-dialog-close:focus-visible { outline: 3px solid var(--orange); outline-offset: 3px; }
.badge-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; }
.badge-card { display: flex; flex-direction: column; align-items: center; min-width: 0; padding: 13px 11px 11px; color: var(--ink); font: inherit; text-align: center; cursor: pointer; transition: transform .25s var(--ease-out-quart), border-color .25s ease, box-shadow .25s ease; }
.badge-section.is-visible .badge-card { animation: badgeDealIn .52s var(--ease-out-quart) both; animation-delay: calc(var(--badge-order, 0) * 42ms); }
@keyframes badgeDealIn { from { opacity: 0; transform: translateY(22px) scale(.88) rotate(-3deg); } to { opacity: 1; transform: translateY(0) scale(1) rotate(0); } }
.badge-card:hover { transform: translateY(-4px); border-color: var(--orange-d); }
.badge-card.earned { position: relative; overflow: hidden; background: linear-gradient(155deg, var(--orange-l), var(--paper) 65%); }
.badge-card.earned::after { content: ''; position: absolute; top: -60%; left: -95%; width: 46%; height: 220%; transform: rotate(22deg); background: linear-gradient(90deg, transparent, rgb(255 255 255 / 68%), transparent); transition: left .65s ease; pointer-events: none; }
.badge-card.earned:hover::after { left: 145%; }
.badge-card.earned:hover { box-shadow: 0 10px 25px rgb(98 55 25 / 13%); }
.badge-card:not(.earned) { color: var(--ink3); background: var(--cream); }
.badge-art { display: grid; place-items: center; width: min(100%, 148px); aspect-ratio: 1; border-radius: 18px; background: radial-gradient(circle at 50% 38%, #fffaf0 0, #f1e9e0 64%, #ece8ed 100%); }
.badge-art img { display: block; width: 100%; height: 100%; object-fit: contain; transition: transform .35s var(--ease-out-quart); }
.badge-card.earned:hover .badge-art img { transform: translateY(-5px) rotate(-4deg) scale(1.07); }
.badge-card:not(.earned) .badge-art { background: #efeeed; }
.badge-card:not(.earned) .badge-art img, .badge-dialog > img.locked { filter: grayscale(1); opacity: .62; }
.badge-card strong { max-width: 100%; margin-top: 8px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; }
.badge-card-bottom { display: flex; justify-content: space-between; align-self: stretch; gap: 4px; margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--hairline); color: var(--ink3); }
.badge-card-bottom small { font-size: 10px; white-space: nowrap; }
.badge-card.earned .badge-card-bottom small:last-child { color: var(--orange-d); font-weight: 800; }
.badge-dialog-backdrop { position: fixed; inset: 0; z-index: 80; display: grid; place-items: center; padding: 18px; background: rgb(24 20 30 / 55%); backdrop-filter: blur(5px); }
.badge-detail-enter-active, .badge-detail-leave-active { transition: opacity .22s ease; }
.badge-detail-enter-from, .badge-detail-leave-to { opacity: 0; }
.badge-detail-enter-active .badge-dialog, .badge-detail-leave-active .badge-dialog { transition: transform .34s var(--ease-out-quart), opacity .25s ease; }
.badge-detail-enter-from .badge-dialog { opacity: 0; transform: translateY(24px) scale(.86) rotate(-3deg); }
.badge-detail-leave-to .badge-dialog { opacity: 0; transform: translateY(12px) scale(.95); }
.badge-dialog { position: relative; display: flex; flex-direction: column; align-items: center; width: min(100%, 370px); padding: 28px 26px 30px; text-align: center; background: var(--paper); box-shadow: 8px 10px 0 rgb(28 20 22 / 18%); }
.badge-dialog-close { position: absolute; right: 12px; top: 9px; border: 0; background: transparent; color: var(--ink2); font-size: 28px; cursor: pointer; }
.badge-dialog > img { width: 200px; height: 200px; object-fit: contain; border-radius: 20px; background: radial-gradient(circle at 50% 38%, #fffaf0, #f1e9e0 72%); }
.badge-dialog-group { margin-top: 13px; color: var(--orange-d); font-size: 12px; font-weight: 800; }
.badge-dialog h2 { margin: 4px 0 0; font-size: 22px; }
.badge-dialog p { margin: 8px 0 18px; color: var(--ink2); font-size: 13px; }
.badge-dialog > strong { font-size: 13px; }
.badge-dialog > strong.unlocked { color: var(--orange-d); }
.badge-dialog-progress { width: 100%; height: 8px; margin-top: 10px; overflow: hidden; border-radius: 99px; background: var(--warm); }
.badge-dialog-progress i { display: block; height: 100%; border-radius: inherit; background: var(--orange); }
@media (prefers-reduced-motion: reduce) { .badge-section.is-visible .badge-card { animation: none; } .badge-card.earned::after, .badge-art img, .badge-detail-enter-active, .badge-detail-leave-active, .badge-detail-enter-active .badge-dialog, .badge-detail-leave-active .badge-dialog { transition: none; } }
.more-stats { margin-top: 16px; padding: 0; }
.more-stats summary { padding: 16px 20px; cursor: pointer; font-size: 14px; font-weight: 850; }
.more-stats summary span { margin-left: 10px; color: var(--ink3); font-size: 11px; font-weight: 500; }
.more-body { padding: 0 20px 20px; }
.more-section { border-top: 1px solid var(--hairline); padding-top: 14px; margin-top: 14px; }
.more-section h3 { margin-bottom: 9px; font-size: 13px; }
.more-section h3 small { color: var(--ink3); font-size: 11px; }
.heatmap { display: flex; gap: 4px; overflow-x: auto; padding: 2px 0 8px; }
.heat-week { display: flex; flex-direction: column; gap: 4px; flex: none; }
.heat-cell { width: 13px; height: 13px; border: 1px solid var(--hairline); border-radius: 4px; }
.heat-0 { background: var(--heat0); } .heat-1 { background: var(--heat1); } .heat-2 { background: var(--heat2); } .heat-3 { background: var(--heat3); } .heat-4 { background: var(--heat4); }
.deck-health { display: grid; grid-template-columns: minmax(90px, 160px) minmax(0, 1fr) 38px; gap: 10px; align-items: center; padding: 5px 0; font-size: 12px; }
.deck-health > span:first-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.health-track { height: 8px; border-radius: 99px; background: var(--warm); overflow: hidden; }
.health-track i { display: block; height: 100%; background: var(--mint); }
.deck-health b { text-align: right; }
.stats-footnote { margin-top: 14px; color: var(--ink3); font-size: 11px; }
@media (max-width: 900px) { .learning-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .badge-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
@media (max-width: 700px) { .period-grid { gap: 8px; } .period-card { padding: 12px; } .period-card strong { font-size: 20px; white-space: normal; } .topic-content { grid-template-columns: 1fr; gap: 0; } .topic-chart-wrap { height: 230px; } .topic-panel { padding: 18px; } .badge-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; } }
@media (max-width: 480px) { .stats-head .btn { padding: 7px 10px; font-size: 11px; } .stats-section-head span { display: none; } .period-card strong { font-size: 16px; } .period-label { font-size: 11px; } .period-goal { font-size: 10px; } .topic-head { align-items: flex-start; flex-wrap: wrap; } .period-switch { width: 100%; justify-content: space-around; } .learning-grid { gap: 8px; } .learning-card { padding: 12px; } .learning-card strong { font-size: 22px; } .badge-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .badge-card { padding: 10px 8px; } .more-stats summary span { display: block; margin: 2px 0 0; } }
@media (prefers-reduced-motion: reduce) { .period-card, .period-progress i { transition: none; } }
</style>
