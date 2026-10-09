<template>
  <div>
    <div class="decks-head">
      <div>
        <div class="h-page">卡组</div>
        <div class="h-sub">在这里建卡组，再从阅读器、AI 提炼或手动建卡时存入</div>
      </div>
      <button class="btn btn-primary" @click="openCreateDeck">新建卡组</button>
    </div>

    <!-- 卡组网格 -->
    <div class="deck-grid" v-if="decks.length">
      <button v-for="d in decks" :key="d.id" type="button" class="card deck-item"
              :class="{ on: selected?.id === d.id }" :aria-expanded="selected?.id === d.id"
              :aria-controls="`deck-panel-${d.id}`" @click="selectDeck(d)">
        <span class="deck-folder-art" aria-hidden="true"><i></i><i></i><i></i></span>
        <span class="deck-name">{{ d.name }}</span>
        <span class="deck-count">{{ d.card_count }} 张卡片</span>
        <span class="deck-desc" v-if="d.description">{{ d.description }}</span>
        <span class="deck-toggle">{{ selected?.id === d.id ? '收起卡组' : '展开卡片' }} <span aria-hidden="true">{{ selected?.id === d.id ? '↑' : '→' }}</span></span>
      </button>
    </div>
    <div class="card empty" v-else>
      <p>还没有卡组。建一个，比如「英语·词根」或「考研政治·马原」。</p>
      <button class="btn btn-primary" @click="openCreateDeck">新建第一个卡组</button>
    </div>

    <!-- 选中卡组 → 卡片列表 -->
    <Transition name="deck-unfold" @enter="onPanelEnter" @after-enter="onPanelAfterEnter" @leave="onPanelLeave">
    <div v-if="selected" :id="`deck-panel-${selected.id}`" :key="selected.id" class="card cards-panel">
      <div class="cards-head">
        <div>
          <div class="h-sec">{{ selected.name }} · 卡片</div>
          <div class="h-sub">共 {{ cardTotal }} 张 · {{ loadingCards ? '正在打开卡组…' : '选一张查看完整内容' }}</div>
        </div>
        <div class="cards-head-actions">
          <button class="btn" @click="closeDeck">收起</button>
          <button class="btn btn-primary" @click="openCreateCard">新建卡片</button>
        </div>
      </div>

      <div class="deck-next">
        <span>{{ cards.length ? '继续把知识放进这个卡组' : '卡组已就绪，从下面选一种方式加入卡片' }}</span>
        <div>
          <button class="btn" @click="router.push({ path: '/reader', query: { deck: selected.id } })">从阅读器摘录</button>
          <button class="btn" @click="router.push({ path: '/extract', query: { deck: selected.id } })">从 AI 提炼拆卡</button>
          <button v-if="cards.length" class="btn btn-primary" @click="router.push({ path: '/review', query: { deck: selected.id } })">复习此卡组</button>
        </div>
      </div>

      <p v-if="cardsError" class="err" role="alert">{{ cardsError }} <button class="retry-link" @click="reloadCards">重试</button></p>
      <p v-else-if="loadingCards" class="muted" role="status">正在取出卡片…</p>
      <div class="deck-browser" v-else-if="cards.length">
        <div class="card-list" role="listbox" aria-label="卡组中的卡片">
          <button v-for="(c, index) in cards" :key="c.id" type="button" class="card-row"
                  :class="{ active: activeCardId === c.id }" role="option" :aria-selected="activeCardId === c.id"
                  @click="activeCardId = c.id">
            <span class="card-row-index">{{ String(index + 1).padStart(2, '0') }}</span>
            <span class="card-row-main"><span class="c-front">{{ previewText(c.front) }}</span><span class="card-row-meta">{{ typeLabel(c.card_type) }} · {{ cardQualityError(c.card_type, c.front, c.back) ? '待补全答案' : stateLabel(c.state) }}</span></span>
            <span class="card-row-arrow" aria-hidden="true">›</span>
          </button>
          <button v-if="cards.length < cardTotal" class="load-more" :disabled="loadingMore" @click="loadMoreCards">
            {{ loadingMore ? '加载中…' : `加载更多 · 还有 ${cardTotal - cards.length} 张` }}
          </button>
          <p v-if="moreError" class="err" role="alert">{{ moreError }}</p>
        </div>
        <Transition name="card-swap" mode="out-in">
          <article v-if="activeCard" :key="activeCard.id" class="card-detail" aria-live="polite">
            <div class="card-detail-top"><span class="c-tag" :class="activeCard.card_type">{{ typeLabel(activeCard.card_type) }}</span><span class="card-detail-position">{{ activeIndex + 1 }} / {{ cardTotal }}</span></div>
            <section class="card-detail-section"><div class="card-detail-label">正面</div><div class="card-detail-text">{{ detailFront(activeCard) }}</div></section>
            <section class="card-detail-section answer"><div class="card-detail-label">背面</div><div class="card-detail-text">{{ detailBack(activeCard) }}</div></section>
            <div v-if="cardQualityError(activeCard.card_type, activeCard.front, activeCard.back)" class="card-quality-warning" role="status">
              这张卡暂不进入复习队列：{{ cardQualityError(activeCard.card_type, activeCard.front, activeCard.back) }}
            </div>
            <p v-if="activeCard.hint" class="card-detail-hint">提示：{{ activeCard.hint }}</p>
            <div v-if="activeCard.tags.length" class="card-detail-tags"><span v-for="tag in activeCard.tags" :key="tag"># {{ tag }}</span></div>
            <div class="card-detail-footer"><span>{{ stateLabel(activeCard.state) }}</span><div><button class="btn" @click="openEditCard(activeCard)">编辑卡片</button><button class="detail-nav" :disabled="activeIndex <= 0" @click="stepCard(-1)" aria-label="上一张卡片">←</button><button class="detail-nav" :disabled="activeIndex >= cards.length - 1" @click="stepCard(1)" aria-label="下一张卡片">→</button></div></div>
          </article>
        </Transition>
      </div>
      <p class="muted" v-else>这个卡组还没有卡片，点「新建卡片」加一张。</p>
    </div>
    </Transition>

    <!-- 遮罩 + 弹窗 -->
    <div v-if="modal" class="mask" @click.self="modal = null">
      <div class="card modal-card">
        <h3 class="modal-title">{{ modal === 'deck' ? '新建卡组' : modal === 'edit' ? '编辑卡片' : '新建卡片' }}</h3>

        <template v-if="modal === 'deck'">
          <label class="field"><span>名称</span><input v-model="deckForm.name" placeholder="英语·词根" /></label>
          <label class="field"><span>说明（可选）</span><input v-model="deckForm.description" placeholder="四级核心词根" /></label>
        </template>

        <template v-else>
          <label class="field"><span>类型</span>
            <select v-model="cardForm.card_type">
              <option value="basic">问答</option>
              <option value="cloze">挖空</option>
              <option value="quote">书摘</option>
            </select>
          </label>
          <label class="field"><span>正面</span>
            <textarea v-model="cardForm.front" rows="2" placeholder="问题 / 原文（挖空用 {{c1::答案}}）" /></label>
          <label class="field"><span>背面{{ cardForm.card_type === 'cloze' ? '（可选）' : '（必填）' }}</span>
            <textarea v-model="cardForm.back" rows="3" placeholder="答案 / 释义" /></label>
          <label class="field"><span>标签（逗号分隔）</span><input v-model="cardForm.tags" placeholder="四级,动词" /></label>
        </template>

        <p class="err" v-if="modalError">{{ modalError }}</p>

        <div class="modal-actions">
          <button class="btn" @click="modal = null">取消</button>
          <button class="btn btn-primary" :disabled="saving || (modal === 'deck' && !deckForm.name.trim())" @click="submitModal">{{ saving ? '保存中…' : '保存' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { decksApi } from '@/api/decks'
import { cardsApi } from '@/api/cards'
import { cardQualityError } from '@/lib/cardQuality'
import type { Card, Deck } from '@/types/api'

const decks = ref<Deck[]>([])
const route = useRoute()
const router = useRouter()
const cards = ref<Card[]>([])
const cardTotal = ref(0)
const selected = ref<Deck | null>(null)
const activeCardId = ref<string | null>(null)
const activeCard = computed(() => cards.value.find((c) => c.id === activeCardId.value) ?? null)
const activeIndex = computed(() => cards.value.findIndex((c) => c.id === activeCardId.value))
const loadingCards = ref(false)
const loadingMore = ref(false)
const cardsError = ref('')
const moreError = ref('')
let loadToken = 0
const modal = ref<'deck' | 'card' | 'edit' | null>(null)
const editingCardId = ref<string | null>(null)
const modalError = ref('')
const saving = ref(false)

const deckForm = reactive({ name: '', description: '' })
const cardForm = reactive<{ card_type: Card['card_type']; front: string; back: string; tags: string }>({ card_type: 'basic', front: '', back: '', tags: '' })

function typeLabel(t: string) {
  return { basic: '问答', cloze: '挖空', quote: '书摘', image: '图片' }[t] || t
}
function stateLabel(s: string) {
  return { new: '新卡', learning: '学习中', review: '复习', relearning: '重学', suspended: '已挂起', buried: '已埋藏' }[s] || s
}

function previewText(value: string) {
  return value.replace(/\{\{c\d+::([^}]+)\}\}/g, '＿＿＿').replace(/\s+/g, ' ').slice(0, 54) || '无标题卡片'
}

function detailFront(card: Card) {
  return card.card_type === 'cloze' ? card.front.replace(/\{\{c\d+::([^}]+)\}\}/g, '＿＿＿') : card.front
}

function detailBack(card: Card) {
  if (card.back) return card.back
  return card.card_type === 'cloze'
    ? card.front.replace(/\{\{c\d+::([^}]+)\}\}/g, '$1')
    : '这张卡片还没有背面内容'
}

function stepCard(step: number) {
  const next = cards.value[activeIndex.value + step]
  if (next) activeCardId.value = next.id
}

function onPanelEnter(el: Element) {
  const node = el as HTMLElement
  node.style.height = '0px'
  requestAnimationFrame(() => { node.style.height = `${node.scrollHeight}px` })
}
function onPanelAfterEnter(el: Element) { (el as HTMLElement).style.height = 'auto' }
function onPanelLeave(el: Element) {
  const node = el as HTMLElement
  node.style.height = `${node.scrollHeight}px`
  void node.offsetHeight
  requestAnimationFrame(() => { node.style.height = '0px' })
}

async function loadDecks() {
  const res = await decksApi.list()
  decks.value = res.data
}

async function selectDeck(d: Deck, updateUrl = true) {
  if (updateUrl && selected.value?.id === d.id) {
    closeDeck()
    return
  }
  loadToken++
  selected.value = d
  cards.value = []
  activeCardId.value = null
  cardTotal.value = d.card_count
  cardsError.value = ''
  moreError.value = ''
  if (updateUrl) router.replace({ path: '/decks', query: { deck: d.id } })
  await loadCards(d.id)
}

function closeDeck() {
  loadToken++
  selected.value = null
  cards.value = []
  activeCardId.value = null
  router.replace({ path: '/decks', query: {} })
}

async function loadCards(deckId: string, preferredCardId?: string) {
  const token = ++loadToken
  loadingCards.value = true
  cardsError.value = ''
  moreError.value = ''
  try {
    const res = await cardsApi.list({ deck_id: deckId, limit: 100 })
    if (token !== loadToken || selected.value?.id !== deckId) return
    cards.value = res.data.items
    cardTotal.value = res.data.total
    activeCardId.value = cards.value.find((c) => c.id === preferredCardId)?.id ?? cards.value[0]?.id ?? null
  } catch {
    if (token === loadToken) cardsError.value = '卡片加载失败。'
  } finally {
    if (token === loadToken) loadingCards.value = false
  }
}

function reloadCards() {
  if (selected.value) loadCards(selected.value.id)
}

async function loadMoreCards() {
  if (!selected.value || loadingMore.value || cards.value.length >= cardTotal.value) return
  const deckId = selected.value.id
  const token = loadToken
  loadingMore.value = true
  moreError.value = ''
  try {
    const res = await cardsApi.list({ deck_id: deckId, limit: 100, offset: cards.value.length })
    if (token !== loadToken || selected.value?.id !== deckId) return
    cards.value.push(...res.data.items)
    cardTotal.value = res.data.total
  } catch {
    if (token === loadToken) moreError.value = '更多卡片加载失败，请重试。'
  } finally {
    loadingMore.value = false
  }
}

function openCreateDeck() {
  deckForm.name = ''
  deckForm.description = ''
  modalError.value = ''
  modal.value = 'deck'
}

function openCreateCard() {
  editingCardId.value = null
  cardForm.card_type = 'basic'
  cardForm.front = ''
  cardForm.back = ''
  cardForm.tags = ''
  modalError.value = ''
  modal.value = 'card'
}

function openEditCard(card: Card) {
  editingCardId.value = card.id
  cardForm.card_type = card.card_type
  cardForm.front = card.front
  cardForm.back = card.back
  cardForm.tags = card.tags.join(', ')
  modalError.value = ''
  modal.value = 'edit'
}

async function submitModal() {
  if (modal.value !== 'deck') {
    const error = cardQualityError(cardForm.card_type, cardForm.front, cardForm.back)
    if (error) { modalError.value = error; return }
  }
  saving.value = true
  modalError.value = ''
  try {
    if (modal.value === 'deck') {
      const created = await decksApi.create({ name: deckForm.name.trim(), description: deckForm.description.trim() })
      await loadDecks()
      await selectDeck(created.data)
    } else if (selected.value) {
      const payload = {
        card_type: cardForm.card_type,
        front: cardForm.front.trim(),
        back: cardForm.back.trim(),
        tags: cardForm.tags.split(/[,，]/).map((t) => t.trim()).filter(Boolean),
      }
      const saved = modal.value === 'edit' && editingCardId.value
        ? await cardsApi.update(editingCardId.value, payload)
        : await cardsApi.create({ deck_id: selected.value.id, ...payload })
      const deckId = selected.value.id
      await loadDecks()
      selected.value = decks.value.find((d) => d.id === deckId) ?? selected.value
      await loadCards(deckId, saved.data.id)
    }
    modal.value = null
  } catch (e) {
    modalError.value = '保存失败，请重试'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadDecks()
  const requested = typeof route.query.deck === 'string' ? route.query.deck : null
  const match = decks.value.find((deck) => deck.id === requested)
  if (match) await selectDeck(match, false)
})
watch(() => route.query.deck, (id) => {
  const match = decks.value.find((deck) => deck.id === id)
  if (match && match.id !== selected.value?.id) selectDeck(match, false)
  else if (!id && selected.value) {
    loadToken++
    selected.value = null
  }
})
</script>

<style scoped>
.decks-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}
.h-sec { font-size: 15px; font-weight: 800; }
.h-sub { font-size: 12.5px; color: var(--ink2); margin-top: 2px; }

.deck-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
}
.deck-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-height: 174px;
  padding: 19px 18px 16px;
  text-align: left;
  font: inherit;
  color: var(--ink);
  cursor: pointer;
  overflow: hidden;
  transition: transform .32s var(--ease-out-quart), box-shadow .32s var(--ease-out-quart), background .32s ease;
}
.deck-item:hover { transform: translateY(-4px); box-shadow: var(--pop); }
.deck-item.on { border-color: var(--orange); background: var(--orange-l); box-shadow: var(--pop); }
.deck-item:focus-visible, .card-row:focus-visible, .detail-nav:focus-visible { outline: 3px solid var(--orange); outline-offset: 3px; }
.deck-folder-art { position: absolute; top: 20px; right: 20px; width: 54px; height: 40px; }
.deck-folder-art i { position: absolute; width: 34px; height: 39px; border: 2px solid var(--line); border-radius: 5px 5px 8px 8px; background: var(--paper); box-shadow: 2px 2px 0 var(--line); transition: transform .42s var(--ease-out-quart); }
.deck-folder-art i:nth-child(1) { left: 2px; top: 1px; transform: rotate(-13deg); background: var(--mint-l); }
.deck-folder-art i:nth-child(2) { left: 13px; top: 0; transform: rotate(1deg); background: var(--grape-l); }
.deck-folder-art i:nth-child(3) { left: 22px; top: 3px; transform: rotate(12deg); background: var(--orange-l); }
.deck-item.on .deck-folder-art i:nth-child(1), .deck-item:hover .deck-folder-art i:nth-child(1) { transform: translate(-4px, -4px) rotate(-20deg); }
.deck-item.on .deck-folder-art i:nth-child(3), .deck-item:hover .deck-folder-art i:nth-child(3) { transform: translate(4px, -4px) rotate(20deg); }
.deck-name { font-size: 16px; font-weight: 800; letter-spacing: -0.3px; }
.deck-count { font-size: 13px; color: var(--orange-d); font-weight: 800; margin-top: 6px; }
.deck-desc { font-size: 12px; color: var(--ink3); margin-top: 4px; }
.deck-toggle { margin-top: auto; padding-top: 18px; color: var(--ink2); font-size: 12px; font-weight: 800; }
.deck-toggle span { margin-left: 5px; font-size: 17px; }

.empty { padding: 28px; text-align: center; color: var(--ink2); font-size: 14px; }

.cards-panel { margin-top: 18px; padding: 20px 22px 22px; overflow: hidden; transform-origin: top center; }
.deck-unfold-enter-active, .deck-unfold-leave-active { transition: height .46s cubic-bezier(.22, 1, .36, 1), opacity .34s ease, transform .46s cubic-bezier(.22, 1, .36, 1), margin .46s ease; }
.deck-unfold-enter-from, .deck-unfold-leave-to { opacity: 0; transform: translateY(-12px) scale(.98); margin-top: 0; }
.deck-next { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; padding: 12px 14px; margin-bottom: 16px; border-radius: 12px; background: var(--cream); color: var(--ink2); font-size: 13px; font-weight: 700; }
.deck-next > div { display: flex; gap: 8px; flex-wrap: wrap; }
.cards-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}
.cards-head-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.deck-browser { display: grid; grid-template-columns: minmax(220px, .8fr) minmax(0, 1.4fr); gap: 14px; align-items: stretch; }
.card-list { display: flex; flex-direction: column; gap: 8px; max-height: 520px; overflow: auto; padding: 2px 4px 4px 2px; }
.card-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 11px 12px;
  border: 2px solid var(--hairline);
  border-radius: 12px;
  background: var(--paper);
  color: var(--ink);
  text-align: left;
  font: inherit;
  cursor: pointer;
  transition: transform .23s var(--ease-out-quart), border-color .23s ease, background .23s ease, box-shadow .23s ease;
}
.card-row:hover { transform: translateX(3px); border-color: var(--orange); }
.card-row.active { border-color: var(--orange); background: var(--orange-l); box-shadow: 3px 3px 0 var(--line); }
.card-row-index { flex: none; color: var(--orange-d); font-size: 11px; font-weight: 850; font-variant-numeric: tabular-nums; }
.card-row-main { flex: 1; display: flex; flex-direction: column; min-width: 0; gap: 4px; }
.card-row-meta { font-size: 11px; color: var(--ink3); }
.card-row-arrow { color: var(--orange-d); font-size: 23px; line-height: 1; }
.load-more { padding: 10px; border: 1px dashed var(--hairline); border-radius: 10px; background: transparent; color: var(--ink2); font: inherit; font-size: 12px; cursor: pointer; }
.load-more:hover { border-color: var(--orange); }
.load-more:disabled { cursor: wait; opacity: .65; }
.c-tag {
  flex: none;
  font-size: 11px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 99px;
  border: 1.5px solid var(--line);
}
.c-tag.basic { background: var(--sky-l); }
.c-tag.cloze { background: var(--grape-l); }
.c-tag.quote { background: var(--ham-l); }
.c-front { display: block; font-size: 13px; font-weight: 750; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card-detail { min-width: 0; min-height: 300px; padding: 22px; border: 2px solid var(--line); border-radius: 18px; background: var(--cream); box-shadow: 4px 4px 0 var(--line); }
.card-detail-top, .card-detail-footer { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.card-detail-position { color: var(--ink3); font-size: 12px; font-weight: 800; font-variant-numeric: tabular-nums; }
.card-detail-section { padding: 20px 0 18px; border-bottom: 1px dashed var(--hairline); }
.card-detail-section.answer { border: 0; }
.card-detail-label { color: var(--orange-d); font-size: 11px; font-weight: 850; letter-spacing: .08em; margin-bottom: 8px; }
.card-detail-text { color: var(--ink); font-size: 16px; font-weight: 700; line-height: 1.75; white-space: pre-wrap; overflow-wrap: anywhere; }
.card-detail-section.answer .card-detail-text { font-size: 14px; font-weight: 600; }
.card-quality-warning { margin: 8px 0 14px; padding: 10px 12px; border-radius: 10px; background: var(--orange-l); color: var(--orange-d); font-size: 12px; font-weight: 700; }
.card-detail-hint { color: var(--ink2); font-size: 12px; margin: 0 0 10px; }
.card-detail-tags { display: flex; gap: 6px; flex-wrap: wrap; margin: 5px 0 16px; }
.card-detail-tags span { padding: 3px 8px; background: var(--mint-l); border-radius: 99px; color: var(--mint-d); font-size: 11px; font-weight: 750; }
.card-detail-footer { padding-top: 14px; border-top: 1px solid var(--hairline); color: var(--ink3); font-size: 12px; }
.card-detail-footer > div { display: flex; gap: 6px; }
.detail-nav { width: 34px; height: 32px; border: 1.5px solid var(--line); border-radius: 9px; background: var(--paper); color: var(--ink); font: inherit; cursor: pointer; }
.detail-nav:disabled { opacity: .35; cursor: not-allowed; }
.card-swap-enter-active, .card-swap-leave-active { transition: opacity .18s ease, transform .25s var(--ease-out-quart); }
.card-swap-enter-from { opacity: 0; transform: translateX(12px); }
.card-swap-leave-to { opacity: 0; transform: translateX(-10px); }
.retry-link { border: 0; background: transparent; color: var(--orange-d); font: inherit; text-decoration: underline; cursor: pointer; }
.muted { color: var(--ink2); font-size: 13.5px; margin-top: 8px; }
@media (max-width: 760px) { .deck-browser { grid-template-columns: 1fr; } .card-list { max-height: 210px; } .cards-panel { padding: 16px; } }
@media (max-width: 480px) { .decks-head { align-items: flex-start; } .deck-grid { grid-template-columns: 1fr 1fr; gap: 10px; } .deck-item { min-height: 150px; padding: 15px 12px; } .deck-folder-art { transform: scale(.72); transform-origin: top right; right: 9px; top: 13px; } .deck-name { max-width: 75%; font-size: 14px; } .deck-desc { display: none; } .cards-head { align-items: flex-start; } .cards-head-actions .btn { padding: 8px 10px; font-size: 12px; } }
@media (prefers-reduced-motion: reduce) { .deck-unfold-enter-active, .deck-unfold-leave-active, .card-swap-enter-active, .card-swap-leave-active, .deck-item, .card-row, .deck-folder-art i { transition-duration: .01ms !important; } }

.mask {
  position: fixed;
  inset: 0;
  background: rgba(10, 7, 4, 0.48);
  z-index: 90;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.modal-card {
  width: min(440px, 100%);
  padding: 26px 26px 22px;
  box-shadow: var(--pop-lg);
}
.modal-title { font-size: 19px; font-weight: 800; margin-bottom: 18px; letter-spacing: -0.4px; }
.field { display: block; margin-bottom: 14px; }
.field span { display: block; font-size: 12.5px; font-weight: 750; color: var(--ink2); margin-bottom: 6px; }
.field input, .field textarea, .field select {
  width: 100%;
  padding: 10px 12px;
  font-family: inherit;
  font-size: 14px;
  color: var(--ink);
  background: var(--cream);
  border: 2.5px solid var(--line);
  border-radius: 12px;
  outline: none;
  resize: vertical;
}
.field input:focus, .field textarea:focus, .field select:focus { border-color: var(--orange); }
.err { color: var(--berry); font-size: 13px; font-weight: 650; margin-bottom: 10px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 6px; }
</style>
