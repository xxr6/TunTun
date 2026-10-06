<template>
  <button
    ref="buttonRef"
    type="button"
    class="hb"
    :disabled="disabled"
    :data-phase="phase"
    :data-input="input ?? undefined"
    :aria-describedby="hintId"
    :style="cssVars"
    @pointerdown="handlePointerDown"
    @pointermove="handlePointerMove"
    @pointerup="endPointer($event)"
    @pointercancel="endPointer($event, { drifted: true })"
    @lostpointercapture="endPointer($event, { drifted: true })"
    @pointerleave="handlePointerLeave"
    @keydown="handleKeyDown"
    @keyup="handleKeyUp"
    @contextmenu.prevent
  >
    <span class="hb-pulse" aria-hidden="true"></span>

    <!-- 双层标签：底层墨字 / 上层填充字，随填充推进露出 -->
    <span class="hb-labels">
      <span class="hb-l" :class="{ out: phase === 'done' }" :aria-hidden="phase === 'done'">
        <span v-if="$slots.icon" class="hb-ic"><slot name="icon" /></span>
        <slot>按住丢弃</slot>
      </span>
      <span class="hb-l hb-l-done" :class="{ in: phase === 'done' }" :aria-hidden="phase !== 'done'">
        <span v-if="$slots.doneIcon" class="hb-ic"><slot name="doneIcon" /></span>
        {{ doneLabel }}
      </span>
    </span>

    <!-- 填充层：clip-path 从左推进 + 波浪前缘 -->
    <span class="hb-clip" aria-hidden="true">
      <span class="hb-fill">
        <span class="hb-labels">
          <span class="hb-l" :class="{ out: phase === 'done' }" aria-hidden="true">
            <span v-if="$slots.icon" class="hb-ic"><slot name="icon" /></span>
            <slot>按住丢弃</slot>
          </span>
          <span class="hb-l hb-l-done" :class="{ in: phase === 'done' }" aria-hidden="true">
            <span v-if="$slots.doneIcon" class="hb-ic"><slot name="doneIcon" /></span>
            {{ doneLabel }}
          </span>
        </span>
      </span>
      <span class="hb-crest"></span>
    </span>

    <span :id="hintId" class="sr-only">按住 {{ Math.round(holdTime / 100) / 10 }} 秒确认{{ doneLabel }}</span>
  </button>
</template>

<script setup lang="ts">
/** 贴纸风长按确认按钮：交互时序移植自 vue-bits HoldButton（rAF 进度、波浪前缘、
    pointer capture、漂移取消、键盘长按、tap 检测、reduce-motion 降级），
    视觉层按三主题贴纸系统重写——危险动作用莓果粉填充，无发光。 */
import { computed, onMounted, onUnmounted, ref, watch, useId, type CSSProperties } from 'vue'

export type HoldPhase = 'idle' | 'holding' | 'done'

interface Props {
  doneLabel?: string
  holdTime?: number
  releaseTime?: number
  pressScale?: number
  wave?: boolean
  waveAmplitude?: number
  resetAfter?: number
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  doneLabel: '已丢弃',
  holdTime: 1500,
  releaseTime: 200,
  pressScale: 0.96,
  wave: true,
  waveAmplitude: 6,
  resetAfter: 1200,
  disabled: false,
})
const emit = defineEmits<{ hold: []; tap: [] }>()

const TAP_MS = 250
const HIT_PAD = 10
const LINEAR = (t: number) => t
const EASE_OUT = (t: number) => 1 - Math.pow(1 - t, 3)

const phase = ref<HoldPhase>('idle')
const input = ref<'pointer' | 'key' | null>(null)
let phaseNow: HoldPhase = 'idle'
let inputNow: 'pointer' | 'key' | null = null
const buttonRef = ref<HTMLButtonElement | null>(null)
const gesture = { pointerId: null as number | null, start: 0, rect: null as DOMRect | null }
const timers = { complete: 0, reset: 0 }
const hintId = useId()
let resizeObserver: ResizeObserver | null = null

const go = (next: HoldPhase, kind: 'pointer' | 'key' | null = null) => {
  phaseNow = next
  inputNow = kind
  phase.value = next
  input.value = kind
}
const clearTimers = () => {
  clearTimeout(timers.complete)
  clearTimeout(timers.reset)
}

const motion = { raf: 0, p: 0, from: 0, to: 0, start: 0 }
const drive = (to: number, duration: number, ease: (t: number) => number) => {
  const m = motion
  cancelAnimationFrame(m.raf)
  m.from = m.p
  m.to = to
  m.start = performance.now()
  const step = (now: number) => {
    const t = duration > 0 ? Math.min(1, (now - m.start) / duration) : 1
    m.p = m.from + (m.to - m.from) * ease(t)
    buttonRef.value?.style.setProperty('--hb-p', m.p.toFixed(4))
    if (t < 1) {
      m.raf = requestAnimationFrame(step)
      return
    }
    m.raf = 0
    if (m.to === 1) complete()
  }
  m.raf = requestAnimationFrame(step)
}

const complete = () => {
  if (phaseNow !== 'holding') return
  if (performance.now() - gesture.start < props.holdTime - 50) return
  clearTimers()
  go('done', inputNow)
  emit('hold')
  if (props.resetAfter > 0) {
    timers.reset = window.setTimeout(() => {
      go('idle')
      drive(0, props.releaseTime, EASE_OUT)
    }, props.resetAfter)
  }
}

const begin = (kind: 'pointer' | 'key') => {
  if (props.disabled || phaseNow !== 'idle') return false
  const button = buttonRef.value
  if (!button) return false
  gesture.start = performance.now()
  gesture.rect = button.getBoundingClientRect()
  go('holding', kind)
  drive(1, props.holdTime, LINEAR)
  timers.complete = window.setTimeout(complete, props.holdTime + 100)
  return true
}

const release = ({ drifted = false }: { drifted?: boolean } = {}) => {
  if (phaseNow !== 'holding') return
  clearTimers()
  const held = performance.now() - gesture.start
  go('idle')
  drive(0, props.releaseTime, EASE_OUT)
  if (!drifted && held < TAP_MS) emit('tap')
}

const handlePointerDown = (e: PointerEvent) => {
  if (e.button !== 0 || !e.isPrimary || gesture.pointerId !== null) return
  if (!begin('pointer')) return
  gesture.pointerId = e.pointerId
  try {
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
  } catch {
    /* capture unavailable */
  }
}
const endPointer = (e: PointerEvent, options?: { drifted?: boolean }) => {
  if (e.pointerId !== gesture.pointerId) return
  gesture.pointerId = null
  const el = e.currentTarget as HTMLElement
  try {
    if (el.hasPointerCapture(e.pointerId)) el.releasePointerCapture(e.pointerId)
  } catch {
    /* already released */
  }
  release(options)
}
const handlePointerMove = (e: PointerEvent) => {
  if (e.pointerId !== gesture.pointerId) return
  const r = gesture.rect
  if (!r) return
  const out =
    e.clientX < r.left - HIT_PAD || e.clientX > r.right + HIT_PAD ||
    e.clientY < r.top - HIT_PAD || e.clientY > r.bottom + HIT_PAD
  if (out) endPointer(e, { drifted: true })
}
const handlePointerLeave = (e: PointerEvent) => {
  if (e.pointerType !== 'touch') endPointer(e, { drifted: true })
}
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    if (inputNow === 'key') release({ drifted: true })
    return
  }
  if (e.key === ' ' || e.key === 'Enter') {
    e.preventDefault()
    if (!e.repeat) begin('key')
  }
}
const handleKeyUp = (e: KeyboardEvent) => {
  if (e.key === ' ' || e.key === 'Enter') {
    e.preventDefault()
    if (inputNow === 'key') release()
  }
}

onMounted(() => {
  const button = buttonRef.value
  if (!button) return
  const measure = () => {
    button.style.setProperty('--hb-w', `${button.offsetWidth}px`)
    button.style.setProperty('--hb-h', `${button.offsetHeight}px`)
  }
  measure()
  resizeObserver = new ResizeObserver(measure)
  resizeObserver.observe(button)
})
onUnmounted(() => {
  resizeObserver?.disconnect()
  clearTimers()
  cancelAnimationFrame(motion.raf)
})

watch(phase, (next, _prev, onCleanup) => {
  if (next !== 'holding') return
  const cancel = () => release({ drifted: true })
  const onVisibility = () => {
    if (document.hidden) cancel()
  }
  window.addEventListener('blur', cancel)
  document.addEventListener('visibilitychange', onVisibility)
  onCleanup(() => {
    window.removeEventListener('blur', cancel)
    document.removeEventListener('visibilitychange', onVisibility)
  })
})

const cssVars = computed(
  () =>
    ({
      '--hb-hold': `${props.holdTime}ms`,
      '--hb-cycles': String(props.holdTime / 1100),
      '--hb-release': `${props.releaseTime}ms`,
      '--hb-press': String(props.pressScale),
      '--hb-wave': `${props.wave ? props.waveAmplitude : 0}px`,
    }) as CSSProperties,
)
</script>

<style scoped>
.hb {
  --hb-p: 0;
  position: relative;
  display: inline-grid;
  isolate: isolation;
  place-items: center;
  height: 38px;
  padding: 0 16px;
  border-radius: var(--r-sm);
  background: var(--paper);
  border: 2.5px solid var(--line);
  box-shadow: var(--pop-sm);
  color: var(--ink2);
  font-family: inherit;
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.01em;
  white-space: nowrap;
  cursor: pointer;
  user-select: none;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  transition: transform 0.16s var(--ease-out-quart), background-color 0.16s ease, box-shadow var(--hb-release) var(--ease-out-quart);
}
.hb:hover { background: color-mix(in srgb, var(--paper) 92%, var(--orange)); }
.hb:disabled { opacity: 0.5; cursor: default; pointer-events: none; }
.hb[data-phase='holding'][data-input='pointer'] { transform: scale(var(--hb-press)); }
.hb[data-phase='done'] {
  transform: translateY(-2px);
  border-color: var(--berry);
  box-shadow: var(--pop);
}

/* 完成脉冲环（贴纸风：低透明 berry 扩散一次） */
.hb-pulse {
  position: absolute;
  inset: 0;
  border-radius: var(--r-sm);
  pointer-events: none;
  opacity: 0;
}
.hb[data-phase='done'] .hb-pulse { animation: hbPulse 0.6s var(--ease-out-quart) forwards; }
@keyframes hbPulse {
  from { opacity: 1; box-shadow: 0 0 0 0 color-mix(in srgb, var(--berry) 45%, transparent); }
  to { opacity: 0; box-shadow: 0 0 0 12px color-mix(in srgb, var(--berry) 0%, transparent); }
}

/* 标签双层：普通 / 完成 */
.hb-labels { position: relative; z-index: 2; display: grid; place-items: center; }
.hb-l {
  grid-area: 1 / 1;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  transition: opacity 0.2s ease, filter 0.2s ease;
}
.hb-l.out { opacity: 0; filter: blur(2px); }
.hb-l-done { opacity: 0; filter: blur(2px); }
.hb-l-done.in { opacity: 1; filter: none; }
.hb-ic { display: inline-flex; flex: none; }
.hb-ic :deep(svg) { width: 14px; height: 14px; display: block; }

/* 填充层：clip-path 从左推进，前缘波浪 */
.hb-clip {
  position: absolute;
  inset: 0;
  z-index: 3;
  pointer-events: none;
  clip-path: inset(0 round var(--r-sm));
}
.hb-fill {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  background: var(--berry);
  color: var(--onfill);
  clip-path: inset(0 calc((1 - var(--hb-p)) * (100% + 0.75 * var(--hb-wave)) - var(--hb-p) * 0.25 * var(--hb-wave)) 0 0);
}
.hb-crest {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  background: var(--berry);
  color: var(--onfill);
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='200' viewBox='0 0 20 200' preserveAspectRatio='none'%3E%3Cpath d='M0 0H10C18 8 18 25.3 10 33.3S2 58.7 10 66.7S18 92 10 100S2 125.3 10 133.3S18 158.7 10 166.7S2 192 10 200H0Z'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='200' viewBox='0 0 20 200' preserveAspectRatio='none'%3E%3Cpath d='M0 0H10C18 8 18 25.3 10 33.3S2 58.7 10 66.7S18 92 10 100S2 125.3 10 133.3S18 158.7 10 166.7S2 192 10 200H0Z'/%3E%3C/svg%3E");
  -webkit-mask-repeat: repeat-y;
  mask-repeat: repeat-y;
  -webkit-mask-size: var(--hb-wave) calc(var(--hb-h, 38px) * 2);
  mask-size: var(--hb-wave) calc(var(--hb-h, 38px) * 2);
  -webkit-mask-position-x: calc(-1 * var(--hb-wave) + var(--hb-p) * (var(--hb-w, 120px) + var(--hb-wave)));
  mask-position-x: calc(-1 * var(--hb-wave) + var(--hb-p) * (var(--hb-w, 120px) + var(--hb-wave)));
  -webkit-mask-position-y: calc(-1 * var(--hb-p) * var(--hb-cycles) * var(--hb-h, 38px));
  mask-position-y: calc(-1 * var(--hb-p) * var(--hb-cycles) * var(--hb-h, 38px));
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
  .hb { transform: none !important; transition: background-color 160ms ease, box-shadow 200ms ease !important; }
  .hb-fill { clip-path: inset(0) !important; opacity: 0; transition: opacity var(--hb-release) ease !important; }
  .hb[data-phase='holding'] .hb-fill, .hb[data-phase='done'] .hb-fill { opacity: 1; transition: opacity var(--hb-hold) linear !important; }
  .hb-crest { display: none; }
  .hb-pulse { animation: none !important; }
  .hb-l { filter: none !important; transition: opacity 200ms ease !important; }
}
</style>
