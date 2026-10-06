<template>
  <div>
    <div class="row between wrap gap12 rise" style="margin-bottom:18px">
      <div>
        <div class="h-page">个人中心</div>
        <div class="h-sub">你的账号、时区与这段时间囤下的成果</div>
      </div>
    </div>

    <div class="me-grid">
      <!-- 左：资料 -->
      <div>
        <div class="card pad rise">
          <div class="me-profile">
            <div class="me-avatar">{{ avatarText }}</div>
            <div style="flex:1;min-width:0">
              <div class="me-name">{{ user?.username }}</div>
              <div class="muted" style="font-size:13px">{{ user?.email }}</div>
              <div class="muted" style="font-size:12px;margin-top:2px">{{ joinText }}</div>
            </div>
          </div>

          <label class="me-field">
            <span>时区</span>
            <div class="row gap8">
              <select v-model="timezone" class="me-select" @change="saveTimezone" aria-label="时区">
                <option v-for="z in TIMEZONES" :key="z.value" :value="z.value">{{ z.label }}</option>
              </select>
              <span v-if="tzSaved" class="chip chip-m">已保存</span>
            </div>
            <small class="muted">专注/签到的「今天」按这个时区切天。</small>
          </label>
        </div>

        <div class="card pad rise" style="margin-top:14px">
          <div class="h-sec" style="margin-bottom:10px">这段时间囤下了</div>
          <div class="me-stats">
            <div class="me-stat"><b>{{ overview.total_cards.toLocaleString() }}</b><span>张卡片</span></div>
            <div class="me-stat"><b>{{ overview.total_reviews.toLocaleString() }}</b><span>次复习</span></div>
            <div class="me-stat"><b>{{ fmtH(overview.focus_seconds) }}</b><span>专注时长</span></div>
            <div class="me-stat"><b>{{ checkin.total_days }}</b><span>天签到</span></div>
          </div>
          <button class="btn btn-ghost" style="width:100%;margin-top:12px" @click="router.push('/stats')">
            <svg class="icon"><use href="#i-crown" /></svg>查看成就收藏柜
          </button>
        </div>
      </div>

      <!-- 右：账号操作 -->
      <div>
        <div class="card pad rise">
          <div class="h-sec" style="margin-bottom:6px">主题</div>
          <div class="muted" style="font-size:12.5px;margin-bottom:12px">在侧边栏调色板切换，或按 Shift + T 快速循环。</div>
          <div class="row gap8 wrap">
            <button v-for="(m, i) in THEME_META" :key="m.key" class="me-theme" :class="{ on: themeIndex === i }"
                    :aria-label="'切换' + m.label" @click="setThemeByIndex(i)">
              <img class="me-theme-ic" :src="m.icon" alt="" />{{ m.label }}
            </button>
          </div>
        </div>

        <div class="card pad rise" style="margin-top:14px">
          <div class="h-sec" style="margin-bottom:8px">账号</div>
          <button class="btn btn-danger" style="width:100%" @click="confirmLogout = true">
            <svg class="icon"><use href="#i-close" /></svg>退出登录
          </button>
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
import { statsApi } from '@/api/stats'
import { useUserStore } from '@/stores/user'
import { useTheme, THEME_META } from '@/composables/useTheme'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import type { CheckinStatus, StatsOverview } from '@/types/api'

const router = useRouter()
const userStore = useUserStore()
const { index: themeIndex, setThemeByIndex } = useTheme()

const user = computed(() => userStore.user)
const timezone = ref('Asia/Shanghai')
const tzSaved = ref(false)
const overview = ref<StatsOverview>({ total_cards: 0, total_decks: 0, total_reviews: 0, today_reviews: 0, focus_seconds: 0 })
const checkin = ref<CheckinStatus>({ checked: false, streak: 0, total_days: 0, month_days: 0, new_achievements: [] })
const confirmLogout = ref(false)

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

const avatarText = computed(() => (user.value?.username || '囤').slice(0, 1))
const joinText = computed(() => {
  const t = user.value?.created_at
  return t ? `加入于 ${new Date(t).toLocaleDateString('zh-CN')}` : ''
})

function fmtH(s: number) {
  return s >= 3600 ? (s / 3600).toFixed(1) + 'h' : Math.round(s / 60) + 'min'
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

onMounted(async () => {
  timezone.value = user.value?.timezone || 'Asia/Shanghai'
  try {
    const [o, c] = await Promise.all([statsApi.overview(), checkinApi.status()])
    overview.value = o.data
    checkin.value = c.data
  } catch {
    /* 忽略 */
  }
})
</script>

<style scoped>
.me-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 14px; align-items: start; }
@media (max-width: 860px) { .me-grid { grid-template-columns: 1fr; } }
.pad { padding: 18px 20px; }

.me-profile { display: flex; align-items: center; gap: 14px; margin-bottom: 18px; }
.me-avatar {
  width: 60px; height: 60px; border-radius: 20px; flex: none;
  display: flex; align-items: center; justify-content: center;
  background: var(--mint-l); border: 2.5px solid var(--line); box-shadow: var(--pop-sm);
  font-size: 24px; font-weight: 800; color: var(--mint-d);
}
.me-name { font-size: 19px; font-weight: 800; letter-spacing: -0.4px; }

.me-field { display: block; margin-bottom: 4px; }
.me-field > span { display: block; font-size: 12.5px; font-weight: 750; color: var(--ink2); margin-bottom: 6px; }
.me-field small { display: block; font-size: 11.5px; margin-top: 6px; }
.me-select {
  flex: 1; min-width: 0; font-family: inherit; font-size: 13.5px; font-weight: 700;
  color: var(--ink); background: var(--cream); border: 2.5px solid var(--line);
  border-radius: 11px; padding: 8px 11px; outline: none;
}
.me-select:focus-visible { outline: 2.5px solid var(--line); outline-offset: 2px; }

.me-stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.me-stat {
  background: var(--cream); border: 2px solid var(--hairline); border-radius: 13px;
  padding: 12px 14px; display: flex; flex-direction: column;
}
.me-stat b { font-size: 20px; font-weight: 800; font-variant-numeric: tabular-nums; }
.me-stat span { font-size: 11.5px; color: var(--ink2); margin-top: 1px; font-weight: 650; }

.me-theme {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 8px 13px; border-radius: 999px; font-size: 13px; font-weight: 750;
  color: var(--ink2); background: var(--paper); border: 2px solid var(--hairline); cursor: pointer;
  font-family: inherit; transition: all 0.2s var(--ease);
}
.me-theme.on { border-color: var(--line); box-shadow: var(--pop-sm); color: var(--ink); background: var(--warm); }
.me-theme-ic { width: 20px; height: 20px; border-radius: 6px; border: 2px solid var(--line); object-fit: cover; }

.btn-danger { background: var(--berry); color: var(--onfill); border-color: var(--line); }
</style>
