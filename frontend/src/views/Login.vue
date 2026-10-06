<template>
  <div class="auth">
    <!-- 漂浮贴纸装饰（几何 + 文字标签，非吉祥物） -->
    <div class="auth-decor" aria-hidden="true">
      <span class="sticker s1">划词 → 卡片</span>
      <span class="sticker s2">FSRS</span>
      <span class="sticker s3">溯源</span>
      <span class="sticker s4"></span>
    </div>

    <div class="auth-shell">
      <!-- 品牌区 -->
      <section class="auth-brand">
        <div class="brand-top">
          <span class="logo-mark">囤</span>
          <span class="logo-name">囤囤 TUNTUN</span>
        </div>

        <div class="brand-main">
          <h1>把知识一点点<br />囤下来</h1>
          <p class="brand-sub">单词、考点、面试题、书摘，都变成一张张会按时回来的卡片。</p>

          <ul class="brand-points">
            <li><b>划词成卡</b>读书选中一段，几秒变卡片</li>
            <li><b>FSRS 复习</b>在你快忘的时候，它刚好出现</li>
            <li><b>一键溯源</b>想不起来，跳回原文看一眼</li>
          </ul>
        </div>
      </section>

      <!-- 表单区 -->
      <section class="auth-form">
        <div class="form-top">
          <GooeyNav
            class="gooey-nav"
            compact
            :items="themeItems"
            :particle-count="15"
            :particle-distances="[90, 10]"
            :particle-r="100"
            :initial-active-index="themeIndex"
            :animation-time="600"
            :time-variance="300"
            :colors="[1, 2, 3, 1, 2, 3, 1, 4]"
            @select="setThemeByIndex"
          />
        </div>

        <div class="card form-card">
          <div class="mode-tabs">
            <button type="button" :class="{ on: mode === 'login' }" @click="mode = 'login'">登录</button>
            <button type="button" :class="{ on: mode === 'register' }" @click="mode = 'register'">注册</button>
          </div>

          <h2 class="form-title">{{ mode === 'login' ? '欢迎回来' : '开始囤卡' }}</h2>
          <p class="form-sub">{{ mode === 'login' ? '登录后，继续你的复习队列' : '30 秒建个号，今天就能开始' }}</p>

          <form @submit.prevent="submit">
            <label class="field" v-if="mode === 'register'">
              <span>邮箱</span>
              <input v-model="form.email" type="email" autocomplete="email" placeholder="you@example.com" />
            </label>
            <label class="field" v-if="mode === 'register'">
              <span>用户名</span>
              <input v-model="form.username" autocomplete="username" placeholder="2~64 个字符" />
            </label>
            <label class="field" v-else>
              <span>邮箱或用户名</span>
              <input v-model="form.account" autocomplete="username" placeholder="you@example.com" />
            </label>
            <label class="field">
              <span>密码</span>
              <input v-model="form.password" type="password" autocomplete="current-password"
                     placeholder="至少 8 位" />
            </label>

            <p class="err" v-if="error">{{ error }}</p>

            <button class="btn btn-primary submit" type="submit" :disabled="loading">
              {{ loading ? '处理中…' : mode === 'login' ? '登录' : '注册' }}
            </button>
          </form>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { AxiosError } from 'axios'
import { useUserStore } from '@/stores/user'
import { useTheme } from '@/composables/useTheme'
import GooeyNav from '@/components/common/GooeyNav.vue'
import type { ApiErrorBody } from '@/types/api'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const { themeItems, index: themeIndex, setThemeByIndex } = useTheme()

const mode = ref<'login' | 'register'>('login')
const loading = ref(false)
const error = ref('')

const form = reactive({
  email: '',
  username: '',
  account: '',
  password: '',
})

function extractError(e: unknown): string {
  const err = e as AxiosError<ApiErrorBody>
  return err.response?.data?.message || '网络错误，请稍后再试'
}

async function submit() {
  error.value = ''
  loading.value = true
  try {
    if (mode.value === 'login') {
      await userStore.login(form.account, form.password)
    } else {
      await userStore.register(form.email, form.username, form.password)
    }
    const redirect = (route.query.redirect as string) || '/today'
    router.push(redirect)
  } catch (e) {
    error.value = extractError(e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
}

/* ── 漂浮贴纸 ── */
.auth-decor {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.sticker {
  position: absolute;
  border: 2.5px solid var(--line);
  border-radius: 14px;
  box-shadow: var(--pop-sm);
  font-weight: 800;
  font-size: 13px;
  letter-spacing: 0.3px;
  animation: float 6s ease-in-out infinite;
}
.s1 { background: var(--orange); color: var(--onfill); padding: 9px 14px; top: 16%; left: 6%; transform: rotate(-8deg); }
.s2 { background: var(--mint); color: var(--onfill); padding: 9px 12px; top: 30%; right: 44%; transform: rotate(7deg); animation-delay: -2s; }
.s3 { background: var(--grape); color: var(--onink); padding: 9px 14px; bottom: 14%; left: 12%; transform: rotate(5deg); animation-delay: -4s; }
.s4 { background: var(--ham); width: 40px; height: 40px; bottom: 20%; right: 46%; transform: rotate(-14deg); animation-delay: -1s; }
@keyframes float {
  0%, 100% { translate: 0 0; }
  50% { translate: 0 -12px; }
}

/* ── 分屏 ── */
.auth-shell {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  min-height: 100vh;
}

/* ── 品牌区 ── */
.auth-brand {
  display: flex;
  flex-direction: column;
  padding: 40px clamp(28px, 5vw, 64px);
  background:
    radial-gradient(120% 140% at 0% 0%, var(--hero-hl), transparent 55%),
    linear-gradient(160deg, var(--hero-a), var(--hero-b));
  color: var(--hero-ink);
  border-right: 2.5px solid var(--line);
}
.brand-top {
  display: flex;
  align-items: center;
  gap: 12px;
}
.logo-mark {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--orange);
  color: var(--onfill);
  border: 2.5px solid var(--line);
  border-radius: 13px;
  box-shadow: var(--pop-sm);
  font-weight: 800;
  font-size: 20px;
}
.logo-name {
  font-size: 19px;
  font-weight: 800;
  letter-spacing: -0.3px;
}

.brand-main {
  margin: auto 0;
  padding: 48px 0;
}
.brand-main h1 {
  font-size: clamp(2.1rem, 4.2vw, 3.2rem);
  font-weight: 800;
  line-height: 1.12;
  letter-spacing: -1px;
}
.brand-sub {
  margin-top: 18px;
  font-size: 15.5px;
  color: var(--hero-sub);
  max-width: 30em;
  font-weight: 500;
}
.brand-points {
  list-style: none;
  margin-top: 34px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.brand-points li {
  font-size: 14px;
  color: var(--hero-sub);
  font-weight: 500;
}
.brand-points b {
  color: var(--hero-ink);
  font-weight: 800;
  margin-right: 8px;
}

/* ── 表单区 ── */
.auth-form {
  display: flex;
  flex-direction: column;
  padding: 28px clamp(24px, 4vw, 56px) 48px;
}
.form-top {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}
.gooey-nav {
  display: inline-block;
  padding: 4px 2px;
}

.form-card {
  margin: auto 0;
  width: min(420px, 100%);
  padding: 30px 30px 28px;
  box-shadow: var(--pop);
}

.mode-tabs {
  display: inline-flex;
  gap: 5px;
  padding: 5px;
  background: var(--warm);
  border: 2.5px solid var(--line);
  border-radius: 999px;
  margin-bottom: 22px;
}
.mode-tabs button {
  padding: 7px 20px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 750;
  color: var(--ink2);
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.15s var(--ease-out);
}
.mode-tabs button.on {
  background: var(--paper);
  color: var(--ink);
  box-shadow: var(--pop-sm);
  border: 2px solid var(--line);
}

.form-title {
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.5px;
}
.form-sub {
  font-size: 13.5px;
  color: var(--ink2);
  margin: 6px 0 24px;
}

.field {
  display: block;
  margin-bottom: 16px;
}
.field span {
  display: block;
  font-size: 12.5px;
  font-weight: 750;
  color: var(--ink2);
  margin-bottom: 6px;
}
.field input {
  width: 100%;
  padding: 12px 14px;
  font-family: inherit;
  font-size: 14.5px;
  color: var(--ink);
  background: var(--cream);
  border: 2.5px solid var(--line);
  border-radius: 12px;
  outline: none;
  transition: transform 0.15s var(--ease-out-quart), box-shadow 0.15s var(--ease-out-quart),
    border-color 0.15s var(--ease-out);
}
.field input:focus {
  border-color: var(--orange);
  box-shadow: 3px 3px 0 var(--line);
  transform: translate(-1px, -1px);
}
.field input::placeholder {
  color: var(--ink3);
}

.err {
  color: var(--berry);
  font-size: 13px;
  font-weight: 650;
  margin: 2px 0 12px;
}

.submit {
  width: 100%;
  margin-top: 6px;
  font-size: 15.5px;
  padding: 13px 18px;
}
.submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ── 响应式 ── */
@media (max-width: 900px) {
  .auth-shell {
    grid-template-columns: 1fr;
  }
  .auth-brand {
    border-right: none;
    border-bottom: 2.5px solid var(--line);
    padding: 24px 22px 28px;
  }
  .brand-main {
    margin: 0;
    padding: 28px 0 8px;
  }
  .brand-main h1 {
    font-size: clamp(1.8rem, 8vw, 2.4rem);
  }
  .brand-sub {
    margin-top: 12px;
    font-size: 14px;
  }
  .brand-points {
    display: none;
  }
  .auth-form {
    padding: 20px 20px 40px;
  }
  .form-card {
    margin: 0 auto;
  }
  .sticker.s2, .sticker.s4 { display: none; }
}
</style>
