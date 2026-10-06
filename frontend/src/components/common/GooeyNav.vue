<template>
  <div class="gn-root" :class="{ compact }">
    <div class="gn-container" ref="containerRef">
      <nav class="gn-nav">
        <ul class="gn-list" ref="navRef">
          <li
            v-for="(item, index) in items"
            :key="index"
            class="gn-item"
            :class="{ active: activeIndex === index }"
          >
            <a
              :href="item.href || undefined"
              class="gn-link"
              @click="e => handleClick(e, index)"
              @keydown="e => handleKeyDown(e, index)"
            >
              {{ item.label }}
            </a>
          </li>
        </ul>
      </nav>

      <!-- 滑动指示器（贴纸风：橙底 + 可可描边 + 硬投影），带粘滞拉伸 -->
      <span class="gn-pill" ref="pillRef" aria-hidden="true" />
      <!-- 粒子爆发层 -->
      <span class="gn-burst" ref="burstRef" aria-hidden="true" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch, useTemplateRef } from 'vue'

export interface GooeyNavItem {
  label: string
  href: string | null
}

interface GooeyNavProps {
  items: GooeyNavItem[]
  animationTime?: number
  particleCount?: number
  particleDistances?: [number, number]
  particleR?: number
  timeVariance?: number
  colors?: number[]
  initialActiveIndex?: number
  compact?: boolean
}

const props = withDefaults(defineProps<GooeyNavProps>(), {
  animationTime: 600,
  particleCount: 15,
  particleDistances: () => [90, 10] as [number, number],
  particleR: 100,
  timeVariance: 300,
  colors: () => [1, 2, 3, 1, 2, 3, 1, 4],
  initialActiveIndex: 0,
  compact: false,
})

const emit = defineEmits<{ select: [index: number] }>()

const containerRef = useTemplateRef<HTMLDivElement>('containerRef')
const navRef = useTemplateRef<HTMLUListElement>('navRef')
const pillRef = useTemplateRef<HTMLSpanElement>('pillRef')
const burstRef = useTemplateRef<HTMLSpanElement>('burstRef')
const activeIndex = ref<number>(props.initialActiveIndex)

let resizeObserver: ResizeObserver | null = null
/** 每项的几何（相对容器），切项时用旧值算粘滞拉伸 */
let geo: { x: number; y: number; w: number; h: number }[] = []
let pillVisible = false

const noise = (n = 1) => n / 2 - Math.random() * n

const getXY = (distance: number, pointIndex: number, totalPoints: number): [number, number] => {
  const angle = ((360 + noise(8)) / totalPoints) * pointIndex * (Math.PI / 180)
  return [distance * Math.cos(angle), distance * Math.sin(angle)]
}

const createParticle = (i: number, t: number, d: [number, number], r: number) => {
  const rotate = noise(r / 10)
  return {
    start: getXY(d[0], props.particleCount - i, props.particleCount),
    end: getXY(d[1] + noise(7), props.particleCount - i, props.particleCount),
    time: t,
    scale: 1 + noise(0.2),
    color: props.colors[Math.floor(Math.random() * props.colors.length)],
    rotate: rotate > 0 ? (rotate + r / 20) * 10 : (rotate - r / 20) * 10,
  }
}

/** 粒子爆发：从指示器中心向外炸开一小圈彩色点（vue-bits 同款参数） */
const makeParticles = (element: HTMLElement) => {
  const d: [number, number] = props.particleDistances
  const r = props.particleR
  for (let i = 0; i < props.particleCount; i++) {
    const t = props.animationTime * 2 + noise(props.timeVariance * 2)
    const p = createParticle(i, t, d, r)
    const particle = document.createElement('span')
    const point = document.createElement('span')
    particle.classList.add('gn-particle')
    particle.style.setProperty('--start-x', `${p.start[0]}px`)
    particle.style.setProperty('--start-y', `${p.start[1]}px`)
    particle.style.setProperty('--end-x', `${p.end[0]}px`)
    particle.style.setProperty('--end-y', `${p.end[1]}px`)
    particle.style.setProperty('--time', `${p.time}ms`)
    particle.style.setProperty('--scale', `${p.scale}`)
    particle.style.setProperty('--color', `var(--color-${p.color}, var(--orange))`)
    particle.style.setProperty('--rotate', `${p.rotate}deg`)
    point.classList.add('gn-point')
    particle.appendChild(point)
    element.appendChild(particle)
    window.setTimeout(() => {
      try {
        element.removeChild(particle)
      } catch {
        /* 已移除 */
      }
    }, t)
  }
}

/** 量取每项几何（相对容器左上角），并把指示器对到当前项 */
function measure() {
  if (!containerRef.value || !navRef.value) return
  const cRect = containerRef.value.getBoundingClientRect()
  const lis = Array.from(navRef.value.querySelectorAll<HTMLElement>('li'))
  geo = lis.map(li => {
    const r = li.getBoundingClientRect()
    return { x: r.x - cRect.x, y: r.y - cRect.y, w: r.width, h: r.height }
  })
}

function setPill(to: number, from: number | null, animate: boolean) {
  const pill = pillRef.value
  const cur = geo[to]
  if (!pill || !cur) return

  const pad = 4
  let x0 = cur.x - pad
  let w0 = cur.w + pad * 2

  // 粘滞：从旧项过来时先把拉伸方向（旧的在外侧）
  if (animate && from != null && geo[from]) {
    const prev = geo[from]
    const stretch = Math.min(Math.abs(cur.x - prev.x) * 0.34, 34)
    if (cur.x > prev.x) {
      // 向右：先向左拉伸，把旧的盖住
      x0 = cur.x - pad - stretch
      w0 = cur.w + pad * 2 + stretch
    } else {
      x0 = cur.x - pad
      w0 = cur.w + pad * 2 + stretch
    }
  }

  pill.style.width = `${w0}px`
  pill.style.height = `${cur.h + pad * 2}px`
  pill.style.setProperty('--pill-x', `${x0}px`)
  pill.style.setProperty('--pill-y', `${cur.y - pad}px`)
  pill.style.setProperty('--pill-w', `${cur.w + pad * 2}px`)

  if (!animate) {
    pill.classList.add('no-anim')
    pillVisible = true
    void pill.offsetWidth
    pill.classList.remove('no-anim')
    return
  }

  const settle = Math.max(320, props.animationTime)
  pill.style.setProperty('--pill-time', `${settle}ms`)
  pill.classList.remove('moving')
  void pill.offsetWidth
  pill.classList.add('moving')
}

/** 外部调用：跟随外部主题状态（不触发粒子） */
function setActive(index: number, animate = false) {
  if (index < 0 || index >= props.items.length) return
  if (activeIndex.value === index && pillVisible) return
  const from = pillVisible ? activeIndex.value : null
  activeIndex.value = index
  nextTick(() => {
    measure()
    setPill(index, animate ? from : null, animate)
  })
}

function switchTo(index: number) {
  const li = navRef.value?.querySelectorAll('li')[index] as HTMLElement | undefined
  if (!li) return
  const from = pillVisible ? activeIndex.value : null
  activeIndex.value = index
  measure()
  setPill(index, from, true)
  if (burstRef.value) makeParticles(burstRef.value)
}

const handleClick = (e: Event, index: number) => {
  e.preventDefault()
  if (activeIndex.value === index) return
  switchTo(index)
  emit('select', index)
}

const handleKeyDown = (e: KeyboardEvent, index: number) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    handleClick(e, index)
  }
}

// 外部改了 activeIndex（比如父组件同步）时，指示器跟进并量几何
watch(activeIndex, () => {
  nextTick(() => {
    measure()
    setPill(activeIndex.value, null, false)
  })
})

onMounted(() => {
  nextTick(() => {
    measure()
    setPill(activeIndex.value, null, false)
  })
  resizeObserver = new ResizeObserver(() => {
    if (!pillVisible) return
    measure()
    setPill(activeIndex.value, null, false)
  })
  if (containerRef.value) resizeObserver.observe(containerRef.value)
})

onUnmounted(() => {
  resizeObserver?.disconnect()
})

defineExpose({ setActive })
</script>

<style scoped>
/* vue-bits GooeyNav 的结构与交互参数保留；视觉层换成贴纸风「粘滞滑动指示器 + 粒子爆发」，
   原因是原版的 gooey 滤镜依赖一个不受裁剪的深色遮罩层（filter::before inset:-75px），
   在侧边栏浮层这种带背景/描边的小容器里会整块变黑（详见 MEMORY.md）。 */
.gn-root {
  display: inline-block;
}
.gn-container {
  position: relative;
}
.gn-nav {
  display: flex;
  position: relative;
}
.gn-list {
  display: flex;
  gap: 2rem;
  list-style: none;
  padding: 0 1rem;
  margin: 0;
  position: relative;
  z-index: 3;
}
.gn-item {
  border-radius: 9999px;
  position: relative;
  cursor: pointer;
  color: var(--ink2);
  font-weight: 700;
  font-size: 14px;
  transition: color 0.26s var(--ease-out-quart);
}
.gn-item.active {
  color: var(--onfill);
}
.gn-link {
  outline: none;
  padding: 0.6em 1em;
  display: inline-block;
  color: inherit;
  text-decoration: none;
}

/* ── 滑动指示器 ── */
.gn-pill {
  position: absolute;
  left: 0;
  top: 0;
  width: 0;
  height: 0;
  border-radius: 9999px;
  background: var(--orange);
  border: 2.5px solid var(--line);
  box-shadow: var(--pop-sm);
  transform: translate(var(--pill-x, 0), var(--pill-y, 0));
  width: var(--pill-w, 0);
  z-index: 2;
  pointer-events: none;
  opacity: 0;
}
.gn-pill.moving,
.gn-pill.no-anim {
  opacity: 1;
}
.gn-pill:not(.no-anim) {
  opacity: 1;
  transition:
    width var(--pill-time, 460ms) var(--ease-out-quart),
    transform var(--pill-time, 460ms) var(--ease-spring);
}
.gn-pill.no-anim {
  transition: none;
}

/* ── 粒子爆发层 ── */
.gn-burst {
  position: absolute;
  left: 0;
  top: 0;
  width: 0;
  height: 0;
  z-index: 4;
  pointer-events: none;
  overflow: visible;
}
.gn-particle,
.gn-point {
  display: block;
  width: 12px;
  height: 12px;
  border-radius: 9999px;
  transform-origin: center;
}
.gn-particle {
  position: absolute;
  top: -6px;
  left: -6px;
  animation: gnParticle var(--time, 1.5s) ease 1;
}
.gn-point {
  background: var(--color, var(--orange));
  border: 1.5px solid var(--line);
  animation: gnPoint var(--time, 1.5s) ease 1;
}
@keyframes gnParticle {
  0% {
    transform: rotate(0deg) translate(calc(var(--start-x, 0px) * 0.18), calc(var(--start-y, 0px) * 0.18));
    opacity: 0;
    animation-timing-function: cubic-bezier(0.22, 1, 0.36, 1);
  }
  18% {
    opacity: 1;
  }
  62% {
    transform: rotate(calc(var(--rotate, 0deg) * 0.5))
      translate(calc(var(--end-x, 0px) * 1.1), calc(var(--end-y, 0px) * 1.1));
    opacity: 1;
  }
  100% {
    transform: rotate(calc(var(--rotate, 0deg) * 1.2)) translate(var(--end-x, 0px), var(--end-y, 0px));
    opacity: 0;
  }
}
@keyframes gnPoint {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  22% {
    transform: scale(calc(var(--scale, 1) * 1.15));
    opacity: 1;
  }
  60% {
    transform: scale(var(--scale, 1));
    opacity: 1;
  }
  100% {
    transform: scale(0);
    opacity: 0;
  }
}

/* ── 紧凑模式（登录页顶部小尺寸） ── */
.compact .gn-list {
  gap: 0.25rem;
  padding: 0 0.35rem;
}
.compact .gn-link {
  padding: 0.4em 0.72em;
}
.compact .gn-item {
  font-size: 13px;
}
.compact .gn-pill {
  border-width: 2px;
  box-shadow: 2px 2px 0 var(--line);
}

@media (prefers-reduced-motion: reduce) {
  .gn-pill {
    transition: none !important;
  }
  .gn-particle,
  .gn-point {
    animation: none;
    opacity: 0;
  }
}
</style>
