import { computed, ref } from 'vue'

import cocoaIcon from '@/assets/themes/theme-cocoa.png'
import nightIcon from '@/assets/themes/theme-night.png'
import mintIcon from '@/assets/themes/theme-mint.png'

const THEMES = ['cocoa', 'night', 'mint'] as const
export type Theme = (typeof THEMES)[number]

/** 侧边/登录页共用的短标签 */
const LABELS: Record<Theme, string> = { cocoa: '暖奶油', night: '夜读', mint: '薄荷' }
/** 主题选择器里的完整名称 */
const NAMES: Record<Theme, string> = { cocoa: '可可奶油', night: '夜读深色', mint: '薄荷晨间' }

/** 每个主题的粒子配色（对应 GooeyNav 的 --color-1..4） */
const PARTICLE_COLORS: Record<Theme, [string, string, string, string]> = {
  cocoa: ['#ff8b4a', '#ffce8e', '#38c79c', '#8b7bf5'],
  night: ['#ff9263', '#f3b25f', '#4fd8ac', '#a79aff'],
  mint: ['#2fb98c', '#159e7b', '#ff8a4c', '#7c6bf5'],
}

/** 主题选择器图标：每个主题一枚 app 图标插画（存 assets/themes/） */
const THEME_ICONS: Record<Theme, string> = {
  cocoa: cocoaIcon,
  night: nightIcon,
  mint: mintIcon,
}

/** 主题选择器用的元数据：名称 + 副标题 + 图标 */
export interface ThemeMeta {
  key: Theme
  label: string
  sub: string
  icon: string
}
const SUBS: Record<Theme, string> = { cocoa: '暖色 · 默认', night: '深色 · 护眼', mint: '冷色 · 清爽' }
export const THEME_META: ThemeMeta[] = THEMES.map((t) => ({
  key: t,
  label: NAMES[t],
  sub: SUBS[t],
  icon: THEME_ICONS[t],
}))

/** 深色底的主题（GooeyNav 指示器需要换混合模式） */
const DARK_THEMES: Theme[] = ['night']

const current = ref<Theme>('cocoa')

function apply(t: Theme) {
  current.value = t
  document.documentElement.dataset.theme = t
  localStorage.setItem('zhistack.theme', t)
}

/** 写入 / 刷新 GooeyNav 需要的全局粒子色变量 */
function syncParticleColors(t: Theme) {
  const cs = PARTICLE_COLORS[t]
  const root = document.documentElement
  cs.forEach((c, i) => root.style.setProperty(`--color-${i + 1}`, c))
}

const saved = localStorage.getItem('zhistack.theme') as Theme | null
if (saved && THEMES.includes(saved)) apply(saved)
else apply('cocoa')
syncParticleColors(current.value)

/** 主题「呼吸」：切换瞬间内容区轻微 blur + 变淡，避免颜色硬闪 */
function breathe(run: () => void, ms = 340) {
  const html = document.documentElement
  html.classList.add('theming')
  run()
  window.setTimeout(() => html.classList.remove('theming'), ms)
}

/** 三主题循环切换（登录页按钮、快捷键用） */
export function useTheme() {
  const cycle = () => breathe(() => {
    const i = THEMES.indexOf(current.value)
    const next = THEMES[(i + 1) % THEMES.length]
    apply(next)
    syncParticleColors(next)
  })

  const setTheme = (t: Theme) => {
    if (t === current.value) return
    breathe(() => {
      apply(t)
      syncParticleColors(t)
    })
  }

  const setThemeByIndex = (i: number) => {
    const t = THEMES[i]
    if (t) setTheme(t)
  }

  const label = computed(() => LABELS[current.value])
  const name = computed(() => NAMES[current.value])
  const isDark = computed(() => DARK_THEMES.includes(current.value))
  const index = computed(() => THEMES.indexOf(current.value))
  const themeItems = THEMES.map(t => ({ label: NAMES[t], href: null }))

  return {
    current, label, name, isDark, index, themeItems, THEMES, NAMES,
    cycle, setTheme, setThemeByIndex,
  }
}
