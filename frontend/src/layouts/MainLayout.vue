<template>
  <div class="app">
    <div class="deco" aria-hidden="true">
      <span class="blob b1"></span><span class="blob b2"></span><span class="blob b3"></span>
    </div>

    <aside class="sidebar">
      <div class="logo" @click="router.push('/today')" aria-label="回到今日">
        <img :src="logoUrl" alt="囤囤 TUNTUN" />
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
              :aria-label="focusStore.mode === 'countup' ? `${focusStore.paused ? '正向计时已暂停' : '正向计时中'}，已专注 ${focusClock}` : focusStore.paused ? `专注已暂停 ${focusClock}` : `专注进行中，剩余 ${focusClock}`"
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

      <div class="avatar" @click="router.push('/me')" :title="userStore.user?.username">{{ avatarText }}</div>
    </aside>

    <main class="main theming-fade">
      <router-view v-slot="{ Component }">
        <Transition name="view">
          <KeepAlive include="Extract">
            <component :is="Component" :key="route.path" />
          </KeepAlive>
        </Transition>
      </router-view>
    </main>

    <Transition name="badge-reveal" mode="out-in">
      <div v-if="activeBadge" :key="activeBadge.name" class="badge-reveal-mask" @click.self="dismissBadge">
        <div class="badge-reveal-card" role="dialog" aria-modal="true" :aria-label="`恭喜获得${activeBadge.name}徽章`">
          <button class="badge-reveal-close" type="button" aria-label="收起徽章" @click="dismissBadge">×</button>
          <span class="badge-reveal-spark spark-a" aria-hidden="true">✦</span>
          <span class="badge-reveal-spark spark-b" aria-hidden="true">✧</span>
          <span class="badge-reveal-spark spark-c" aria-hidden="true">✦</span>
          <div class="badge-reveal-art"><img :src="badgeArt[activeBadge.name]" :alt="`${activeBadge.name}徽章`" /></div>
          <span class="badge-reveal-kicker">新徽章解锁 · {{ activeBadge.rarity }}</span>
          <h2>恭喜获得「{{ activeBadge.name }}」！</h2>
          <p>{{ activeBadge.desc }}</p>
          <button class="badge-reveal-primary" type="button" @click="dismissBadge">{{ badgeQueue.length > 1 ? '继续领取' : '收下徽章' }}</button>
          <button v-if="badgeQueue.length === 1" class="badge-reveal-link" type="button" @click="goToMyBadges">查看我的徽章 →</button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useFocusStore, formatFocusClock } from '@/stores/focus'
import { useTheme, THEME_META } from '@/composables/useTheme'
import { statsApi } from '@/api/stats'
import { badgeArt, type Badge } from '@/lib/badges'
import logoUrl from '@/assets/logo.png'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const focusStore = useFocusStore()
const { name: themeName, index: themeIndex, setThemeByIndex, cycle } = useTheme()

/** 侧栏迷你进度的时钟（mm:ss，随 store 250ms 一次 tick 更新） */
const focusClock = computed(() => {
  return formatFocusClock(focusStore.remaining)
})

const themeOpen = ref(false)
const badgeQueue = ref<Badge[]>([])
const activeBadge = computed(() => badgeQueue.value[0] ?? null)
let badgeTimer: number | null = null
let badgeCheckBusy = false
let badgeCheckAgain = false

function dismissBadge() {
  badgeQueue.value.shift()
}
function goToMyBadges() {
  dismissBadge()
  router.push('/me#my-badges')
}
async function claimBadges() {
  if (!userStore.user) return
  if (badgeCheckBusy) { badgeCheckAgain = true; return }
  badgeCheckBusy = true
  try {
    const fresh = (await statsApi.claimNewBadges()).data
    const queued = new Set(badgeQueue.value.map((badge) => badge.name))
    for (const badge of fresh) {
      if (!queued.has(badge.name)) badgeQueue.value.push(badge)
    }
  } catch {
    // The next navigation or progress change retries the notification check.
  } finally {
    badgeCheckBusy = false
    if (badgeCheckAgain) { badgeCheckAgain = false; scheduleBadgeCheck() }
  }
}
function scheduleBadgeCheck() {
  if (badgeTimer !== null) window.clearTimeout(badgeTimer)
  badgeTimer = window.setTimeout(() => { badgeTimer = null; void claimBadges() }, 220)
}
watch(() => route.fullPath, scheduleBadgeCheck)

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
  if (e.key === 'Escape' && activeBadge.value) dismissBadge()
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
  scheduleBadgeCheck()
  window.addEventListener('zhistack:achievement-progress', scheduleBadgeCheck)
  document.addEventListener('click', onDocClick)
  document.addEventListener('keydown', onKey)
  document.addEventListener('keydown', onHotkey)
})
onUnmounted(() => {
  if (badgeTimer !== null) window.clearTimeout(badgeTimer)
  window.removeEventListener('zhistack:achievement-progress', scheduleBadgeCheck)
  document.removeEventListener('click', onDocClick)
  document.removeEventListener('keydown', onKey)
  document.removeEventListener('keydown', onHotkey)
})

const navItems = [
  { path: '/today', label: '今日', icon: '#i-home' },
  { path: '/review', label: '复习', icon: '#i-cards' },
  { path: '/decks', label: '卡组', icon: '#i-library' },
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
.logo img { width: 100%; height: 100%; object-fit: cover; }

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

.badge-reveal-mask { position: fixed; inset: 0; z-index: 100; display: grid; place-items: center; padding: 18px; background: rgb(21 20 34 / 67%); backdrop-filter: blur(8px); }
.badge-reveal-card { position: relative; width: min(100%, 420px); padding: 26px 28px 28px; overflow: hidden; border: 3px solid var(--line); border-radius: 28px; background: radial-gradient(circle at 50% 34%, #fff9e5, var(--paper) 70%); box-shadow: 9px 11px 0 rgb(15 13 25 / 28%); text-align: center; }
.badge-reveal-card::before { content: ''; position: absolute; width: 300px; height: 300px; left: calc(50% - 150px); top: -52px; border-radius: 50%; background: repeating-conic-gradient(from 8deg, rgb(245 167 79 / 11%) 0 9deg, transparent 9deg 18deg); pointer-events: none; }
.badge-reveal-close { position: absolute; top: 10px; right: 15px; z-index: 2; border: 0; background: transparent; color: var(--ink2); font-size: 27px; cursor: pointer; }
.badge-reveal-art { position: relative; width: 210px; height: 210px; margin: 8px auto 0; display: grid; place-items: center; border-radius: 50%; background: radial-gradient(circle, #ffe9b2, transparent 69%); animation: badgeArtIn .65s var(--ease-out-quart) both; }
.badge-reveal-art img { width: 100%; height: 100%; object-fit: contain; filter: drop-shadow(0 10px 11px rgb(48 25 29 / 22%)); }
.badge-reveal-kicker { position: relative; display: block; margin-top: 7px; color: var(--orange-d); font-size: 12px; font-weight: 850; letter-spacing: .08em; }
.badge-reveal-card h2 { position: relative; margin: 7px 0 0; color: var(--ink); font-size: clamp(20px, 5vw, 25px); }
.badge-reveal-card p { position: relative; margin: 8px 0 20px; color: var(--ink2); font-size: 13px; }
.badge-reveal-primary { position: relative; width: 100%; padding: 12px 16px; border: 2px solid var(--line); border-radius: 14px; background: var(--orange); color: var(--onfill); box-shadow: var(--pop-sm); font: inherit; font-weight: 850; cursor: pointer; }
.badge-reveal-link { position: relative; margin-top: 14px; padding: 4px; border: 0; background: transparent; color: var(--ink2); font: inherit; font-size: 12px; font-weight: 750; cursor: pointer; }
.badge-reveal-spark { position: absolute; z-index: 1; color: #e8a34c; font-size: 24px; animation: badgeSpark 2s ease-in-out infinite; pointer-events: none; }
.badge-reveal-spark.spark-a { left: 13%; top: 19%; }
.badge-reveal-spark.spark-b { right: 14%; top: 27%; animation-delay: .4s; }
.badge-reveal-spark.spark-c { right: 26%; top: 10%; animation-delay: .8s; }
.badge-reveal-enter-active { animation: badgeMaskIn .3s ease both; }
.badge-reveal-enter-active .badge-reveal-card { animation: badgeCardIn .5s var(--ease-out-quart) both; }
.badge-reveal-leave-active { animation: badgeMaskIn .2s ease reverse both; }
@keyframes badgeMaskIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes badgeCardIn { from { opacity: 0; transform: translateY(24px) scale(.82) rotate(-5deg); } to { opacity: 1; transform: translateY(0) scale(1) rotate(0); } }
@keyframes badgeArtIn { from { transform: scale(.5) rotate(-24deg); } to { transform: scale(1) rotate(0); } }
@keyframes badgeSpark { 50% { opacity: .35; transform: scale(.7) rotate(25deg); } }
@media (prefers-reduced-motion: reduce) { .badge-reveal-mask, .badge-reveal-card, .badge-reveal-art, .badge-reveal-spark { animation: none !important; } }

.main {
  flex: 1;
  margin-left: 92px;
  padding: 28px 40px 28px;
  max-width: 1200px;
  position: relative;
  transition: opacity 0.3s var(--ease), filter 0.3s var(--ease), margin-left 0.3s var(--ease);
}
@media (max-width: 760px) {
  .main { padding: 20px 18px 80px; }
}

/* ── 屏幕自适应：中屏收窄成图标栏，窄屏转底部横栏 ── */
@media (max-width: 900px) {
  .sidebar { width: 64px; padding: 14px 0 12px; gap: 5px; }
  .logo { width: 42px; height: 42px; border-radius: 14px; }
  .brand { display: none; }
  .nav-item { width: 44px; height: 44px; border-radius: 13px; }
  .nav-item .icon { width: 19px; height: 19px; }
  .nav-item .tip { left: 52px; }
  .nav-mini { width: 44px; font-size: 9.5px; }
  .avatar { width: 36px; height: 36px; border-radius: 12px; font-size: 14px; }
  .tp-iconbox { width: 38px; height: 38px; border-radius: 11px; }
  .theme-pop { left: 54px; width: 236px; }
  .main { margin-left: 64px; padding: 20px 22px 26px; }
}

@media (max-width: 600px) {
  .app { display: block; }
  .sidebar {
    top: auto; right: 0; bottom: 0; left: 0; width: auto; height: 62px;
    flex-direction: row; justify-content: space-between; align-items: center;
    padding: 0 12px; gap: 2px;
    border-right: none; border-top: 2.5px solid var(--line);
    background: var(--paper);
  }
  .logo { width: 34px; height: 34px; border-radius: 11px; margin-bottom: 0; }
  .nav-item { width: 40px; height: 40px; border-radius: 12px; }
  .nav-item .tip { left: 50%; top: auto; bottom: calc(100% + 8px); transform: translateX(-50%) translateY(4px); }
  .nav-item:hover .tip { transform: translateX(-50%) translateY(0); }
  .nav-spacer { display: none; }
  .nav-mini { width: 44px; padding: 4px 0; font-size: 9px; border-radius: 12px; }
  .avatar { width: 32px; height: 32px; border-radius: 10px; font-size: 13px; }
  .theme-slot { position: static; }
  /* 底部栏模式：主题浮层向上弹出、水平居中 */
  .theme-pop {
    left: 50%; top: auto; bottom: 70px; width: 244px;
    transform: translateX(-50%);
    animation: none;
    border-radius: 20px;
  }
  .gooey-enter-active, .gooey-leave-active { animation: none; transition: opacity 0.18s var(--ease); }
  .main { margin-left: 0; padding: 16px 14px 84px; }
}
</style>
