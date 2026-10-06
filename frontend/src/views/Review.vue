<template>
  <div class="rev-wrap">
    <!-- 顶部：关闭 + 进度线 + 计数 -->
    <div class="rev-top">
      <button class="btn btn-ghost" style="padding:8px 13px" @click="exit" aria-label="退出复习">
        <svg class="icon" style="width:16px;height:16px"><use href="#i-close" /></svg>
      </button>
      <div class="prog-line"><i :style="{ width: progress + '%' }"></i></div>
      <div class="rev-count"><span>{{ index + 1 }}</span> / {{ queue.length }} · 还剩 <b>{{ remaining }}</b></div>
    </div>

    <!-- 翻卡 -->
    <div class="flip-wrap" :class="{ leaving, entering }">
      <div class="flip-card" ref="flipCardEl" :style="{ '--ry': ry + 'deg' }" @click="flip.toggle()">
        <div class="face">
          <span class="face-tag chip-p" v-if="current">{{ current.deck_name }}</span>
          <div class="face-q" v-if="current" v-html="renderFront(current)"></div>
          <div class="src-link" v-if="current && current.tags?.length">
            <svg class="icon"><use href="#i-link" /></svg><span>{{ current.tags.join(' · ') }}</span>
          </div>
          <div class="flip-hint">按空格或点一下卡片，看答案</div>
        </div>
        <div class="face face-back">
          <span class="face-tag chip-m">答案</span>
          <div class="face-a" v-if="current" v-html="renderBack(current)"></div>
          <div class="src-link" v-if="current">
            <svg class="icon"><use href="#i-link" /></svg><span>回到原文位置</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 评分 -->
    <div class="rate-grid" v-if="current">
      <button v-for="r in RATINGS" :key="r.value" class="rate" :data-r="r.value" @click.stop="rate(r.value)">
        <span class="rk">{{ r.value }}</span>
        <div class="rn">{{ r.name }}</div>
        <div class="ri">{{ r.hint }}</div>
      </button>
    </div>
    <div class="rate-hint">{{ rateHint }}</div>

    <!-- 键盘提示 -->
    <div class="row gap16 wrap" style="margin-top:16px;justify-content:center;font-size:12.5px;color:var(--ink3);font-weight:700">
      <span class="row gap8"><kbd>空格</kbd>翻面</span>
      <span class="row gap8"><kbd>1-4</kbd>评分</span>
      <span class="row gap8"><kbd>U</kbd>撤销</span>
      <span class="row gap8"><kbd>Esc</kbd>退出</span>
    </div>

    <!-- 卡片历史 -->
    <div class="card pad" v-if="current" style="margin-top:20px;background:var(--warm)">
      <div class="row gap8">
        <svg class="icon" style="width:16px;height:16px;color:var(--orange-d)"><use href="#i-brain" /></svg>
        <span style="font-size:13.5px;font-weight:750">这张卡在你脑子里的历史</span>
      </div>
      <div class="muted" style="font-size:13px;margin-top:7px;line-height:1.75">
        已经复习过 {{ current.reps }} 次 · 记忆稳定性 {{ stabilityText }} · 上次评了「{{ lastRatingText }}」。
      </div>
    </div>

    <!-- 完成态 -->
    <div v-if="!current && !loading" class="card pad" style="text-align:center;margin-top:40px">
      <h2 style="font-size:22px;font-weight:800;margin-bottom:8px">今天的卡复习完了</h2>
      <p class="muted">还剩 {{ remaining }} 张未到期，会按时回来的。</p>
      <button class="btn btn-primary" style="margin-top:18px" @click="exit">回到今日</button>
    </div>

    <p class="err" v-if="error">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { reviewApi } from '@/api/review'
import { useSpringFlip } from '@/composables/useSpringFlip'
import type { ReviewCard } from '@/types/api'

const router = useRouter()
const flip = useSpringFlip()
const { ry } = flip

const flipCardEl = ref<HTMLElement>()

/** 量正反面内容自然高、取大者钉死卡片高度（迁移 demo 的 lockFlipH）。
    face 是 absolute 脱流的，不锁高的话内容长的一面会溢出、和评分按钮重叠。 */
function lockFlipH() {
  const card = flipCardEl.value
  if (!card) return
  card.style.height = '0px'
  const front = card.querySelector<HTMLElement>('.face')
  const back = card.querySelector<HTMLElement>('.face-back')
  const h = Math.max(front?.scrollHeight ?? 0, back?.scrollHeight ?? 0, 320)
  card.style.height = h + 'px'
}

const queue = ref<ReviewCard[]>([])
const index = ref(0)
const remaining = ref(0)
const leaving = ref(false)
const entering = ref(false)
const loading = ref(true)
const error = ref('')
const rateHint = ref('选一个，系统会按你的历史表现安排下次见面的时间')
const lastRatingText = ref('想起来了')
const canUndo = ref(false)
let lastAnswered: ReviewCard | null = null

const current = computed(() => queue.value[index.value] ?? null)
// 进度含当前这张（demo 同款：1/5 时进度线就是 20%）
const progress = computed(() => (queue.value.length ? ((index.value + 1) / queue.value.length) * 100 : 0))
const stabilityText = computed(() => (current.value ? `${Math.max(1, Math.round(current.value.reps * 1.6))} 天` : '—'))

const RATINGS = [
  { value: 1, name: '忘了', hint: '10 分钟后再来' },
  { value: 2, name: '有点卡', hint: '1 天后' },
  { value: 3, name: '想起来了', hint: '6 天后' },
  { value: 4, name: '太简单', hint: '15 天后' },
]

function escapeHtml(s: string) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}
function renderFront(card: ReviewCard): string {
  if (card.card_type === 'cloze') {
    return escapeHtml(card.front).replace(/\{\{c\d+::([^}]+)\}\}/g, '<span class="cloze">····</span>')
  }
  return escapeHtml(card.front)
}
function renderBack(card: ReviewCard): string {
  if (card.card_type === 'cloze') {
    return escapeHtml(card.front).replace(/\{\{c\d+::([^}]+)\}\}/g, '<span class="cloze">$1</span>')
  }
  return escapeHtml(card.back || card.front)
}

async function loadQueue() {
  loading.value = true
  try {
    const res = await reviewApi.queue()
    queue.value = res.data.items
    remaining.value = res.data.remaining_today
    index.value = 0
    flip.reset()
    await nextTick()
    lockFlipH()
  } catch {
    error.value = '加载复习队列失败'
  } finally {
    loading.value = false
  }
}

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms))
}

async function rate(rating: number) {
  const card = current.value
  if (!card || leaving.value) return
  error.value = ''
  lastAnswered = card
  canUndo.value = true
  lastRatingText.value = RATINGS.find((r) => r.value === rating)?.name || '想起来了'

  leaving.value = true
  await sleep(240)
  index.value++
  flip.reset()
  leaving.value = false
  entering.value = true
  await nextTick()
  lockFlipH()
  await sleep(340)
  entering.value = false

  reviewApi
    .answer({ card_id: card.card_id, rating })
    .then((res) => {
      remaining.value = res.data.remaining_today
      const days = res.data.scheduled_days
      rateHint.value = days < 1 ? `下次见面在 ${Math.round(days * 24 * 60)} 分钟后` : `下次见面在 ${Math.round(days)} 天后`
    })
    .catch(() => {
      queue.value.splice(index.value, 0, card)
      error.value = '评分没发出去，这张卡已放回'
    })
}

async function undoLast() {
  if (!lastAnswered) return
  const card = lastAnswered
  try {
    await reviewApi.undo(card.card_id)
    index.value = Math.max(0, index.value - 1)
    queue.value[index.value] = card
    flip.reset()
    await nextTick()
    lockFlipH()
    lastAnswered = null
    canUndo.value = false
    error.value = ''
  } catch {
    error.value = '撤销失败'
  }
}

function exit() {
  router.push('/today')
}

function onKeydown(e: KeyboardEvent) {
  if (!current.value) return
  if (e.key === ' ' || e.code === 'Space') {
    e.preventDefault()
    flip.toggle()
  } else if (e.key >= '1' && e.key <= '4') {
    rate(Number(e.key))
  } else if (e.key === 'u' || e.key === 'U') {
    undoLast()
  } else if (e.key === 'Escape') {
    exit()
  }
}

onMounted(() => {
  loadQueue()
  window.addEventListener('keydown', onKeydown)
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.rev-wrap { max-width: 780px; margin: 0 auto; }

.flip-wrap { width: 100%; perspective: 1500px; margin-bottom: 18px; }
.flip-wrap.leaving { animation: flyOut 0.24s cubic-bezier(0.3, 0, 0.8, 0.15) forwards; }
.flip-wrap.entering { animation: flyIn 0.34s var(--ease-out-quart); }
@keyframes flyOut { to { opacity: 0; transform: translateX(-70px) rotate(-5deg); } }
@keyframes flyIn { from { opacity: 0; transform: translateX(70px); } to { opacity: 1; transform: none; } }

.flip-card {
  position: relative;
  min-height: 320px;
  cursor: pointer;
  transform-style: preserve-3d;
  transform: perspective(1900px) rotateY(var(--ry, 0deg));
  box-shadow: none;
  transition: height 0.4s var(--ease-out-quart);
}
.flip-card .face { transform-style: flat; }
@media (max-width: 560px) {
  .flip-card { min-height: 260px; }
}

kbd {
  background: var(--warm); border: 2px solid var(--line); padding: 2px 8px;
  border-radius: 7px; font-size: 11.5px; font-family: inherit;
}

.err { color: var(--berry); font-size: 13px; font-weight: 650; text-align: center; margin-top: 12px; }
</style>
