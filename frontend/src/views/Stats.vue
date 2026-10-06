<template>
  <div>
    <div class="st-head rise">
      <div>
        <div class="h-page">统计</div>
        <div class="h-sub">过去 12 周，时间都花在哪儿了</div>
      </div>
      <span class="chip chip-g" title="专注目标现在写死在统计里，设置页做好后可改">目标可在设置里改</span>
    </div>

    <!-- ── 专注时长三卡 ── -->
    <div class="sec-head rise"><span class="h-sec">专注时长</span></div>
    <div class="focus-grid rise">
      <div v-for="card in focusCards" :key="card.key" class="card fcard2" :data-tone="card.tone">
        <div class="f-top">
          <span class="f-ic"><svg class="icon"><use :href="card.icon" /></svg></span>
          <span class="f-label">{{ card.label }}</span>
        </div>
        <div class="f-num" :class="'tone-' + card.tone">{{ fmtH(dash.focus[card.key].sec) }}</div>
        <div class="f-goal">
          目标 {{ fmtH(dash.focus[card.key].goal) }} · {{ card.goalNote }}
        </div>
        <div class="f-bar"><i :style="{ width: dash.focus[card.key].pct + '%' }"></i></div>
        <div class="f-prev">
          <template v-if="dash.focus[card.key].prev_pct !== null">
            <span :class="dash.focus[card.key].prev_pct! >= 0 ? 'up' : 'down'">
              {{ dash.focus[card.key].prev_pct! >= 0 ? '↑' : '↓' }}
              比{{ card.prevName }}{{ Math.abs(dash.focus[card.key].prev_pct!) }}%
            </span>
          </template>
          <span v-else class="muted-s">还没有{{ card.prevName }}的记录</span>
        </div>
        <div class="f-bars">
          <div v-for="b in card.bars" :key="b.label" class="f-bar-col" :title="b.label + ' ' + b.min + ' 分钟'">
            <i :style="{ height: b.h + '%' }" :class="{ hot: b.hot }"></i>
            <small>{{ b.label }}</small>
          </div>
        </div>
      </div>
    </div>

    <!-- ── 指标行 ── -->
    <div class="metric-grid rise">
      <div class="card mcard">
        <div class="m-label">累计复习</div>
        <div class="m-num">{{ dash.metrics.total_reviews.toLocaleString() }}</div>
        <div class="m-sub muted-s">次</div>
      </div>
      <div class="card mcard">
        <div class="m-label">平均正确率</div>
        <div class="m-num tone-mint">{{ dash.metrics.accuracy_30d }}%</div>
        <div class="m-sub muted-s">近 30 天 · 评分「想起来了」及以上</div>
      </div>
      <div class="card mcard">
        <div class="m-label">囤了多少</div>
        <div class="m-num">{{ dash.metrics.cards_total.toLocaleString() }}</div>
        <div class="m-sub muted-s">张卡片在库里</div>
      </div>
      <div class="card mcard">
        <div class="m-label">AI 用量</div>
        <div class="m-num tone-orange">{{ dash.metrics.ai_calls_month }} 次</div>
        <div class="m-sub muted-s">本月调用 · 免费模型额度内</div>
      </div>
    </div>

    <!-- ── 复习热力图 ── -->
    <div class="card pad rise" style="margin-top:18px">
      <div class="hm-head">
        <span class="h-sec">复习热力图</span>
        <span class="hm-legend">少 <i v-for="l in 5" :key="l" class="hm-cell" :class="'heat' + (l - 1)"></i> 多</span>
      </div>
      <div class="hm-grid">
        <div v-for="(week, wi) in heatWeeks" :key="wi" class="hm-col">
          <i v-for="cell in week" :key="cell.date" class="hm-cell" :class="'heat' + heatLevel(cell.count)"
             :title="cell.date + ' · ' + cell.count + ' 次'"></i>
        </div>
      </div>
    </div>

    <!-- ── 遗忘曲线 ── -->
    <div class="card pad rise" style="margin-top:18px">
      <div class="fc-head">
        <div>
          <span class="h-sec">遗忘曲线</span>
          <div class="muted-s" style="margin-top:2px">同一批卡片，复习与不复习的差别（按你的平均稳定性推算）</div>
        </div>
        <div class="fc-legend">
          <span><i class="lg-dot" style="background:var(--berry)"></i>不复习的话</span>
          <span><i class="lg-dot" style="background:var(--mint)"></i>按计划复习</span>
        </div>
      </div>
      <svg viewBox="0 0 640 220" class="fc-svg" role="img" aria-label="遗忘曲线示意图">
        <line v-for="g in [0, 25, 50, 75, 100]" :key="g" x1="36" :y1="gy(g)" x2="632" :y2="gy(g)"
              stroke="var(--hairline)" stroke-width="1" stroke-dasharray="4 4" />
        <text v-for="g in [0, 25, 50, 75, 100]" :key="'t' + g" x="30" :y="gy(g) + 4" text-anchor="end"
              class="fc-tick">{{ g }}%</text>
        <path :d="forgetPath" fill="none" stroke="var(--berry)" stroke-width="2.5" stroke-linecap="round" />
        <path :d="planPath" fill="none" stroke="var(--mint)" stroke-width="2.5" stroke-linecap="round" />
        <circle v-for="(p, i) in planResetPts" :key="i" :cx="p.x" :cy="p.y" r="4"
                fill="var(--mint)" stroke="var(--paper)" stroke-width="1.5" />
        <text v-for="d in [0, 1, 3, 7, 14, 30]" :key="'d' + d" :x="fx(d)" y="214" text-anchor="middle"
              class="fc-tick">{{ d }}天</text>
      </svg>
      <div class="fc-stats">
        <div class="fc-stat"><small>当期平均保留率</small><b class="tone-mint">90%</b></div>
        <div class="fc-stat"><small>平均记忆稳定性</small><b>{{ stabilityDays }} 天</b></div>
        <div class="fc-stat"><small>最佳复习时机</small><b class="tone-orange">保留率 ~75%</b></div>
        <div class="fc-stat"><small>30 天后差距</small><b class="tone-orange">{{ planAt30 }}% vs {{ freeAt30 }}%</b></div>
      </div>
    </div>

    <!-- ── 14 天预测 + 卡组健康度 ── -->
    <div class="two-grid rise">
      <div class="card pad">
        <div class="h-sec" style="margin-bottom:12px">未来 14 天到期预测</div>
        <div class="f-bars" style="height:110px">
          <div v-for="d in forecast" :key="d.date" class="f-bar-col fc-bar" :title="d.date + ' · ' + d.count + ' 张到期'">
            <i :style="{ height: barH(d.count, forecastMax) + '%' }"></i>
            <small>{{ Number(d.date.slice(-2)) }}</small>
          </div>
        </div>
      </div>
      <div class="card pad">
        <div class="h-sec" style="margin-bottom:6px">卡组健康度</div>
        <div class="muted-s" style="margin-bottom:10px">毕业卡占比——进入长期复习的卡片越多越健康</div>
        <div v-if="!dash.deck_health.length" class="muted-s">还没有卡组数据。</div>
        <div v-for="d in dash.deck_health" :key="d.name" class="dh-row">
          <div class="dh-top"><span class="dh-name">{{ d.name }}</span><span class="dh-pct" :class="healthTone(d.pct)">{{ d.pct }}%</span></div>
          <div class="dh-bar"><i :style="{ width: d.pct + '%' }" :class="healthTone(d.pct)"></i></div>
        </div>
      </div>
    </div>

    <!-- ── 成就勋章 ── -->
    <div class="ach-head rise">
      <span class="h-sec">成就勋章</span>
      <span class="chip chip-g">{{ unlockedCount }} / {{ dash.achievements.length }}</span>
    </div>
    <div class="muted-s rise" style="margin:-6px 0 12px">四组共 {{ dash.achievements.length }} 枚 · 稀有度越高越难拿</div>

    <!-- 收藏柜 -->
    <div class="card pad rise ach-cabinet">
      <div class="cab-main">
        <div class="cab-num">{{ unlockedCount }}<small> / {{ dash.achievements.length }}</small></div>
        <div class="cab-sub">枚勋章已解锁 · 收藏柜完成度 {{ cabinetPct }}%</div>
        <div class="cab-bar"><i :style="{ width: cabinetPct + '%' }"></i></div>
      </div>
      <div class="cab-next">
        <small>离下一枚还差</small>
        <b>{{ nextAchievement?.name || '全部解锁！' }}</b>
        <div class="cab-next-bar"><i :style="{ width: nextPct + '%' }"></i></div>
        <small class="muted-s">{{ nextAchievement ? nextProgressText : '你就是满级囤囤玩家' }}</small>
      </div>
    </div>

    <!-- 最近解锁 -->
    <div v-if="latestUnlocked" class="card pad rise latest-card">
      <div class="hex" :class="'r-' + latestUnlocked.rarity">
        <svg class="icon"><use :href="latestUnlocked.icon" /></svg>
      </div>
      <div class="latest-body">
        <small class="muted-s">最近解锁</small>
        <div class="latest-name">{{ latestUnlocked.name }}</div>
        <div class="latest-desc">{{ latestUnlocked.desc }}</div>
      </div>
      <span class="chip" :class="rarityChip(latestUnlocked.rarity)">{{ latestUnlocked.rarity }}章</span>
    </div>

    <!-- 分组徽章 -->
    <div v-for="g in groupedAch" :key="g.name" class="ach-group rise">
      <div class="ach-group-head">
        <span class="ach-group-name">{{ g.name }} <b>{{ g.unlocked }}/{{ g.items.length }}</b></span>
        <span class="ach-group-progress" :style="{ '--p': (g.unlocked / g.items.length * 100) + '%' }"></span>
      </div>
      <div class="ach-grid">
        <div v-for="a in g.items" :key="a.name" class="card ach-card" :class="{ locked: !a.unlocked }" :title="a.desc">
          <span class="ach-rarity" :class="rarityChip(a.rarity)">{{ a.rarity }}章</span>
          <div class="hex" :class="a.unlocked ? 'r-' + a.rarity : 'r-locked'">
            <svg class="icon"><use :href="a.icon" /></svg>
          </div>
          <div class="ach-name">{{ a.name }}</div>
          <div class="ach-desc">{{ a.unlocked ? a.desc : progressText(a) }}</div>
          <div class="ach-bar"><i :style="{ width: (a.progress / a.target * 100) + '%' }"></i></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { reviewApi } from '@/api/review'
import { statsApi } from '@/api/stats'
import type { StatsDashboard } from '@/types/api'

const dash = ref<StatsDashboard>({
  focus: {
    today: { sec: 0, goal: 10800, pct: 0, prev_pct: null },
    week: { sec: 0, goal: 72000, pct: 0, prev_pct: null },
    month: { sec: 0, goal: 288000, pct: 0, prev_pct: null },
    dist_today: {}, dist_week: {}, dist_month: {},
  },
  metrics: { total_reviews: 0, accuracy_30d: 0, cards_total: 0, ai_calls_month: 0 },
  avg_stability: null,
  deck_health: [],
  achievements: [],
})
const heatmap = ref<{ date: string; count: number }[]>([])
const forecast = ref<{ date: string; count: number }[]>([])

/* ── 专注三卡 ── */
const focusCards = computed(() => {
  const d = dash.value.focus
  const barsOf = (dist: Record<string, number>, labels: string[]) => {
    const max = Math.max(1, ...labels.map((l) => dist[l] || 0))
    return labels.map((l) => ({
      label: l,
      min: Math.round((dist[l] || 0) / 60),
      h: Math.round((dist[l] || 0) / max * 100),
      hot: (dist[l] || 0) === max && (dist[l] || 0) > 0,
    }))
  }
  const hourLabels = Array.from({ length: 18 }, (_, i) => String(i + 6)) // 6~23 点
  return [
    { key: 'today' as const, tone: 'orange', label: '今日专注', icon: '#i-flame', goalNote: '今日目标', prevName: '昨天',
      bars: barsOf(d.dist_today, hourLabels) },
    { key: 'week' as const, tone: 'mint', label: '本周专注', icon: '#i-calendar', goalNote: '周目标', prevName: '上周',
      bars: barsOf(d.dist_week, ['一', '二', '三', '四', '五', '六', '日']) },
    { key: 'month' as const, tone: 'grape', label: '本月专注', icon: '#i-target', goalNote: '月目标', prevName: '上月',
      bars: barsOf(d.dist_month, ['第1期', '第2期', '第3期', '第4期', '第5期']) },
  ]
})

/* ── 热力图：91 天 → 按周分列 ── */
const heatWeeks = computed(() => {
  const cols: { date: string; count: number }[][] = []
  let cur: { date: string; count: number }[] = []
  for (const cell of heatmap.value) {
    cur.push(cell)
    if (cur.length === 7) { cols.push(cur); cur = [] }
  }
  if (cur.length) cols.push(cur)
  return cols
})
function heatLevel(count: number) {
  if (count <= 0) return 0
  if (count <= 2) return 1
  if (count <= 5) return 2
  if (count <= 9) return 3
  return 4
}

/* ── 遗忘曲线（FSRS 理论曲线，按平均稳定性推算）── */
const S = computed(() => Math.max(1, dash.value.avg_stability ?? 5))
const RESETS = [1, 3, 7, 14] // 按计划复习的重置点（天）
const W = 640, H = 220, PAD_L = 36, PAD_B = 24, TOP = 12
const fx = (t: number) => PAD_L + (t / 30) * (W - PAD_L - 8)
const gy = (pct: number) => TOP + (1 - pct / 100) * (H - TOP - PAD_B)
// 不复习：R = 100·e^(-t/S)
const forgetPath = computed(() => {
  const pts: string[] = []
  for (let t = 0; t <= 30; t += 0.5) {
    const r = 100 * Math.exp(-t / S.value)
    pts.push(`${pts.length ? 'L' : 'M'}${fx(t).toFixed(1)} ${gy(r).toFixed(1)}`)
  }
  return pts.join(' ')
})
// 按计划：每段从 90% 衰减，到重置点跳回（复习瞬间恢复）
const planSegs = computed(() => {
  const pts: { t: number; r: number }[] = [{ t: 0, r: 100 }]
  let last = { t: 0, r: 100 }
  for (const tr of RESETS) {
    for (let t = last.t + 0.25; t <= tr; t += 0.25) {
      pts.push({ t, r: last.r * Math.exp(-(t - last.t) / S.value) })
    }
    pts.push({ t: tr, r: 90 })
    last = { t: tr, r: 90 }
  }
  for (let t = last.t + 0.25; t <= 30; t += 0.25) {
    pts.push({ t, r: last.r * Math.exp(-(t - last.t) / S.value) })
  }
  return pts
})
const planPath = computed(() =>
  planSegs.value.map((p, i) => `${i ? 'L' : 'M'}${fx(p.t).toFixed(1)} ${gy(p.r).toFixed(1)}`).join(' '))
const planResetPts = computed(() => {
  const seen: { x: number; y: number }[] = []
  let last = { t: 0, r: 100 }
  for (const tr of RESETS) {
    const rBefore = last.r * Math.exp(-(tr - last.t) / S.value)
    seen.push({ x: fx(tr), y: gy(rBefore) })
    last = { t: tr, r: 90 }
  }
  return seen
})
const planAt30 = computed(() => Math.round(planSegs.value[planSegs.value.length - 1].r))
const freeAt30 = computed(() => Math.round(100 * Math.exp(-30 / S.value)))
const stabilityDays = computed(() => Math.round(S.value * 10) / 10)

/* ── 成就 ── */
const unlockedCount = computed(() => dash.value.achievements.filter((a) => a.unlocked).length)
const cabinetPct = computed(() =>
  dash.value.achievements.length
    ? Math.round(unlockedCount.value / dash.value.achievements.length * 100)
    : 0)
const groupedAch = computed(() => {
  const map = new Map<string, typeof dash.value.achievements>()
  for (const a of dash.value.achievements) {
    if (!map.has(a.group)) map.set(a.group, [])
    map.get(a.group)!.push(a)
  }
  return [...map.entries()].map(([name, items]) => ({
    name,
    items,
    unlocked: items.filter((a) => a.unlocked).length,
  }))
})
const latestUnlocked = computed(() => {
  const list = dash.value.achievements.filter((a) => a.unlocked)
  return list.length ? list[list.length - 1] : null
})
const nextAchievement = computed(() =>
  dash.value.achievements
    .filter((a) => !a.unlocked)
    .sort((x, y) => y.progress / y.target - x.progress / x.target)[0] ?? null)
const nextPct = computed(() =>
  nextAchievement.value ? Math.round(nextAchievement.value.progress / nextAchievement.value.target * 100) : 100)
const nextProgressText = computed(() => {
  const a = nextAchievement.value
  if (!a) return ''
  return a.name.includes('仓') || a.name.includes('拆解') || a.name.includes('笔记')
    ? `${a.progress} / ${a.target}`
    : `还差 ${a.target - a.progress} 天`
})
function progressText(a: { progress: number; target: number }) {
  return `${a.progress} / ${a.target}`
}
function rarityChip(r: string) {
  return { 铜: 'chip-r-copper', 银: 'chip-r-silver', 金: 'chip-r-gold', 钻: 'chip-r-diamond' }[r] ?? 'chip-g'
}
function healthTone(pct: number) {
  return pct >= 80 ? 'ok' : pct >= 50 ? 'mid' : 'low'
}

/* ── 工具 ── */
function fmtH(sec: number) {
  return (sec / 3600).toFixed(1) + 'h'
}
function barH(count: number, max: number) {
  return max > 0 ? Math.round(count / max * 100) : 0
}
const forecastMax = computed(() => Math.max(1, ...forecast.value.map((d) => d.count)))

onMounted(async () => {
  const [d, hm, fc] = await Promise.all([
    statsApi.dashboard(),
    statsApi.heatmap(),
    reviewApi.forecast(14).catch(() => ({ data: [] as { date: string; count: number }[] })),
  ])
  dash.value = d.data
  heatmap.value = hm.data
  forecast.value = fc.data
})
</script>

<style scoped>
.st-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
.h-sec { font-size: 15px; font-weight: 800; }
.muted-s { color: var(--ink3); font-size: 12px; font-weight: 600; }
.tone-orange { color: var(--orange-d); }
.tone-mint { color: var(--mint-d); }
.tone-grape { color: var(--grape-d); }

/* ── 专注三卡 ── */
.sec-head { margin-bottom: 10px; }
.focus-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
@media (max-width: 900px) { .focus-grid { grid-template-columns: 1fr; } }
.fcard2 { padding: 16px 18px; }
.f-top { display: flex; align-items: center; gap: 9px; margin-bottom: 8px; }
.f-ic {
  width: 34px; height: 34px; display: grid; place-items: center; flex: none;
  border-radius: 11px; background: var(--paper); border: 2px solid var(--line); box-shadow: var(--pop-sm);
}
.fcard2[data-tone='orange'] .f-ic { color: var(--orange-d); background: var(--orange-l); }
.fcard2[data-tone='mint'] .f-ic { color: var(--mint-d); background: var(--mint-l); }
.fcard2[data-tone='grape'] .f-ic { color: var(--grape-d); background: var(--grape-l); }
.f-label { font-size: 13px; font-weight: 800; color: var(--ink2); }
.f-num { font-size: 34px; font-weight: 800; letter-spacing: -1.5px; line-height: 1.1; font-variant-numeric: tabular-nums; }
.f-goal { font-size: 11.5px; color: var(--ink3); font-weight: 700; margin-top: 2px; }
.f-bar { height: 10px; border-radius: 99px; background: var(--warm); border: 2px solid var(--hairline); margin: 8px 0 6px; overflow: hidden; }
.f-bar i { display: block; height: 100%; border-radius: 99px; transition: width 0.6s var(--ease-out-quart); }
.fcard2[data-tone='orange'] .f-bar i { background: var(--orange); }
.fcard2[data-tone='mint'] .f-bar i { background: var(--mint); }
.fcard2[data-tone='grape'] .f-bar i { background: var(--grape); }
.f-prev { font-size: 12px; font-weight: 750; }
.f-prev .up { color: var(--mint-d); }
.f-prev .down { color: var(--berry); }

/* mini 柱状 */
.f-bars { display: flex; align-items: flex-end; gap: 6px; height: 56px; margin-top: 12px; }
.f-bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; gap: 4px; }
.f-bar-col i { display: block; width: 100%; max-width: 22px; min-height: 3px; border-radius: 5px 5px 2px 2px; background: var(--ham); border: 1.5px solid var(--line); }
.f-bar-col i.hot { background: var(--orange); }
.f-bar-col small { font-size: 9.5px; color: var(--ink3); font-weight: 700; }
.fc-bar i { background: var(--sky); }

/* ── 指标行 ── */
.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 14px; }
@media (max-width: 900px) { .metric-grid { grid-template-columns: repeat(2, 1fr); } }
.mcard { padding: 13px 16px; }
.m-label { font-size: 11.5px; font-weight: 800; color: var(--ink2); }
.m-num { font-size: 24px; font-weight: 800; letter-spacing: -0.8px; margin-top: 2px; font-variant-numeric: tabular-nums; }
.m-sub { margin-top: 1px; }

/* ── 热力图 ── */
.pad { padding: 16px 18px; }
.hm-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.hm-legend { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; color: var(--ink3); font-weight: 700; }
.hm-grid { display: flex; gap: 5px; overflow-x: auto; padding-bottom: 4px; }
.hm-col { display: flex; flex-direction: column; gap: 5px; flex: none; }
.hm-cell { width: 14px; height: 14px; border-radius: 4.5px; border: 1.5px solid var(--hairline); display: inline-block; }
.hm-cell.heat0 { background: var(--heat0); }
.hm-cell.heat1 { background: var(--heat1); }
.hm-cell.heat2 { background: var(--heat2); }
.hm-cell.heat3 { background: var(--heat3); border-color: var(--line); }
.hm-cell.heat4 { background: var(--heat4); border-color: var(--line); }

/* ── 遗忘曲线 ── */
.fc-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; flex-wrap: wrap; margin-bottom: 8px; }
.fc-legend { display: flex; gap: 14px; font-size: 12px; font-weight: 700; color: var(--ink2); }
.fc-legend span { display: inline-flex; align-items: center; gap: 5px; }
.lg-dot { width: 14px; height: 5px; border-radius: 3px; display: inline-block; }
.fc-svg { width: 100%; height: auto; }
.fc-tick { font-size: 11px; fill: var(--ink3); font-weight: 700; }
.fc-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; border-top: 2px dashed var(--hairline); padding-top: 12px; margin-top: 4px; }
@media (max-width: 700px) { .fc-stats { grid-template-columns: repeat(2, 1fr); } }
.fc-stat small { display: block; font-size: 11px; color: var(--ink3); font-weight: 700; }
.fc-stat b { font-size: 17px; font-weight: 800; }

/* ── 两栏 ── */
.two-grid { display: grid; grid-template-columns: 1.2fr 1fr; gap: 14px; }
@media (max-width: 900px) { .two-grid { grid-template-columns: 1fr; } }

/* 卡组健康度 */
.dh-row { margin-bottom: 12px; }
.dh-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
.dh-name { font-size: 13px; font-weight: 750; }
.dh-pct { font-size: 12.5px; font-weight: 800; }
.dh-bar { height: 9px; border-radius: 99px; background: var(--warm); border: 2px solid var(--hairline); overflow: hidden; }
.dh-bar i { display: block; height: 100%; border-radius: 99px; transition: width 0.6s var(--ease-out-quart); }
.dh-bar i.ok { background: var(--mint); }
.dh-bar i.mid { background: var(--ham); }
.dh-bar i.low { background: var(--orange); }
.dh-pct.ok { color: var(--mint-d); }
.dh-pct.mid { color: var(--ham-d); }
.dh-pct.low { color: var(--orange-d); }

/* ── 成就 ── */
.ach-head { display: flex; align-items: center; justify-content: space-between; margin: 20px 0 6px; }
.ach-cabinet { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; background: var(--ham-l); }
.cab-num { font-size: 36px; font-weight: 800; letter-spacing: -1.5px; line-height: 1; }
.cab-num small { font-size: 15px; color: var(--ink3); font-weight: 750; letter-spacing: 0; }
.cab-sub { font-size: 12.5px; color: var(--ink2); font-weight: 700; margin: 4px 0 8px; }
.cab-bar { height: 10px; width: 260px; max-width: 100%; border-radius: 99px; background: var(--paper); border: 2px solid var(--hairline); overflow: hidden; }
.cab-bar i { display: block; height: 100%; background: var(--orange); border-radius: 99px; transition: width 0.6s var(--ease-out-quart); }
.cab-next {
  background: var(--paper); border: 2.5px solid var(--line); border-radius: var(--r-md);
  padding: 12px 16px; min-width: 220px; box-shadow: var(--pop-sm);
}
.cab-next small { font-size: 11px; color: var(--ink3); font-weight: 700; }
.cab-next b { display: block; font-size: 16px; font-weight: 800; margin: 3px 0 7px; }
.cab-next-bar { height: 8px; border-radius: 99px; background: var(--warm); border: 2px solid var(--hairline); overflow: hidden; margin-bottom: 5px; }
.cab-next-bar i { display: block; height: 100%; background: var(--orange); border-radius: 99px; }

.latest-card { display: flex; align-items: center; gap: 16px; margin-top: 14px; background: var(--ham-l); }
.latest-body { flex: 1; min-width: 0; }
.latest-name { font-size: 18px; font-weight: 800; letter-spacing: -0.4px; }
.latest-desc { font-size: 12.5px; color: var(--ink2); font-weight: 650; margin-top: 2px; }

/* 六边形勋章（clip-path + drop-shadow 硬投影，沿用项目成就系统） */
.hex {
  width: 52px; height: 52px; flex: none;
  clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
  display: grid; place-items: center;
  filter: drop-shadow(2.5px 2.5px 0 var(--line));
}
.hex .icon { width: 24px; height: 24px; }
.hex.r-铜 { background: #ecd9c3; color: #8a5a2b; }
.hex.r-银 { background: #e9edf1; color: #5f6b76; }
.hex.r-金 { background: #f6e7ae; color: #8a6d0b; }
.hex.r-钻 { background: #daf0fa; color: #2c6e8a; }
.hex.r-locked { background: var(--warm); color: var(--ink3); }

.latest-card .hex { width: 64px; height: 64px; }
.latest-card .hex .icon { width: 30px; height: 30px; }

.chip-r-copper { background: #ecd9c3; color: #8a5a2b; }
.chip-r-silver { background: #e9edf1; color: #5f6b76; }
.chip-r-gold { background: #f6e7ae; color: #8a6d0b; }
.chip-r-diamond { background: #daf0fa; color: #2c6e8a; }

/* 分组 */
.ach-group { margin-top: 16px; }
.ach-group-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.ach-group-name { font-size: 13px; font-weight: 800; color: var(--ink2); }
.ach-group-name b { color: var(--orange-d); }
.ach-group-progress {
  width: 60px; height: 6px; border-radius: 99px; background: var(--warm);
  position: relative; overflow: hidden;
}
.ach-group-progress::after {
  content: ''; position: absolute; inset: 0; width: var(--p);
  background: var(--mint); border-radius: 99px; transition: width 0.5s var(--ease-out-quart);
}
.ach-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
@media (max-width: 800px) { .ach-grid { grid-template-columns: repeat(2, 1fr); } }
.ach-card {
  position: relative; text-align: center; padding: 14px 10px 12px;
  display: flex; flex-direction: column; align-items: center; gap: 7px;
}
.ach-card.locked { border-style: dashed; background: var(--cream); box-shadow: none; opacity: 0.75; }
.ach-rarity {
  position: absolute; top: 8px; right: 8px;
  font-size: 10px; font-weight: 800; padding: 1px 8px; border-radius: 99px; border: 1.5px solid var(--line);
}
.ach-name { font-size: 13.5px; font-weight: 800; }
.ach-desc { font-size: 11px; color: var(--ink3); font-weight: 700; min-height: 14px; }
.ach-bar { width: 82%; height: 7px; border-radius: 99px; background: var(--warm); border: 2px solid var(--hairline); overflow: hidden; }
.ach-bar i { display: block; height: 100%; background: var(--ham); border-radius: 99px; transition: width 0.5s var(--ease-out-quart); }
.ach-card:not(.locked) .ach-bar i { background: var(--mint); }
</style>
