<template>
  <div>
    <div class="decks-head">
      <div>
        <div class="h-page">卡组</div>
        <div class="h-sub">把不同类型的卡片分门别类，复习时按卡组拉取</div>
      </div>
      <button class="btn btn-primary" @click="openCreateDeck">新建卡组</button>
    </div>

    <!-- 卡组网格 -->
    <div class="deck-grid" v-if="decks.length">
      <div v-for="d in decks" :key="d.id" class="card deck-item" :class="{ on: selected?.id === d.id }"
           @click="selectDeck(d)">
        <div class="deck-name">{{ d.name }}</div>
        <div class="deck-count">{{ d.card_count }} 张</div>
        <div class="deck-desc" v-if="d.description">{{ d.description }}</div>
      </div>
    </div>
    <div class="card empty" v-else>
      <p>还没有卡组。建一个，比如「英语·词根」或「考研政治·马原」。</p>
    </div>

    <!-- 选中卡组 → 卡片列表 -->
    <div v-if="selected" class="card cards-panel">
      <div class="cards-head">
        <div>
          <div class="h-sec">{{ selected.name }} · 卡片</div>
          <div class="h-sub">共 {{ cards.length }} 张</div>
        </div>
        <button class="btn" @click="openCreateCard">新建卡片</button>
      </div>

      <div class="card-list" v-if="cards.length">
        <div v-for="c in cards" :key="c.id" class="card-row">
          <span class="c-tag" :class="c.card_type">{{ typeLabel(c.card_type) }}</span>
          <span class="c-front">{{ c.front.slice(0, 60) }}{{ c.front.length > 60 ? '…' : '' }}</span>
          <span class="c-state">{{ stateLabel(c.state) }}</span>
        </div>
      </div>
      <p class="muted" v-else>这个卡组还没有卡片，点「新建卡片」加一张。</p>
    </div>

    <!-- 遮罩 + 弹窗 -->
    <div v-if="modal" class="mask" @click.self="modal = null">
      <div class="card modal-card">
        <h3 class="modal-title">{{ modal === 'deck' ? '新建卡组' : '新建卡片' }}</h3>

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
          <label class="field"><span>背面</span>
            <textarea v-model="cardForm.back" rows="3" placeholder="答案 / 释义" /></label>
          <label class="field"><span>标签（逗号分隔）</span><input v-model="cardForm.tags" placeholder="四级,动词" /></label>
        </template>

        <p class="err" v-if="modalError">{{ modalError }}</p>

        <div class="modal-actions">
          <button class="btn" @click="modal = null">取消</button>
          <button class="btn btn-primary" :disabled="saving" @click="submitModal">{{ saving ? '保存中…' : '保存' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { decksApi } from '@/api/decks'
import { cardsApi } from '@/api/cards'
import type { Card, Deck } from '@/types/api'

const decks = ref<Deck[]>([])
const cards = ref<Card[]>([])
const selected = ref<Deck | null>(null)
const modal = ref<'deck' | 'card' | null>(null)
const modalError = ref('')
const saving = ref(false)

const deckForm = reactive({ name: '', description: '' })
const cardForm = reactive({ card_type: 'basic', front: '', back: '', tags: '' })

function typeLabel(t: string) {
  return { basic: '问答', cloze: '挖空', quote: '书摘', image: '图片' }[t] || t
}
function stateLabel(s: string) {
  return { new: '新卡', learning: '学习中', review: '复习', relearning: '重学', suspended: '已挂起', buried: '已埋藏' }[s] || s
}

async function loadDecks() {
  const res = await decksApi.list()
  decks.value = res.data
}

async function selectDeck(d: Deck) {
  selected.value = d
  const res = await cardsApi.list({ deck_id: d.id, limit: 100 })
  cards.value = res.data.items
}

function openCreateDeck() {
  deckForm.name = ''
  deckForm.description = ''
  modalError.value = ''
  modal.value = 'deck'
}

function openCreateCard() {
  cardForm.card_type = 'basic'
  cardForm.front = ''
  cardForm.back = ''
  cardForm.tags = ''
  modalError.value = ''
  modal.value = 'card'
}

async function submitModal() {
  saving.value = true
  modalError.value = ''
  try {
    if (modal.value === 'deck') {
      await decksApi.create({ name: deckForm.name, description: deckForm.description })
      await loadDecks()
    } else if (selected.value) {
      await cardsApi.create({
        deck_id: selected.value.id,
        card_type: cardForm.card_type,
        front: cardForm.front,
        back: cardForm.back,
        tags: cardForm.tags.split(/[,，]/).map((t) => t.trim()).filter(Boolean),
      })
      await selectDeck(selected.value)
    }
    modal.value = null
  } catch (e) {
    modalError.value = '保存失败，请重试'
  } finally {
    saving.value = false
  }
}

onMounted(loadDecks)
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
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 14px;
}
.deck-item {
  padding: 18px 18px 16px;
  cursor: pointer;
  transition: transform 0.15s var(--ease-out-quart), box-shadow 0.15s var(--ease-out-quart);
}
.deck-item:hover { transform: translate(-2px, -2px); box-shadow: var(--pop); }
.deck-item.on { border-color: var(--orange); box-shadow: var(--pop); }
.deck-name { font-size: 16px; font-weight: 800; letter-spacing: -0.3px; }
.deck-count { font-size: 13px; color: var(--orange-d); font-weight: 800; margin-top: 6px; }
.deck-desc { font-size: 12px; color: var(--ink3); margin-top: 4px; }

.empty { padding: 28px; text-align: center; color: var(--ink2); font-size: 14px; }

.cards-panel { margin-top: 22px; padding: 20px 22px; }
.cards-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}
.card-list { display: flex; flex-direction: column; gap: 8px; }
.card-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 2px solid var(--hairline);
  border-radius: 12px;
}
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
.c-front { flex: 1; font-size: 14px; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.c-state { flex: none; font-size: 12px; color: var(--ink3); font-weight: 700; }
.muted { color: var(--ink2); font-size: 13.5px; margin-top: 8px; }

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
