<template>
  <div>
    <div class="row between wrap gap12 rise" style="margin-bottom:18px">
      <div>
        <div class="h-page">阅读器</div>
        <div class="h-sub">选中任意一段，就能把它拆成一张卡</div>
      </div>
      <span class="chip chip-o">
        <svg class="icon" style="width:14px;height:14px"><use href="#i-spark" /></svg>
        划词成卡已开启
      </span>
    </div>

    <div v-if="!docs.length && !loading" class="card pad rise" style="text-align:center;padding:48px 20px">
      <div style="font-size:15px;font-weight:800;margin-bottom:6px">还没有可阅读的文档</div>
      <div class="muted" style="font-size:13px;margin-bottom:16px">先去内容库上传一份 PDF / Markdown / TXT，解析完就能在这里划词拆卡</div>
      <button class="btn btn-primary" @click="router.push('/library')">
        <svg class="icon"><use href="#i-folder" /></svg>去内容库
      </button>
    </div>

    <div v-else class="reader-grid">
      <!-- 左：文档正文 + 划词 -->
      <div class="card pad rise rd-doc">
        <div class="doc-meta">
          <div class="doc-ic"><svg class="icon"><use href="#i-doc" /></svg></div>
          <div class="doc-info">
            <select v-model="currentDocId" class="doc-select" aria-label="选择文档">
              <option v-for="d in docs" :key="d.doc_id!" :value="d.doc_id!">{{ d.name }}</option>
            </select>
            <div class="muted doc-sub">
              {{ isPdf ? 'PDF 文档' : '文本文档' }} · 已拆出 {{ sourceCards.length }} 张卡片
            </div>
          </div>
          <!-- PDF 的 canvas 预览选不了文字，切文本视图（解析正文）即可划词成卡 -->
          <div v-if="isPdf" class="rd-tabs">
            <button :class="{ on: viewMode === 'pdf' }" @click="viewMode = 'pdf'">分页</button>
            <button :class="{ on: viewMode === 'text' }" @click="viewMode = 'text'">文本</button>
          </div>
        </div>

        <div class="doc-body" @mouseup="onSelect">
          <p v-if="docLoading" class="muted" style="text-align:center;padding:40px">加载文档中…</p>
          <pre v-else-if="viewMode === 'text'" class="doc-text">{{ textContent }}</pre>
          <VuePdfEmbed v-else :source="pdfUrl" class="rd-pdf" />
        </div>

        <!-- 划词工具条 -->
        <div v-if="selection" class="tooltip" :style="{ left: tip.x + 'px', top: tip.y + 'px' }" @mousedown.prevent>
          <button class="tip-btn" @click="generate">
            <svg class="icon" style="width:14px;height:14px"><use href="#i-spark" /></svg>生成卡片
          </button>
        </div>
      </div>

      <!-- 右列：生成预览 + 已拆卡片 -->
      <div class="rd-side">
        <div class="card pad rise">
          <div class="row gap8" style="margin-bottom:12px">
            <div class="side-ic"><svg class="icon"><use href="#i-spark" /></svg></div>
            <div class="h-sec">刚生成的卡片</div>
          </div>

          <div v-if="genState !== 'idle'" class="gen-wait">
            <CallChip
              icon="#i-scissor" name="拆卡"
              :argument="genState === 'error' ? '没拆出来，点一下再试' : '正在判断这段适合什么卡'"
              :status="genState" :expected-ms="2500" @retry="generate"
            />
          </div>
          <div v-else-if="!cards.length" class="gen-box">
            <div class="gen-ic"><svg class="icon"><use href="#i-cards" /></svg></div>
            <div class="gen-empty-t">这里还是空的</div>
            <div class="muted gen-empty-s">在左边文章里选一段话试试<br />系统会判断这段适合做成问答还是填空</div>
          </div>

          <template v-else>
            <div class="gen-list">
              <div v-for="(c, i) in cards" :key="i" class="gen-item">
                <div class="gen-item-head">
                  <select v-model="c.card_type">
                    <option value="basic">问答</option>
                    <option value="cloze">挖空</option>
                    <option value="quote">书摘</option>
                  </select>
                  <div class="row gap8">
                    <span class="gen-conf" v-if="!resultFallback">置信 {{ Math.round(c.confidence * 100) }}%</span>
                    <button class="mini-btn" @click="toggleEdit(i)">{{ editing.has(i) ? '完成' : '编辑' }}</button>
                  </div>
                </div>
                <!-- 预览态：直接看成品 -->
                <template v-if="!editing.has(i)">
                  <div class="pv-row">
                    <span class="pv-tag">问</span>
                    <span class="pv-text">{{ c.front }}</span>
                  </div>
                  <div class="pv-row">
                    <span class="pv-tag pv-tag-b">答</span>
                    <span class="pv-text" :class="{ 'pv-empty': !c.back }">{{ c.back || '背面还空着，点「编辑」补上' }}</span>
                  </div>
                </template>
                <!-- 编辑态 -->
                <template v-else>
                  <label class="field"><span>正面</span><textarea v-model="c.front" rows="2" /></label>
                  <label class="field"><span>背面</span><textarea v-model="c.back" rows="2" /></label>
                </template>
              </div>
            </div>
            <label class="field"><span>存入卡组</span>
              <select v-model="targetDeckId">
                <option :value="null">（默认「收件箱」）</option>
                <option v-for="d in decks" :key="d.id" :value="d.id">{{ d.name }}</option>
              </select>
            </label>
            <p class="err" v-if="err">{{ err }}</p>
            <p class="tap-hint" v-if="tapHint">太快了——按住不放才会丢弃</p>
            <div class="gen-actions">
              <HoldButton done-label="已丢弃" :hold-time="1500" @hold="discardCards" @tap="showTapHint">
                <template #icon><svg class="icon"><use href="#i-close" /></svg></template>
                <template #doneIcon><svg class="icon"><use href="#i-check" /></svg></template>
                按住丢弃
              </HoldButton>
              <button class="btn btn-primary" :disabled="saving" @click="saveCards">{{ saving ? '保存中…' : '全部入库' }}</button>
            </div>
          </template>

          <div class="hint-line">
            <svg class="icon" style="width:14px;height:14px;display:inline-block;vertical-align:-2px"><use href="#i-target" /></svg>
            生成后先放在这里给你改，确认后才进卡组，不会污染复习队列。
          </div>
        </div>

        <div class="card pad rise" style="margin-top:18px">
          <div class="h-sec" style="margin-bottom:11px">这篇已经拆出 {{ sourceCards.length }} 张</div>
          <!-- 已拆卡片：文件夹动画展示，点击打开查看 -->
          <div v-if="sourceCards.length" class="folder-grid">
            <div v-for="c in sourceCards" :key="c.id" class="folder-cell">
              <Folder
                :size="0.92" color="var(--ham)" :items="[c.front]"
                :open="viewing?.id === c.id" @select="viewing = c"
              />
            </div>
          </div>
          <div v-else class="folder-empty">
            <Folder :size="0.72" color="var(--warm)" :items="[]" :disabled="true" />
            <div class="muted folder-empty-t">还没有从这篇拆出卡片，在左边选一段话开始。</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 已拆卡片查看弹窗 -->
    <div v-if="viewing" class="mask" @click.self="viewing = null">
      <div class="card view-card">
        <div class="row between" style="margin-bottom:12px">
          <span class="chip chip-m">{{ cardTypeLabel(viewing.card_type) }}</span>
          <button class="mini-btn" @click="viewing = null">关闭</button>
        </div>
        <div class="vc-row">
          <span class="pv-tag">问</span>
          <span class="pv-text">{{ viewing.front }}</span>
        </div>
        <div class="vc-row">
          <span class="pv-tag pv-tag-b">答</span>
          <span class="pv-text" :class="{ 'pv-empty': !viewing.back }">{{ viewing.back || '（背面空着）' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import VuePdfEmbed from 'vue-pdf-embed'
import { aiApi } from '@/api/ai'
import { cardsApi } from '@/api/cards'
import { decksApi } from '@/api/decks'
import { documentsApi, filesApi } from '@/api/files'
import CallChip from '@/components/common/CallChip.vue'
import HoldButton from '@/components/common/HoldButton.vue'
import Folder from '@/components/common/Folder.vue'
import type { Card, Deck, DocumentContent, FileItem, GeneratedCard } from '@/types/api'

const route = useRoute()
const router = useRouter()

const docs = ref<FileItem[]>([])
const currentDocId = ref<string | null>(null)
const textContent = ref('')
const isPdf = ref(false)
const pdfUrl = ref('')
const viewMode = ref<'pdf' | 'text'>('text')
const docLoading = ref(false)
const loading = ref(true)

const selection = ref('')
const selectionLocator = ref<Record<string, unknown> | null>(null)
const tip = reactive({ x: 0, y: 0 })

const cards = ref<GeneratedCard[]>([])
const resultFallback = ref(false)
const decks = ref<Deck[]>([])
const targetDeckId = ref<string | null>(null)
const sourceCards = ref<Card[]>([])
const err = ref('')
const saving = ref(false)
/** 拆卡请求状态：running 时右侧显示等待 chip，error 时 chip 可点重试 */
const genState = ref<'idle' | 'running' | 'error'>('idle')
/** 生成卡片的编辑态（按索引），默认预览、点「编辑」才展开表单 */
const editing = reactive(new Set<number>())
/** 长按丢弃的轻提示 + 正在查看的已拆卡片 */
const tapHint = ref(false)
const viewing = ref<Card | null>(null)

let tapHintTimer: ReturnType<typeof setTimeout> | null = null

function toggleEdit(i: number) {
  if (editing.has(i)) editing.delete(i)
  else editing.add(i)
}
function discardCards() {
  cards.value = []
  editing.clear()
  err.value = ''
}
function showTapHint() {
  tapHint.value = true
  if (tapHintTimer) clearTimeout(tapHintTimer)
  tapHintTimer = setTimeout(() => (tapHint.value = false), 2200)
}
const CARD_TYPE_LABELS: Record<string, string> = { basic: '问答', cloze: '挖空', quote: '书摘', image: '图片' }
const cardTypeLabel = (t: string) => CARD_TYPE_LABELS[t] ?? t

let sourceFileId = ''
let lastSelection = ''

async function loadDocs() {
  loading.value = true
  try {
    const files = (await filesApi.list()).data
    docs.value = files.filter((f) => !f.is_dir && f.doc_id)
    if (!currentDocId.value) {
      const q = route.query.doc as string | undefined
      const initial = q && docs.value.some((d) => d.doc_id === q) ? q : docs.value[0]?.doc_id
      currentDocId.value = initial ?? null
    }
  } catch {
    err.value = '加载文档列表失败'
  } finally {
    loading.value = false
  }
  if (currentDocId.value) await loadDoc()
}

async function loadDoc() {
  if (!currentDocId.value) return
  docLoading.value = true
  err.value = ''
  selection.value = ''
  selectionLocator.value = null
  cards.value = []
  genState.value = 'idle'
  editing.clear()
  viewing.value = null
  try {
    const res = await documentsApi.content(currentDocId.value)
    const doc: DocumentContent = res.data
    sourceFileId = doc.file_id
    textContent.value = doc.text

    const f = docs.value.find((d) => d.doc_id === currentDocId.value)
    isPdf.value = f?.ext === 'pdf'
    if (isPdf.value) {
      const blob = await filesApi.download(doc.file_id)
      pdfUrl.value = URL.createObjectURL(blob.data)
      viewMode.value = 'pdf'
    } else {
      viewMode.value = 'text'
    }
    await loadSourceCards()
  } catch {
    err.value = '加载文档失败'
  } finally {
    docLoading.value = false
  }
}

async function loadSourceCards() {
  if (!sourceFileId) {
    sourceCards.value = []
    return
  }
  try {
    const res = await cardsApi.list({ source_file_id: sourceFileId, limit: 100 })
    sourceCards.value = res.data.items
  } catch {
    sourceCards.value = []
  }
}

watch(currentDocId, loadDoc)

async function loadDecks() {
  try {
    const d = await decksApi.list()
    decks.value = d.data
    if (!targetDeckId.value && d.data.length) targetDeckId.value = d.data[0].id
  } catch {
    /* 卡组加载失败不阻塞阅读 */
  }
}

function onSelect(e: MouseEvent) {
  const sel = window.getSelection()
  const text = sel?.toString().trim()
  if (!text) {
    selection.value = ''
    selectionLocator.value = null
    return
  }
  selection.value = text.slice(0, 500)
  selectionLocator.value = computeLocator(sel)
  tip.x = e.clientX
  tip.y = e.clientY - 40
}

/** 记录选中文字在正文里的位置（pre 是单个文本节点，startOffset 即全文偏移），供卡片溯源回原文。 */
function computeLocator(sel: Selection | null): Record<string, unknown> | null {
  if (!sel || sel.rangeCount === 0) return null
  const range = sel.getRangeAt(0)
  if (range.startContainer.nodeType !== Node.TEXT_NODE) return null
  return {
    start: range.startOffset,
    end: range.endOffset,
    quote: sel.toString().slice(0, 200),
  }
}

async function generate() {
  if (genState.value === 'running') return
  const text = selection.value || lastSelection
  if (!text || !currentDocId.value) return
  lastSelection = text // 留给失败重试用（工具条此刻已被清掉）
  selection.value = ''
  window.getSelection()?.removeAllRanges()
  genState.value = 'running'
  err.value = ''
  const reqDoc = currentDocId.value // 切换文档后旧结果作废
  try {
    const res = await aiApi.cardsFromSelection({
      document_id: reqDoc,
      selection: text,
      locator: selectionLocator.value,
      target_deck_id: targetDeckId.value,
      mode: 'auto',
      max_cards: 3,
    })
    if (currentDocId.value !== reqDoc) return
    cards.value = res.data.cards
    resultFallback.value = res.data.fallback
    genState.value = 'idle'
  } catch {
    if (currentDocId.value !== reqDoc) return
    genState.value = 'error'
  }
}

async function saveCards() {
  saving.value = true
  err.value = ''
  try {
    for (const c of cards.value) {
      await cardsApi.create({
        deck_id: targetDeckId.value,
        card_type: c.card_type,
        front: c.front,
        back: c.back,
        hint: c.hint,
        source_file_id: sourceFileId || null,
        source_locator: selectionLocator.value,
      })
    }
    cards.value = []
    editing.clear()
    await loadSourceCards()
  } catch {
    err.value = '入库失败'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadDecks()
  await loadDocs()
})
</script>

<style scoped>
.reader-grid { display: grid; grid-template-columns: 1.5fr 1fr; gap: 18px; align-items: start; }
@media (max-width: 1000px) { .reader-grid { grid-template-columns: 1fr; } }

/* ── 左：文档 ── */
.doc-meta { display: flex; align-items: center; gap: 11px; padding-bottom: 14px; border-bottom: 2px solid var(--hairline); margin-bottom: 14px; }
.doc-ic { width: 36px; height: 36px; border-radius: 12px; background: var(--ham-l); border: 2px solid var(--line); display: flex; align-items: center; justify-content: center; flex: none; color: var(--ham-d); }
.doc-info { flex: 1; min-width: 0; }
.doc-select { width: 100%; font-family: inherit; font-size: 14px; font-weight: 800; color: var(--ink); background: none; border: none; padding: 0; outline: none; cursor: pointer; }
.doc-sub { font-size: 12px; margin-top: 2px; }

.rd-tabs { display: inline-flex; gap: 3px; padding: 3px; background: var(--warm); border: 2px solid var(--line); border-radius: 999px; flex: none; }
.rd-tabs button { padding: 5px 14px; border-radius: 999px; font-size: 12.5px; font-weight: 750; color: var(--ink2); background: none; border: none; cursor: pointer; transition: all 0.2s var(--ease); }
.rd-tabs button.on { background: var(--paper); color: var(--ink); box-shadow: var(--pop-sm); border: 2px solid var(--line); }

.doc-body { position: relative; max-height: 68vh; overflow: auto; }
.doc-text { font-family: inherit; font-size: 14.5px; line-height: 1.95; white-space: pre-wrap; margin: 0; color: var(--ink); }
.rd-pdf { max-width: 100%; }

.tooltip { position: fixed; z-index: 50; transform: translateX(-50%); }
.tip-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px; font-family: inherit; font-size: 13.5px; font-weight: 800;
  color: var(--onfill); background: var(--orange);
  border: 2.5px solid var(--line); border-radius: 12px; box-shadow: var(--pop); cursor: pointer;
}

/* ── 右：生成预览 ── */
.side-ic { width: 34px; height: 34px; border-radius: 12px; background: var(--orange-l); color: var(--orange-d); border: 2px solid var(--line); display: flex; align-items: center; justify-content: center; flex: none; }
.h-sec { font-size: 15px; font-weight: 800; }

.gen-box { text-align: center; padding: 26px 12px; border: 2px dashed var(--hairline); border-radius: 16px; }
.gen-wait { display: flex; justify-content: center; padding: 18px 0; }
.gen-wait > * { max-width: 100%; }
.gen-ic { width: 44px; height: 44px; margin: 0 auto 10px; border-radius: 14px; background: var(--warm); border: 2px solid var(--line); display: flex; align-items: center; justify-content: center; color: var(--ink3); }
.gen-empty-t { font-size: 14px; font-weight: 800; }
.gen-empty-s { font-size: 12.5px; margin-top: 5px; line-height: 1.6; }

.gen-list { display: flex; flex-direction: column; gap: 14px; }
.gen-item { border: 2px solid var(--hairline); border-radius: 14px; padding: 12px; }
.gen-item-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.gen-item-head select, .field select {
  font-family: inherit; font-size: 13px; color: var(--ink); background: var(--cream);
  border: 2px solid var(--line); border-radius: 9px; padding: 4px 8px; outline: none;
}
.gen-conf { font-size: 11.5px; color: var(--mint-d); font-weight: 700; }
.field { display: block; margin-bottom: 10px; }
.field span { display: block; font-size: 12px; font-weight: 750; color: var(--ink2); margin-bottom: 5px; }
.field textarea, .field select {
  width: 100%; font-family: inherit; font-size: 14px; color: var(--ink);
  background: var(--cream); border: 2.5px solid var(--line); border-radius: 11px; padding: 8px 11px; outline: none; resize: vertical;
}
.field textarea:focus { border-color: var(--orange); }
.err { color: var(--berry); font-size: 13px; font-weight: 650; margin-bottom: 10px; }
.gen-actions { display: flex; justify-content: flex-end; align-items: center; gap: 10px; margin-top: 4px; }
.tap-hint { font-size: 12.5px; color: var(--berry); font-weight: 650; margin-bottom: 8px; text-align: right; }

/* 卡片预览态（编辑按钮切换） */
.mini-btn {
  padding: 4px 11px;
  font-family: inherit;
  font-size: 12px;
  font-weight: 750;
  color: var(--ink2);
  background: var(--cream);
  border: 2px solid var(--line);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s var(--ease-out-quart);
}
.mini-btn:hover { background: var(--paper); color: var(--ink); box-shadow: var(--pop-sm); transform: translateY(-1px); }
.pv-row { display: flex; align-items: flex-start; gap: 8px; padding: 7px 9px; border-radius: 10px; background: var(--warm); border: 2px solid var(--hairline); margin-bottom: 7px; }
.pv-row:last-child { margin-bottom: 0; }
.pv-tag {
  flex: none;
  width: 20px;
  height: 20px;
  display: grid;
  place-items: center;
  border-radius: 7px;
  background: var(--paper);
  border: 2px solid var(--line);
  font-size: 11px;
  font-weight: 800;
  color: var(--orange-d);
}
.pv-tag-b { color: var(--mint-d); }
.pv-text { flex: 1; font-size: 13px; line-height: 1.6; color: var(--ink); font-weight: 600; word-break: break-word; }
.pv-empty { color: var(--ink3); font-weight: 500; }

/* 已拆卡片文件夹网格 */
/* 已拆卡片文件夹网格：padding-top 给纸张飞出动画留空间，避免被 overflow 裁掉 */
.folder-grid { display: flex; flex-wrap: wrap; gap: 14px 10px; max-height: 320px; overflow: auto; padding: 58px 6px 8px; }
.folder-cell { flex: none; }
.folder-empty { text-align: center; padding: 10px 0 4px; }
.folder-empty-t { font-size: 13px; margin-top: 4px; }

/* 已拆卡片查看弹窗 */
.mask { position: fixed; inset: 0; background: rgba(10, 7, 4, 0.5); z-index: 90; display: flex; align-items: center; justify-content: center; padding: 20px; }
.view-card { width: min(460px, 100%); padding: 22px 22px 18px; box-shadow: var(--pop-lg); background: var(--paper); border-radius: var(--r-lg); border: 2.5px solid var(--line); }
.vc-row { display: flex; align-items: flex-start; gap: 9px; padding: 11px 13px; border-radius: 13px; background: var(--warm); border: 2px solid var(--line); margin-bottom: 9px; }
.vc-row:last-child { margin-bottom: 0; }
.vc-row .pv-tag { width: 22px; height: 22px; }
.hint-line { margin-top: 13px; font-size: 12.5px; color: var(--ink3); line-height: 1.7; font-weight: 600; }
</style>
