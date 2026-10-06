<template>
  <span
    ref="rootRef"
    class="cc"
    role="status"
    :aria-busy="status === 'running' || undefined"
    :data-status="status"
    :data-mounted="mounted ? '' : undefined"
    :style="{ '--cc-expected': expectedMs + 'ms' }"
  >
    <!-- 进度填充：running 线性走到 90% 悬停等真实结果；done 冲刺 + 绿 wash；error 停在原地 + 红 wash -->
    <span ref="fillRef" class="cc-fill" aria-hidden="true"></span>

    <!-- 图标：tool / check / retry 三态上下滚动切换 -->
    <span class="cc-glyph" aria-hidden="true">
      <span v-for="g in GLYPHS" :key="g" class="cc-g" :data-state="glyphState(g)">
        <svg class="icon"><use :href="glyphIcon(g)" /></svg>
      </span>
    </span>

    <span class="cc-name">{{ name }}</span>
    <span v-if="argument" class="cc-arg">{{ argument }}</span>
    <span v-if="showTimer" ref="timerRef" class="cc-timer">0 ms</span>

    <!-- 失败后整个 chip 可点重试（透明按钮覆盖，保住键盘可达性） -->
    <button
      v-if="status === 'error'"
      type="button"
      class="cc-retry"
      :aria-label="`重试 ${name}`"
      @click="emit('retry')"
    />
    <span class="sr-only">{{ announce }}</span>
  </span>
</template>

<script setup lang="ts">
/** 贴纸风 CallChip：交互时序移植自 vue-bits CallChip（进度悬停/冲刺/抖动/图标滚动/计时器），
    视觉层按三主题贴纸系统重写——颜色全部走 CSS 变量，不写死深色假设。 */
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

export type CallChipStatus = 'idle' | 'running' | 'done' | 'error'

interface Props {
  icon?: string // SVG sprite id，如 '#i-doc'
  name?: string
  argument?: string
  status?: CallChipStatus
  /** 进度条走到 90% 的预估时长（ms），真实结果先到就立即跳终态 */
  expectedMs?: number
  showTimer?: boolean
  shake?: number
}

const props = withDefaults(defineProps<Props>(), {
  icon: '#i-doc',
  name: '处理中',
  argument: '',
  status: 'running',
  expectedMs: 2500,
  showTimer: true,
  shake: 5,
})
const emit = defineEmits<{ retry: [] }>()

const HOLD_AT = 0.9
const SHAKE = [0, -1, 1, -0.66, 0.66, -0.33, 0]
const GLYPHS = ['tool', 'check', 'retry'] as const
type Glyph = (typeof GLYPHS)[number]

const WORDS: Record<CallChipStatus, string> = { running: '进行中', done: '完成', error: '失败', idle: '排队中' }

const fmt = (ms: number) => (ms < 10000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`)
const reduceMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
const glyphOf = (s: CallChipStatus): Glyph => (s === 'done' ? 'check' : s === 'error' ? 'retry' : 'tool')
const glyphIcon = (g: Glyph) => (g === 'check' ? '#i-check' : g === 'retry' ? '#i-refresh' : props.icon)

const rootRef = ref<HTMLElement | null>(null)
const fillRef = ref<HTMLElement | null>(null)
const timerRef = ref<HTMLElement | null>(null)
const mounted = ref(false)
const announce = ref('')
const glyph = computed(() => glyphOf(props.status))
const prevGlyph = ref<Glyph | null>(null)
watch(glyph, (_next, prev) => (prevGlyph.value = prev))

let isMounted = false
let fraction = 0
let liveFraction = 0
const clock = { ms: 0 }
let shakeAnim: Animation | null = null
let stopTimer: (() => void) | undefined

const setFraction = (f: number, instant: boolean) => {
  const fill = fillRef.value
  if (!fill) return
  fraction = f
  if (instant) fill.style.transition = 'none'
  fill.style.transform = `scaleX(${f})`
  if (instant) {
    void fill.getBoundingClientRect() // 强制回流，避免「无过渡」设置被后续过渡吞掉
    fill.style.transition = ''
  }
}

const apply = (s: CallChipStatus, animate: boolean) => {
  if (s === 'running') {
    shakeAnim?.cancel()
    setFraction(0, true)
    if (animate) setFraction(HOLD_AT, false)
  } else if (s === 'done') {
    setFraction(1, !animate)
  } else if (s === 'error') {
    setFraction(Math.min(1, Math.max(0, liveFraction)), true)
    if (animate && props.shake > 0 && !reduceMotion() && rootRef.value) {
      shakeAnim = rootRef.value.animate(
        SHAKE.map((k) => ({ transform: `translateX(${k * props.shake}px)`, easing: 'cubic-bezier(0.77, 0, 0.175, 1)' })),
        { duration: 450, composite: 'add' },
      )
    }
  } else setFraction(0, true)
}

const startTimer = (s: CallChipStatus) => {
  stopTimer?.()
  stopTimer = undefined
  const write = (ms: number) => {
    clock.ms = ms
    if (timerRef.value) timerRef.value.textContent = fmt(ms)
  }
  if (s !== 'running') {
    if ((s === 'idle' || !clock.ms) && timerRef.value) timerRef.value.textContent = '—'
    return
  }
  const startedAt = performance.now()
  write(0)
  if (reduceMotion()) {
    const id = setInterval(() => write(performance.now() - startedAt), 100)
    stopTimer = () => {
      clearInterval(id)
      write(performance.now() - startedAt)
    }
    return
  }
  let raf = 0
  const tick = () => {
    write(performance.now() - startedAt)
    raf = requestAnimationFrame(tick)
  }
  tick()
  stopTimer = () => {
    cancelAnimationFrame(raf)
    write(performance.now() - startedAt)
  }
}

const updateAnnounce = (s: CallChipStatus) => {
  const ms = props.showTimer && clock.ms ? Math.round(clock.ms) : 0
  const when = s === 'done' && ms ? `，用时 ${ms} ms` : s === 'error' && ms ? `，${ms} ms 后失败` : ''
  announce.value = `${props.name} ${props.argument}，${WORDS[s]}${when}`
}

onMounted(() => {
  isMounted = true
  mounted.value = true
  apply(props.status, props.status === 'running')
  startTimer(props.status)
  updateAnnounce(props.status)
})
onUnmounted(() => {
  isMounted = false
  shakeAnim?.cancel()
  stopTimer?.()
})
watch(
  () => props.status,
  () => {
    const fill = fillRef.value
    liveFraction = fill ? new DOMMatrix(getComputedStyle(fill).transform).a : fraction
  },
  { flush: 'pre' },
)
watch(
  () => props.status,
  (s) => {
    if (isMounted) apply(s, true)
    startTimer(s)
    updateAnnounce(s)
  },
  { flush: 'post' },
)

const glyphState = (g: Glyph) => (g === glyph.value ? 'in' : g === prevGlyph.value ? 'out' : undefined)
</script>

<style scoped>
.cc {
  position: relative;
  display: inline-flex;
  align-items: center;
  box-sizing: border-box;
  max-width: 100%;
  height: 36px;
  padding: 0 12px;
  gap: 8px;
  border-radius: var(--r-sm);
  background: var(--paper);
  border: 2.5px solid var(--line);
  box-shadow: var(--pop-sm);
  color: var(--ink);
  font-size: 12.5px;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
  overflow: hidden;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
  transition: transform 0.16s var(--ease-out-quart), border-color 0.2s var(--ease-out-quart);
}
.cc:active { transform: scale(0.97); }
.cc[data-status='done'] { border-color: var(--mint-d); }
.cc[data-status='error'] { border-color: var(--berry); cursor: pointer; }

/* 进度填充 */
.cc-fill {
  position: absolute;
  inset: 0;
  transform-origin: left;
  transform: scaleX(0);
  pointer-events: none;
  background: color-mix(in srgb, var(--orange) 14%, transparent);
}
.cc:not([data-mounted]) .cc-fill { transition: none !important; }
.cc[data-mounted] .cc-fill { transition: transform var(--cc-expected) linear; }
.cc[data-status='done'] .cc-fill {
  background: color-mix(in srgb, var(--mint) 16%, transparent);
  clip-path: inset(0 0 0 0);
  transition: transform 0.2s var(--ease-out-quart), background-color 0.12s ease, clip-path 0.4s var(--ease-out-quart) 0.2s;
}
.cc[data-status='error'] .cc-fill {
  background: color-mix(in srgb, var(--berry) 15%, transparent);
  transition: background-color 0.2s ease;
}

/* 图标三态滚动 */
.cc-glyph { position: relative; flex: none; width: 16px; height: 16px; overflow: hidden; }
.cc-g {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  opacity: 0;
  filter: blur(3px);
  transform: translateY(70%);
}
.cc-g[data-state='in'] {
  opacity: 1;
  filter: none;
  transform: none;
  transition: opacity 0.24s var(--ease-out-quint), transform 0.24s var(--ease-out-quint), filter 0.24s var(--ease-out-quint);
}
.cc-g[data-state='out'] {
  transform: translateY(-70%);
  transition: opacity 0.16s var(--ease-in-quart), transform 0.16s var(--ease-in-quart), filter 0.16s var(--ease-in-quart);
}
.cc-g .icon { width: 100%; height: 100%; }
.cc[data-status='running'] .cc-g[data-state='in'] { animation: ccBreath 1.6s var(--ease) infinite; }
@keyframes ccBreath {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.45; }
}
.cc[data-status='done'] .cc-g[data-state='in'] { color: var(--mint-d); animation: none; }
.cc[data-status='error'] .cc-g[data-state='in'] { color: var(--berry); animation: none; }

.cc-name { position: relative; font-weight: 800; overflow: hidden; text-overflow: ellipsis; }
.cc-arg { position: relative; color: var(--ink2); overflow: hidden; text-overflow: ellipsis; }
.cc-timer {
  position: relative;
  color: var(--ink3);
  min-width: 6ch;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.cc-retry {
  position: absolute;
  inset: 0;
  background: transparent;
  border: 0;
  padding: 0;
  margin: 0;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
  border: 0;
}

@media (prefers-reduced-motion: reduce) {
  .cc-g, .cc-fill { transition: none !important; animation: none !important; filter: none !important; transform: none; }
  .cc-g[data-state='out'] { opacity: 0; }
  .cc:active { transform: none; }
}
</style>
