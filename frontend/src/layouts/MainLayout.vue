<template>
  <div class="app">
    <div class="deco" aria-hidden="true">
      <span class="blob b1"></span><span class="blob b2"></span><span class="blob b3"></span>
    </div>

    <aside class="sidebar">
      <div class="logo" @click="router.push('/today')" aria-label="回到今日">
        <svg viewBox="0 0 24 24" fill="none" style="stroke:var(--ink)" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2.5" y="7" width="14" height="14" rx="3.5" style="fill:var(--paper)" />
          <path d="M6.5 3h11a3 3 0 0 1 3 3v10" />
          <path d="M6.5 11h6M6.5 15.5h8" />
        </svg>
      </div>
      <div class="brand" @click="router.push('/today')" title="回到今日">TUNTUN</div>

      <button v-for="item in navItems" :key="item.path" class="nav-item"
              :class="{ on: route.path.startsWith(item.path) }"
              @click="router.push(item.path)" :aria-label="item.label">
        <svg class="icon"><use :href="item.icon" /></svg>
        <span class="tip">{{ item.label }}</span>
      </button>

      <div class="nav-spacer"></div>

      <!-- 专注进行中：侧栏迷你进度（跨页存活），点击回到专注页 -->
      <button v-if="focusStore.hasActiveSession" class="nav-mini" :class="{ paused: focusStore.paused }"
              :aria-label="focusStore.paused ? `专注已暂停 ${focusClock}` : `专注进行中，剩余 ${focusClock}`"
              @click="router.push('/focus')">
        <svg class="icon"><use href="#i-timer" /></svg>
        <span>{{ focusClock }}</span>
      </button>

      <div class="theme-slot">
        <button class="nav-item theme-btn" :class="{ on: themeOpen }" @click="themeOpen = !themeOpen"
                :aria-expanded="themeOpen" aria-label="切换配色主题">
          <svg class="icon"><use href="#i-palette" /></svg>
          <span class="tip">主题 · {{ themeName }}</span>
        </button>

        <Transition name="gooey">
          <div v-if="themeOpen" class="theme-pop" role="radiogroup" aria-label="配色主题" @click.stop>
            <div class="tp-title">配色主题</div>
            <button
              v-for="(m, i) in THEME_META" :key="m.key" class="tp-item"
              :class="{ on: themeIndex === i }" role="radio" :aria-checked="themeIndex === i"
              @click="onThemeSelect(i)"
            >
              <!-- 主题图标：每主题一枚 app 图标插画 -->
              <span class="tp-iconbox" aria-hidden="true">
                <img class="tp-icon" :src="m.icon" :alt="m.label" />
              </span>
              <span class="tp-info">
                <b>{{ m.label }}</b>
                <small>{{ m.sub }}</small>
              </span>
              <svg v-if="themeIndex === i" class="tp-check"><use href="#i-check" /></svg>
            </button>
          </div>
        </Transition>
      </div>

      <button class="nav-item" @click="router.push('/decks')" aria-label="卡组">
        <svg class="icon"><use href="#i-library" /></svg>
        <span class="tip">卡组</span>
      </button>
      <div class="avatar" @click="router.push('/me')" :title="userStore.user?.username">{{ avatarText }}</div>
    </aside>

    <main class="main theming-fade">
      <router-view v-slot="{ Component }">
        <Transition name="view">
          <component :is="Component" :key="route.path" />
        </Transition>
      </router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useFocusStore } from '@/stores/focus'
import { useTheme, THEME_META } from '@/composables/useTheme'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const focusStore = useFocusStore()
const { name: themeName, index: themeIndex, setThemeByIndex, cycle } = useTheme()

/** 侧栏迷你进度的时钟（mm:ss，随 store 250ms 一次 tick 更新） */
const focusClock = computed(() => {
  const m = String(Math.floor(focusStore.remaining / 60)).padStart(2, '0')
  const s = String(focusStore.remaining % 60).padStart(2, '0')
  return `${m}:${s}`
})

const themeOpen = ref(false)

function onThemeSelect(i: number) {
  setThemeByIndex(i)
}

// 点击别处 / Esc 收起主题浮层
function onDocClick(e: MouseEvent) {
  const el = e.target as HTMLElement
  if (el.closest('.theme-slot')) return
  themeOpen.value = false
}
function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') themeOpen.value = false
}
// Shift + T 循环切换（保留原来的快速切主题手感）
function onHotkey(e: KeyboardEvent) {
  if (e.shiftKey && (e.key === 'T' || e.key === 't')) {
    const t = e.target as HTMLElement
    if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return
    cycle()
  }
}
onMounted(() => {
  document.addEventListener('click', onDocClick)
  document.addEventListener('keydown', onKey)
  document.addEventListener('keydown', onHotkey)
})
onUnmounted(() => {
  document.removeEventListener('click', onDocClick)
  document.removeEventListener('keydown', onKey)
  document.removeEventListener('keydown', onHotkey)
})

const navItems = [
  { path: '/today', label: '今日', icon: '#i-home' },
  { path: '/review', label: '复习', icon: '#i-cards' },
  { path: '/library', label: '内容库', icon: '#i-folder' },
  { path: '/reader', label: '阅读器', icon: '#i-book' },
  { path: '/extract', label: 'AI 提炼', icon: '#i-scissor' },
  { path: '/focus', label: '专注', icon: '#i-timer' },
  { path: '/stats', label: '统计', icon: '#i-chart' },
]

const avatarText = computed(() => (userStore.user?.username || '囤').slice(0, 1))
</script>

<style scoped>
.app {
  position: relative;
  z-index: 1;
  display: flex;
  min-height: 100vh;
}

.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 92px;
  z-index: 20;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 7px;
  padding: 20px 0 18px;
  background: var(--paper);
  border-right: 2.5px solid var(--line);
}

.logo {
  width: 52px;
  height: 52px;
  border-radius: 17px;
  margin-bottom: 4px;
  flex: none;
  overflow: hidden;
  background: var(--ham);
  border: 2.5px solid var(--line);
  box-shadow: var(--pop-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.42s var(--ease-out-quart);
  cursor: pointer;
}
.logo:hover { transform: rotate(-8deg) scale(1.08); }
.logo svg { width: 30px; height: 30px; }

.brand {
  font-size: 11px;
  font-weight: 800;
  color: var(--ink2);
  letter-spacing: 0.5px;
  margin: 0 0 14px;
  cursor: pointer;
}

.nav-item {
  position: relative;
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ink3);
  border: 2.5px solid transparent;
  background: none;
  cursor: pointer;
  transition: all 0.28s var(--ease-out-quart);
}
.nav-item .icon { width: 21px; height: 21px; stroke-width: 2; }
.nav-item:hover { background: var(--warm); color: var(--ink2); }
.nav-item.on {
  background: var(--orange);
  color: var(--onfill);
  border-color: var(--line);
  box-shadow: var(--pop-sm);
  transform: rotate(-3deg);
}
.nav-item.on .icon { stroke-width: 2.3; }

.nav-item .tip {
  position: absolute;
  left: 66px;
  top: 50%;
  transform: translateY(-50%) translateX(-6px);
  background: var(--ink);
  color: var(--onink);
  font-size: 12.5px;
  padding: 5px 11px;
  border-radius: 9px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: all 0.28s var(--ease);
  z-index: 30;
  font-weight: 600;
}
.nav-item:hover .tip { opacity: 1; transform: translateY(-50%) translateX(0); }

.nav-spacer { flex: 1; }

/* ── 专注迷你进度（侧栏，跨页存活） ── */
.nav-mini {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  width: 52px;
  padding: 7px 0;
  border-radius: 15px;
  border: 2.5px solid var(--line);
  background: var(--orange);
  color: var(--onfill);
  box-shadow: var(--pop-sm);
  font-size: 10.5px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  cursor: pointer;
  transition: transform 0.2s var(--ease-out-quart);
}
.nav-mini:hover { transform: rotate(-2deg) scale(1.06); }
.nav-mini .icon { width: 15px; height: 15px; animation: miniTick 1s var(--ease) infinite; }
.nav-mini.paused { background: var(--ham-l); color: var(--ham-d); }
.nav-mini.paused .icon { animation: none; }
@keyframes miniTick {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.45; }
}

/* ── 主题切换浮层（列表式选择器） ── */
.theme-slot {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 45;
}
.theme-pop {
  position: absolute;
  left: 62px;
  top: 50%;
  transform: translateY(-50%);
  width: 250px;
  padding: 10px 8px 8px;
  background: var(--paper);
  border: 3px solid var(--line);
  /* 左上一角切大、另外三角小圆角，呼应主题图标与整个贴纸系统的轮廓 */
  border-radius: 24px 20px 20px 20px;
  box-shadow: 5px 5px 0 var(--line);
  z-index: 45;
}
.tp-title { font-size: 11.5px; font-weight: 800; color: var(--ink3); padding: 0 9px 8px; letter-spacing: 0.04em; }
.tp-item {
  display: flex; align-items: center; gap: 12px; width: 100%;
  padding: 9px 10px; border-radius: 16px; border: 3px solid transparent;
  background: none; cursor: pointer; font-family: inherit; text-align: left;
  transition: background 0.15s ease, border-color 0.15s ease;
}
.tp-item:hover { background: var(--warm); }
.tp-item.on { border-color: var(--line); background: var(--ham-l); }

/* 主题图标：44px 圆角方块，描边 + 硬投影嵌进贴纸系统。
   图标本身是整版 app 图标插画，圆角与外框都由这里统一处理。 */
.tp-iconbox {
  position: relative;
  flex: none;
  width: 44px;
  height: 44px;
  border-radius: 13px;
  overflow: hidden;
  border: 3px solid var(--line);
  box-shadow: var(--pop-sm);
  background: var(--warm);
}
.tp-icon { display: block; width: 100%; height: 100%; object-fit: cover; }

.tp-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.tp-info b { font-size: 13.5px; font-weight: 800; color: var(--ink); }
.tp-info small { font-size: 11px; color: var(--ink3); font-weight: 650; }
.tp-check { width: 16px; height: 16px; flex: none; color: var(--mint-d); }
.gooey-enter-active {
  animation: gooeyIn 0.34s var(--ease-out-quint) both;
}
.gooey-leave-active {
  animation: gooeyOut 0.16s cubic-bezier(0.3, 0, 0.8, 0.15) both;
}
@keyframes gooeyIn {
  from { opacity: 0; transform: translateY(-50%) translateX(-10px) scale(0.96); }
  to { opacity: 1; transform: translateY(-50%) translateX(0) scale(1); }
}
@keyframes gooeyOut {
  from { opacity: 1; transform: translateY(-50%) translateX(0) scale(1); }
  to { opacity: 0; transform: translateY(-50%) translateX(-8px) scale(0.97); }
}

.avatar {
  width: 42px;
  height: 42px;
  border-radius: 15px;
  flex: none;
  background: var(--mint-l);
  border: 2.5px solid var(--line);
  box-shadow: var(--pop-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 800;
  color: var(--mint-d);
  transition: transform 0.4s var(--ease-out-quart);
  cursor: pointer;
}
.avatar:hover { transform: scale(1.1) rotate(7deg); }

.main {
  flex: 1;
  margin-left: 92px;
  padding: 28px 40px 28px;
  max-width: 1200px;
  position: relative;
  transition: opacity 0.3s var(--ease), filter 0.3s var(--ease);
}
@media (max-width: 760px) {
  .main { padding: 20px 18px 80px; }
}
</style>
