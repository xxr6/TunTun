<template>
  <div>
    <!-- 空态：没有可阅读的文档 -->
    <div v-if="!docs.length && !loading" class="card pad rise" style="text-align:center;padding:48px 20px">
      <img :src="logoUrl" style="width:88px;height:88px" alt="" aria-hidden="true" />
      <div style="font-size:15px;font-weight:800;margin:10px 0 6px">还没有可阅读的文档</div>
      <div class="muted" style="font-size:13px;margin-bottom:16px">{{ sourceNotice || '先去内容库上传一份 PDF / Markdown / TXT，解析完就能在这里划词拆卡' }}</div>
      <button class="btn btn-primary" @click="leaveReader">
        <svg class="icon"><use href="#i-folder" /></svg>{{ fromReview ? '返回复习' : '去内容库' }}
      </button>
    </div>

    <template v-else>
      <!-- 顶栏：返回 | 文件信息 | 翻页 | 目录 | 生成卡片 -->
      <div class="rd-top rise">
        <button class="rd-round" :aria-label="fromReview ? '返回复习' : '返回内容库'" @click="leaveReader">
          <svg class="icon"><use href="#i-back" /></svg>
        </button>
        <div class="rd-file" v-if="currentDoc">
          <div class="rd-file-ic"><svg class="icon"><use href="#i-doc" /></svg></div>
          <div class="rd-file-info">
            <select v-model="currentDocId" class="rd-file-name" aria-label="切换文档">
              <option v-for="d in docs" :key="d.doc_id!" :value="d.doc_id!">{{ d.name }}</option>
            </select>
            <div class="rd-file-sub">已解析 · 可溯源 · 共 {{ pageTotalLabel }}</div>
          </div>
        </div>
        <div v-else class="rd-file rd-file-loading"><span class="muted">加载中…</span></div>

        <div class="rd-pager" aria-label="翻页">
          <button aria-label="上一页" @click="pagePrev"><svg class="icon" style="transform:rotate(180deg)"><use href="#i-chev" /></svg></button>
          <span class="rd-page-num">{{ pageCur }} / {{ pageTotal }}</span>
          <button aria-label="下一页" @click="pageNext"><svg class="icon"><use href="#i-chev" /></svg></button>
        </div>

        <div class="rd-top-actions">
          <button class="btn" @click="tocOpen = !tocOpen">
            <svg class="icon"><use href="#i-list" /></svg><span class="rd-btn-txt">目录</span>
          </button>
          <button class="btn btn-primary" @click="onGenBtn">
            <svg class="icon"><use href="#i-spark" /></svg><span class="rd-btn-txt">生成卡片</span>
          </button>
        </div>

        <!-- 目录弹层 -->
        <Transition name="pop">
          <div v-if="tocOpen" class="toc-pop card">
            <div class="toc-head">目录 <button class="mini-btn" @click="tocOpen = false">关闭</button></div>
            <template v-if="isPdf && viewMode === 'pdf'">
              <div class="toc-pages">
                <button v-for="p in pdfTotal" :key="p" class="toc-page" :class="{ on: p === pdfPage }" @click="goPdfPage(p)">{{ p }}</button>
              </div>
            </template>
            <template v-else>
              <div v-if="tocItems.length" class="toc-list">
                <button v-for="(t, i) in tocItems" :key="i" class="toc-item" @click="goToc(t)">{{ t.title }}</button>
              </div>
              <div v-else class="muted toc-empty">这篇没有识别出章节标题，滚动阅读就好。</div>
            </template>
          </div>
        </Transition>
      </div>

      <div v-if="fromReview" class="source-banner">
        <span>{{ sourceNotice || '正在打开卡片来源…' }}</span>
        <button class="btn" @click="leaveReader">返回复习</button>
      </div>

      <!-- 「生成卡片」无选词提示 -->
      <Transition name="pop">
        <div v-if="genHint" class="gen-hint rise">
          <svg class="icon" style="width:15px;height:15px"><use href="#i-spark" /></svg>
          在左侧文章里选中一段话，就能把它拆成卡片
        </div>
      </Transition>

      <div class="rd-grid" :class="{ single: focusMode }">
        <!-- 左：文档区 -->
        <div class="card rd-doc rise">
          <div class="rd-docbar">
            <div class="rd-docbar-name" :title="currentDoc?.name">{{ currentDoc?.name || '文档' }}</div>
            <div class="rd-docbar-tools">
              <div v-if="isPdf" class="rd-tabs">
                <button :class="{ on: viewMode === 'pdf' }" @click="viewMode = 'pdf'">分页</button>
                <button :class="{ on: viewMode === 'text' }" @click="viewMode = 'text'">文本</button>
              </div>
              <template v-if="viewMode === 'text'">
                <button class="tool-btn" aria-label="缩小字号" @click="zoomBy(-10)"><svg class="icon"><use href="#i-zoom-out" /></svg></button>
                <span class="zoom-val">{{ zoomPercent }}%</span>
                <button class="tool-btn" aria-label="放大字号" @click="zoomBy(10)"><svg class="icon"><use href="#i-zoom-in" /></svg></button>
              </template>
              <button class="tool-btn" aria-label="全屏阅读" @click="toggleFull">
                <svg class="icon"><use href="#i-expand" /></svg>
              </button>
            </div>
          </div>

          <div ref="bodyEl" class="doc-body" :class="{ full: isFull }" @mouseup="onSelect" @scroll="onBodyScroll">
            <p v-if="docLoading" class="muted" style="text-align:center;padding:40px">加载文档中…</p>
            <pre v-else-if="viewMode === 'text'" class="doc-text" :style="textStyle"><template v-if="sourceHighlight">{{ textContent.slice(0, sourceHighlight.start) }}<mark ref="sourceMark" class="source-mark">{{ textContent.slice(sourceHighlight.start, sourceHighlight.end) }}</mark>{{ textContent.slice(sourceHighlight.end) }}</template><template v-else>{{ textContent }}</template></pre>
            <div v-else class="rd-pdf-wrap">
              <VuePdfEmbed v-if="pdfUrl" :source="pdfUrl" :page="pdfPage" :style="pdfStyle" class="rd-pdf" @loaded="onPdfLoaded" />
              <div v-else class="muted" style="text-align:center;padding:40px">PDF 加载中…</div>
            </div>
          </div>

          <!-- 底部操作栏 -->
          <div class="rd-docfoot">
            <button class="btn btn-primary" @click="startRead">
              <svg class="icon"><use href="#i-play" /></svg>开始
            </button>
            <button class="btn" aria-label="回到开头" @click="resetRead">
              <svg class="icon"><use href="#i-refresh" /></svg><span class="rd-btn-txt">重置</span>
            </button>
            <div class="rd-track" aria-hidden="true"><i :style="{ width: progressPct }"></i></div>
            <button class="tool-btn rd-setting" @click="setOpen = !setOpen" aria-label="阅读设置">
              <svg class="icon"><use href="#i-gear" /></svg><span class="rd-btn-txt">阅读设置</span>
            </button>

            <!-- 阅读设置弹层 -->
            <Transition name="pop">
              <div v-if="setOpen" class="set-pop card" @click.stop>
                <div class="set-row">
                  <span class="set-label">字号</span>
                  <button class="mini-btn" @click="zoomBy(-10)">A−</button>
                  <span class="zoom-val">{{ zoomPercent }}%</span>
                  <button class="mini-btn" @click="zoomBy(10)">A+</button>
                </div>
                <div class="set-row">
                  <span class="set-label">行距</span>
                  <button v-for="(v, i) in LH_STEPS" :key="v" class="mini-btn" :class="{ on: lineHeight === v }" @click="lineHeight = v">{{ ['紧凑', '适中', '宽松'][i] }}</button>
                </div>
                <div class="set-row">
                  <span class="set-label">专心</span>
                  <button class="mini-btn" :class="{ on: focusMode }" @click="focusMode = !focusMode">{{ focusMode ? '已开启' : '隐藏侧栏' }}</button>
                </div>
              </div>
            </Transition>
          </div>

          <!-- 划词工具条 -->
          <div v-if="selection" class="tooltip" :style="{ left: tip.x + 'px', top: tip.y + 'px' }" @mousedown.prevent>
            <button class="tip-btn" @click="generate">
              <svg class="icon" style="width:14px;height:14px"><use href="#i-spark" /></svg>生成卡片
            </button>
          </div>
        </div>

        <!-- 右栏 -->
        <div v-if="!focusMode" class="rd-side">
          <!-- 新生成的卡片 -->
          <div class="card rd-panel rise">
            <div class="rp-head">
              <div class="rp-title"><svg class="icon"><use href="#i-spark" /></svg>新生成的卡片</div>
              <span class="rp-count" v-if="cards.length">{{ cards.length }} 张</span>
              <img :src="logoUrl" class="rp-logo" alt="" aria-hidden="true" />
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
              <div class="muted gen-empty-s">在左边文章里选一段话试试<br />系统会判断这段适合做成问答还是挖空</div>
            </div>

            <template v-else>
              <p v-if="resultFallback" class="tap-hint" role="status">AI 暂不可用：已保留原文作为草稿。请展开卡片，改成明确问题并填写答案后再入库。</p>
              <div class="card-list">
                <div v-for="(c, i) in cards" :key="i" class="kitem" :class="{ open: editing.has(i) }">
                  <button class="kitem-head" @click="toggleEdit(i)" :aria-expanded="editing.has(i)">
                    <span class="kitem-ic" :style="typeMeta(c.card_type)"><svg class="icon"><use :href="typeIcon(c.card_type)" /></svg></span>
                    <span class="kitem-main">
                      <span class="kitem-title">{{ c.front }}</span>
                      <span class="kitem-src">来自：{{ currentDoc?.name }}</span>
                    </span>
                    <span class="kitem-tag" :style="typeMeta(c.card_type)">{{ typeLabel(c.card_type) }}</span>
                    <svg class="icon kitem-chev"><use href="#i-chev" /></svg>
                  </button>
                  <div v-if="editing.has(i)" class="kitem-body">
                    <div class="kitem-edit-row">
                      <select v-model="c.card_type" aria-label="卡片类型">
                        <option value="basic">问答</option>
                        <option value="cloze">挖空</option>
                        <option value="quote">书摘</option>
                      </select>
                      <span class="gen-conf" v-if="!resultFallback">置信 {{ Math.round(c.confidence * 100) }}%</span>
                    </div>
                    <label class="field"><span>正面</span><textarea v-model="c.front" rows="2" /></label>
                    <label class="field"><span>背面</span><textarea v-model="c.back" rows="2" /></label>
                  </div>
                </div>
              </div>
              <label class="field" style="margin-top:12px"><span>存入卡组</span>
                <select v-model="targetDeckId">
                  <option :value="null">（默认「收件箱」）</option>
                  <option v-for="d in decks" :key="d.id" :value="d.id">{{ d.name }}</option>
                </select>
              </label>
              <button class="btn" @click="showCreateDeck = true">＋ 新建卡组并选用</button>
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

          <!-- 已提取的卡片 -->
          <div class="card rd-panel rise">
            <div class="rp-head">
              <div class="rp-title"><svg class="icon"><use href="#i-cards" /></svg>已提取的卡片</div>
              <span class="rp-count" v-if="sourceCards.length">{{ sourceCards.length }} 张</span>
              <img :src="logoUrl" class="rp-logo" alt="" aria-hidden="true" />
            </div>
            <div v-if="sourceCards.length" class="card-list">
              <button v-for="c in sourceCards" :key="c.id" class="kitem-head plain" @click="viewing = c">
                <span class="kitem-ic" :style="typeMeta(c.card_type)"><svg class="icon"><use :href="typeIcon(c.card_type)" /></svg></span>
                <span class="kitem-main">
                  <span class="kitem-title">{{ c.front }}</span>
                  <span class="kitem-src">来自：{{ sourceName(c) }}</span>
                </span>
                <span class="kitem-tag" :style="typeMeta(c.card_type)">{{ typeLabel(c.card_type) }}</span>
                <svg class="icon kitem-chev"><use href="#i-chev" /></svg>
              </button>
            </div>
            <div v-else class="gen-box" style="padding:20px 12px">
              <div class="muted gen-empty-s">还没有从这篇拆出卡片，在左边选一段话开始。</div>
            </div>
          </div>

          <!-- 右栏底条 -->
          <div class="rd-sidefoot rise">
            <img :src="logoUrl" alt="" aria-hidden="true" />
            <span class="rd-sidefoot-txt">好好读书，囤住未来！</span>
            <button class="rd-sidefoot-btn" @click="router.push('/library')">返回</button>
          </div>
        </div>
      </div>
    </template>

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
    <CreateDeckDialog v-if="showCreateDeck" @close="showCreateDeck = false" @created="onDeckCreated" />
  </div>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { aiApi } from '@/api/ai'
import { cardsApi } from '@/api/cards'
import { cardQualityError } from '@/lib/cardQuality'
import { decksApi } from '@/api/decks'
import { documentsApi, filesApi } from '@/api/files'
import CallChip from '@/components/common/CallChip.vue'
import HoldButton from '@/components/common/HoldButton.vue'
import CreateDeckDialog from '@/components/common/CreateDeckDialog.vue'
import type { Card, Deck, DocumentContent, FileItem, GeneratedCard } from '@/types/api'
import logoUrl from '@/assets/logo.png'

// 仅在阅读 PDF 时下载渲染器；普通文档进入阅读器无需加载 pdf.js。
const VuePdfEmbed = defineAsyncComponent(() => import('vue-pdf-embed'))

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
const fromReview = computed(() => route.query.from === 'review')
const sourceCard = ref<Card | null>(null)
const sourceNotice = ref('')
const sourceHighlight = ref<{ start: number; end: number } | null>(null)
const sourceMark = ref<HTMLElement | null>(null)
let initialDocumentLoading = true

const selection = ref('')
const selectionLocator = ref<Record<string, unknown> | null>(null)
const tip = reactive({ x: 0, y: 0 })

const cards = ref<GeneratedCard[]>([])
const resultFallback = ref(false)
const decks = ref<Deck[]>([])
const targetDeckId = ref<string | null>(null)
const showCreateDeck = ref(false)
const sourceCards = ref<Card[]>([])
const err = ref('')
const saving = ref(false)
/** 拆卡请求状态：running 时右侧显示等待 chip，error 时 chip 可点重试 */
const genState = ref<'idle' | 'running' | 'error'>('idle')
/** 生成卡片的编辑态（按索引），默认收起、点条目展开 */
const editing = reactive(new Set<number>())
/** 长按丢弃的轻提示 + 正在查看的已拆卡片 */
const tapHint = ref(false)
const viewing = ref<Card | null>(null)

/* ── 阅读器 UI 状态 ── */
const bodyEl = ref<HTMLElement | null>(null)
const pageCur = ref(1)
const pageTotal = ref(1)
const pdfPage = ref(1)
const pdfTotal = ref(0)
const zoom = ref(100)
const lineHeight = ref('1.95')
const focusMode = ref(false)
const tocOpen = ref(false)
const setOpen = ref(false)
const genHint = ref(false)
const isFull = ref(false)
const LH_STEPS = ['1.75', '1.95', '2.2'] as const

let genHintTimer: ReturnType<typeof setTimeout> | null = null
let tapHintTimer: ReturnType<typeof setTimeout> | null = null

const zoomPercent = computed(() => zoom.value)
const textStyle = computed(() => ({ fontSize: (14.5 * zoom.value) / 100 + 'px', lineHeight: lineHeight.value }))
/** PDF 按容器宽度自适应渲染，缩放用倍率 */
const pdfStyle = computed(() => ({ width: '100%', transform: `scale(${zoom.value / 100})`, transformOrigin: 'top left' }))
const progressPct = computed(() => {
  if (pageTotal.value <= 1) return '0%'
  return Math.min(100, Math.round((pageCur.value / pageTotal.value) * 100)) + '%'
})
const pageTotalLabel = computed(() => {
  if (isPdf.value && viewMode.value === 'pdf' && pdfTotal.value) return pdfTotal.value + ' 页'
  return pageTotal.value > 1 ? pageTotal.value + ' 屏' : '单屏'
})

/* ── 卡片类型外观：图标 / 配色 / 标签 ── */
const TYPE_META: Record<string, { icon: string; bg: string; fg: string; label: string }> = {
  basic: { icon: '#i-leaf', bg: 'var(--mint-l)', fg: 'var(--mint-d)', label: '知识点' },
  cloze: { icon: '#i-target', bg: 'var(--orange-l)', fg: 'var(--orange-d)', label: '考点' },
  quote: { icon: '#i-book', bg: 'var(--grape-l)', fg: 'var(--grape-d)', label: '书摘' },
  image: { icon: '#i-doc', bg: 'var(--sky-l)', fg: 'var(--sky)', label: '图片' },
}
function typeMeta(t: string) {
  const m = TYPE_META[t] ?? TYPE_META.basic
  return { background: m.bg, color: m.fg }
}
function typeIcon(t: string) {
  return (TYPE_META[t] ?? TYPE_META.basic).icon
}
function typeLabel(t: string) {
  return (TYPE_META[t] ?? TYPE_META.basic).label
}
const CARD_TYPE_LABELS: Record<string, string> = { basic: '问答', cloze: '挖空', quote: '书摘', image: '图片' }
const cardTypeLabel = (t: string) => CARD_TYPE_LABELS[t] ?? t

function sourceName(c: Card) {
  return docs.value.find((d) => d.id === c.source_file_id)?.name ?? currentDoc.value?.name ?? '本文档'
}

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

let sourceFileId = ''
let lastSelection = ''

const currentDoc = computed(() => docs.value.find((d) => d.doc_id === currentDocId.value) ?? null)

async function loadDocs() {
  loading.value = true
  try {
    const cardId = typeof route.query.card === 'string' ? route.query.card : null
    if (cardId) {
      try {
        sourceCard.value = (await cardsApi.get(cardId)).data
      } catch {
        sourceNotice.value = '这张卡片已无法读取，已打开阅读器。'
      }
    }
    const files = (await filesApi.list({ all: true })).data
    docs.value = files.filter((f) => !f.is_dir && f.doc_id)
    if (!currentDocId.value) {
      const q = route.query.doc as string | undefined
      const fromCard = docs.value.find((d) => d.id === sourceCard.value?.source_file_id)?.doc_id
      const initial = fromCard || (q && docs.value.some((d) => d.doc_id === q) ? q : docs.value[0]?.doc_id)
      currentDocId.value = initial ?? null
      if (sourceCard.value?.source_file_id && !fromCard) sourceNotice.value = '来源文档已删除或尚未解析，暂时无法定位。'
    }
  } catch {
    err.value = '加载文档列表失败'
  } finally {
    loading.value = false
  }
  if (currentDocId.value) await loadDoc()
  initialDocumentLoading = false
}

async function loadDoc() {
  if (!currentDocId.value) return
  docLoading.value = true
  sourceFileId = ''
  err.value = ''
  selection.value = ''
  selectionLocator.value = null
  sourceHighlight.value = null
  cards.value = []
  genState.value = 'idle'
  editing.clear()
  viewing.value = null
  tocOpen.value = false
  zoom.value = 100
  try {
    const res = await documentsApi.content(currentDocId.value)
    const doc: DocumentContent = res.data
    sourceFileId = doc.file_id
    textContent.value = doc.text

    const f = docs.value.find((d) => d.doc_id === currentDocId.value)
    isPdf.value = f?.ext === 'pdf'
    pdfTotal.value = 0
    pdfPage.value = 1
    if (pdfUrl.value) URL.revokeObjectURL(pdfUrl.value)
    if (isPdf.value) {
      const blob = await filesApi.download(doc.file_id)
      pdfUrl.value = URL.createObjectURL(blob.data)
      viewMode.value = 'pdf'
    } else {
      pdfUrl.value = ''
      viewMode.value = 'text'
    }
    await loadSourceCards()
  } catch {
    err.value = '加载文档失败'
  } finally {
    docLoading.value = false
  }
  await nextTick()
  recalcPages()
  if (!err.value && sourceCard.value?.source_file_id === sourceFileId) await revealSource(sourceCard.value)
  else if (fromReview.value && sourceCard.value?.source_file_id && sourceFileId) sourceNotice.value = '已切换到其他文档。'
}

function leaveReader() {
  if (fromReview.value) {
    router.push({ path: '/review', query: { resume: '1', ...(typeof route.query.deck === 'string' ? { deck: route.query.deck } : {}) } })
  } else router.push('/library')
}

async function revealSource(card: Card) {
  const locator = card.source_locator || {}
  const quote = typeof locator.quote === 'string' ? locator.quote.trim() : ''
  const start = typeof locator.start === 'number' ? locator.start : -1
  const page = typeof locator.page === 'number' ? locator.page : 0
  let found = -1
  if (quote && start >= 0 && textContent.value.slice(start, start + quote.length) === quote) found = start
  else if (quote) found = textContent.value.indexOf(quote)

  if (found >= 0 && quote) {
    viewMode.value = 'text'
    sourceHighlight.value = { start: found, end: found + quote.length }
    sourceNotice.value = '已定位并高亮这张卡片的原文。'
    await nextTick()
    sourceMark.value?.scrollIntoView({ block: 'center', behavior: 'smooth' })
    recalcPages()
  } else if (isPdf.value && page > 0) {
    viewMode.value = 'pdf'
    pdfPage.value = page
    sourceNotice.value = `已跳到来源 PDF 第 ${page} 页。`
  } else {
    sourceNotice.value = quote ? '未找到完全匹配的原句，已打开来源文档。' : '已打开来源文档；这张卡片没有精确位置记录。'
  }
}

/* ── 翻页 / 进度（文本 = 滚动屏，PDF = 真实页码） ── */
function recalcPages() {
  const el = bodyEl.value
  if (!el) return
  if (isPdf.value && viewMode.value === 'pdf') {
    pageTotal.value = Math.max(1, pdfTotal.value)
    pageCur.value = pdfPage.value
    return
  }
  const total = Math.max(1, Math.ceil(el.scrollHeight / Math.max(1, el.clientHeight)))
  pageTotal.value = total
  pageCur.value = Math.min(total, Math.floor(el.scrollTop / Math.max(1, el.clientHeight)) + 1)
}
function onBodyScroll() {
  if (isPdf.value && viewMode.value === 'pdf') return
  recalcPages()
}
function pagePrev() {
  const el = bodyEl.value
  if (isPdf.value && viewMode.value === 'pdf') {
    if (pdfPage.value > 1) pdfPage.value--
    return
  }
  el?.scrollBy({ top: -el.clientHeight, behavior: 'smooth' })
}
function pageNext() {
  const el = bodyEl.value
  if (isPdf.value && viewMode.value === 'pdf') {
    if (!pdfTotal.value || pdfPage.value < pdfTotal.value) pdfPage.value++
    return
  }
  el?.scrollBy({ top: el.clientHeight, behavior: 'smooth' })
}
function onPdfLoaded(pdf: unknown) {
  const n = (pdf as { numPages?: number })?.numPages
  if (n) pdfTotal.value = n
  recalcPages()
}
watch(pdfPage, () => {
  if (isPdf.value && viewMode.value === 'pdf') {
    pageCur.value = pdfPage.value
    pageTotal.value = Math.max(1, pdfTotal.value)
  }
})
// 切文本/分页视图后重算页数
watch(viewMode, () => nextTick(recalcPages))
// 字号变化影响分屏数
watch(zoom, () => nextTick(recalcPages))
watch(lineHeight, () => nextTick(recalcPages))

function zoomBy(delta: number) {
  zoom.value = Math.min(200, Math.max(70, zoom.value + delta))
}

/* ── 开始 / 重置 ── */
function startRead() {
  resetRead()
  genHint.value = true
  if (genHintTimer) clearTimeout(genHintTimer)
  genHintTimer = setTimeout(() => (genHint.value = false), 2600)
}
function resetRead() {
  if (isPdf.value && viewMode.value === 'pdf') pdfPage.value = 1
  else bodyEl.value?.scrollTo({ top: 0, behavior: 'smooth' })
}

/* ── 全屏 ── */
function toggleFull() {
  const el = bodyEl.value
  if (!el) return
  if (document.fullscreenElement) {
    document.exitFullscreen()
    isFull.value = false
  } else {
    el.requestFullscreen?.()
    isFull.value = true
  }
}
function onFsChange() {
  isFull.value = !!document.fullscreenElement
}

/* ── 目录 ── */
interface TocItem { title: string; ratio: number }
const tocItems = computed<TocItem[]>(() => {
  if (isPdf.value && viewMode.value === 'pdf') return []
  const text = textContent.value
  if (!text) return []
  const lines = text.split('\n')
  const items: TocItem[] = []
  let offset = 0
  const re = /^(#{1,4}\s+|(第[一二三四五六七八九十百0-9]+\s*[章节部分讲篇])|([一二三四五六七八九十]+\s*[、.])|(\d+(\.\d+)*[、.]\s*\S))/
  for (const line of lines) {
    const t = line.trim()
    if (t && t.length <= 40 && re.test(t)) items.push({ title: t.replace(/^#+\s*/, ''), ratio: offset / Math.max(1, text.length) })
    offset += line.length + 1
  }
  return items.slice(0, 60)
})
function goToc(t: TocItem) {
  const el = bodyEl.value
  if (!el) return
  el.scrollTo({ top: t.ratio * el.scrollHeight, behavior: 'smooth' })
  tocOpen.value = false
}
function goPdfPage(p: number) {
  pdfPage.value = p
  tocOpen.value = false
}

/* ── 数据加载 ── */
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

watch(currentDocId, () => {
  if (!initialDocumentLoading) loadDoc()
})

async function loadDecks() {
  try {
    const d = await decksApi.list()
    decks.value = d.data
    const requested = typeof route.query.deck === 'string' ? route.query.deck : null
    if (requested && d.data.some((deck) => deck.id === requested)) targetDeckId.value = requested
    else if (!targetDeckId.value && d.data.length) targetDeckId.value = d.data[0].id
  } catch {
    /* 卡组加载失败不阻塞阅读 */
  }
}

function onDeckCreated(deck: Deck) {
  decks.value.push(deck)
  targetDeckId.value = deck.id
  showCreateDeck.value = false
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

/** 记录选中文字在正文或 PDF 页里的位置，供复习时回到原文。 */
function computeLocator(sel: Selection | null): Record<string, unknown> | null {
  if (!sel || sel.rangeCount === 0) return null
  const range = sel.getRangeAt(0)
  const quote = sel.toString().slice(0, 200)
  if (isPdf.value && viewMode.value === 'pdf') return { page: pdfPage.value, quote }
  const pre = (range.startContainer.nodeType === Node.ELEMENT_NODE
    ? range.startContainer as Element
    : range.startContainer.parentElement)?.closest('.doc-text')
  if (!pre) return { quote }
  const before = range.cloneRange()
  before.selectNodeContents(pre)
  before.setEnd(range.startContainer, range.startOffset)
  const start = before.toString().length
  return { start, end: start + sel.toString().length, quote }
}

/* ── 顶栏「生成卡片」：有选词直接生成，没有就提示 ── */
function onGenBtn() {
  if (selection.value) {
    generate()
    return
  }
  genHint.value = true
  if (genHintTimer) clearTimeout(genHintTimer)
  genHintTimer = setTimeout(() => (genHint.value = false), 2600)
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
  const invalid = cards.value.findIndex((c) => cardQualityError(c.card_type, c.front, c.back))
  if (invalid >= 0) {
    err.value = `第 ${invalid + 1} 张卡：${cardQualityError(cards.value[invalid].card_type, cards.value[invalid].front, cards.value[invalid].back)}`
    editing.add(invalid)
    return
  }
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

onMounted(() => {
  document.addEventListener('fullscreenchange', onFsChange)
  void Promise.all([loadDecks(), loadDocs()])
})
onUnmounted(() => {
  document.removeEventListener('fullscreenchange', onFsChange)
  if (pdfUrl.value) URL.revokeObjectURL(pdfUrl.value)
  if (genHintTimer) clearTimeout(genHintTimer)
  if (tapHintTimer) clearTimeout(tapHintTimer)
})
</script>

<style scoped>
/* ── 顶栏 ── */
.rd-top {
  position: relative;
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
  background: var(--paper); border: 2.5px solid var(--line); border-radius: var(--r-lg);
  box-shadow: var(--pop-sm); padding: 10px 14px; margin-bottom: 16px;
}
.rd-round {
  width: 40px; height: 40px; border-radius: 14px; flex: none;
  background: var(--cream); border: 2.5px solid var(--line); color: var(--ink);
  display: flex; align-items: center; justify-content: center; cursor: pointer;
  transition: transform 0.25s var(--ease-out-quart), box-shadow 0.25s var(--ease-out-quart);
}
.rd-round:hover { transform: translate(-2px, -2px); box-shadow: var(--pop-sm); }
.rd-file { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 180px; }
.rd-file-ic {
  width: 38px; height: 38px; border-radius: 12px; flex: none;
  background: var(--sky-l); color: var(--sky); border: 2.5px solid var(--line);
  display: flex; align-items: center; justify-content: center;
}
.rd-file-info { min-width: 0; }
.rd-file-name {
  display: block; max-width: 100%; font-family: inherit; font-size: 14.5px; font-weight: 800;
  color: var(--ink); background: none; border: none; padding: 0; outline: none; cursor: pointer;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.rd-file-sub { font-size: 11.5px; color: var(--ink3); font-weight: 600; margin-top: 1px; }
.rd-pager {
  display: flex; align-items: center; gap: 2px; flex: none;
  background: var(--cream); border: 2.5px solid var(--line); border-radius: 999px; padding: 3px;
}
.rd-pager button {
  width: 30px; height: 30px; border-radius: 999px; border: none; background: none;
  color: var(--ink2); display: flex; align-items: center; justify-content: center; cursor: pointer;
  transition: background 0.2s;
}
.rd-pager button:hover { background: var(--warm); color: var(--ink); }
.rd-pager .icon { width: 16px; height: 16px; }
.rd-page-num { font-size: 13px; font-weight: 800; min-width: 58px; text-align: center; font-variant-numeric: tabular-nums; }
.rd-top-actions { display: flex; gap: 9px; flex: none; }
.rd-top-actions .btn { padding: 9px 15px; }

/* 目录弹层（顶栏下方悬浮） */
.toc-pop {
  position: absolute; top: calc(100% + 10px); right: 12px; z-index: 60;
  width: min(320px, calc(100vw - 48px)); max-height: 320px; overflow: auto;
  padding: 14px; box-shadow: var(--pop);
}
.toc-head { display: flex; align-items: center; justify-content: space-between; font-size: 14px; font-weight: 800; margin-bottom: 10px; }
.toc-list { display: flex; flex-direction: column; gap: 2px; }
.toc-item {
  text-align: left; font-family: inherit; font-size: 13px; font-weight: 650; color: var(--ink);
  background: none; border: none; padding: 8px 10px; border-radius: 10px; cursor: pointer;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.toc-item:hover { background: var(--warm); }
.toc-pages { display: grid; grid-template-columns: repeat(6, 1fr); gap: 6px; }
.toc-page {
  font-family: inherit; font-size: 12.5px; font-weight: 750; color: var(--ink2);
  background: var(--cream); border: 2px solid var(--line); border-radius: 9px; padding: 6px 0; cursor: pointer;
}
.toc-page.on { background: var(--orange); color: var(--onfill); }
.toc-empty { font-size: 12.5px; padding: 6px 2px; }

/* 生成提示气泡 */
.gen-hint {
  position: fixed; left: 50%; transform: translateX(-50%); top: 18px; z-index: 70;
  display: flex; align-items: center; gap: 8px;
  background: var(--ink); color: var(--onink); font-size: 13px; font-weight: 700;
  padding: 9px 16px; border-radius: 999px; box-shadow: var(--pop);
}

/* ── 主栅格 ── */
.rd-grid { display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 16px; align-items: start; }
.rd-grid.single { grid-template-columns: minmax(0, 1fr); }

/* ── 左：文档区 ── */
.rd-doc { padding: 0; overflow: hidden; display: flex; flex-direction: column; }
.rd-docbar {
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  padding: 10px 14px; border-bottom: 2.5px solid var(--line); background: var(--cream);
}
.rd-docbar-name {
  font-size: 12.5px; font-weight: 700; color: var(--ink2); min-width: 0;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.rd-docbar-tools { display: flex; align-items: center; gap: 6px; flex: none; }
.tool-btn {
  width: 30px; height: 30px; border-radius: 10px; border: none; background: none;
  color: var(--ink2); display: flex; align-items: center; justify-content: center; cursor: pointer;
  transition: all 0.2s var(--ease-out-quart);
}
.tool-btn .icon { width: 16px; height: 16px; }
.tool-btn:hover { background: var(--warm); color: var(--ink); }
.zoom-val { font-size: 11.5px; font-weight: 800; color: var(--ink2); min-width: 38px; text-align: center; font-variant-numeric: tabular-nums; }

.rd-tabs { display: inline-flex; gap: 3px; padding: 3px; background: var(--warm); border: 2px solid var(--line); border-radius: 999px; }
.rd-tabs button { padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 750; color: var(--ink2); background: none; border: none; cursor: pointer; transition: all 0.2s var(--ease); }
.rd-tabs button.on { background: var(--paper); color: var(--ink); box-shadow: var(--pop-sm); border: 2px solid var(--line); }

.doc-body { position: relative; height: calc(100vh - 320px); min-height: 380px; overflow: auto; padding: 22px 26px; }
.doc-body:fullscreen { background: var(--paper); padding: 6vh 8vw; }
.doc-body.full { background: var(--paper); }
.doc-text { font-family: inherit; white-space: pre-wrap; margin: 0; color: var(--ink); word-break: break-word; }
.source-mark { background: var(--ham); color: var(--ink); border-radius: 4px; box-shadow: 0 0 0 3px var(--ham); }
.source-banner { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; padding: 10px 14px; margin: 0 0 14px; border: 2px solid var(--orange); border-radius: 12px; background: var(--orange-l); color: var(--ink); font-size: 13px; font-weight: 700; }
.source-banner .btn { padding: 7px 12px; }
.rd-pdf-wrap { overflow: hidden; }
.rd-pdf { max-width: 100%; }

/* 底部操作栏 */
.rd-docfoot {
  position: relative;
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px; border-top: 2.5px solid var(--line); background: var(--cream); flex-wrap: wrap;
}
.rd-docfoot .btn { padding: 8px 14px; font-size: 13.5px; }
.rd-track {
  flex: 1; min-width: 90px; height: 12px; border-radius: 99px;
  background: var(--warm); border: 2.5px solid var(--line); overflow: hidden;
}
.rd-track i { display: block; height: 100%; background: var(--orange); border-radius: 99px; transition: width 0.4s var(--ease-out); }
.rd-setting { width: auto; padding: 0 10px; height: 34px; gap: 5px; font-size: 12.5px; font-weight: 750; }

.set-pop {
  position: absolute; bottom: calc(100% + 10px); right: 10px; z-index: 60;
  width: 240px; padding: 14px; box-shadow: var(--pop);
  display: flex; flex-direction: column; gap: 10px;
}
.set-row { display: flex; align-items: center; gap: 7px; flex-wrap: wrap; }
.set-label { font-size: 12px; font-weight: 800; color: var(--ink2); width: 34px; flex: none; }
.mini-btn {
  padding: 4px 11px; font-family: inherit; font-size: 12px; font-weight: 750;
  color: var(--ink2); background: var(--cream); border: 2px solid var(--line); border-radius: 8px;
  cursor: pointer; transition: all 0.2s var(--ease-out-quart);
}
.mini-btn:hover { background: var(--paper); color: var(--ink); box-shadow: var(--pop-sm); transform: translateY(-1px); }
.mini-btn.on { background: var(--orange); color: var(--onfill); }

.tooltip { position: fixed; z-index: 50; transform: translateX(-50%); }
.tip-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px; font-family: inherit; font-size: 13.5px; font-weight: 800;
  color: var(--onfill); background: var(--orange);
  border: 2.5px solid var(--line); border-radius: 12px; box-shadow: var(--pop); cursor: pointer;
}

/* ── 右栏 ── */
.rd-side { display: flex; flex-direction: column; gap: 16px; min-width: 0; }
.rd-panel { padding: 16px 16px 14px; }
.rp-head { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; position: relative; }
.rp-title { display: flex; align-items: center; gap: 7px; font-size: 14.5px; font-weight: 800; }
.rp-title .icon { width: 17px; height: 17px; color: var(--orange-d); }
.rp-count {
  font-size: 11.5px; font-weight: 800; color: var(--ink2);
  background: var(--warm); border: 2px solid var(--line); border-radius: 999px; padding: 1px 9px;
}
.rp-logo {
  position: absolute; right: -4px; top: -8px; width: 40px; height: 40px;
  transform: rotate(10deg); pointer-events: none;
  filter: drop-shadow(2px 2px 0 rgba(61, 43, 28, 0.14));
}

/* 卡片列表（新生成 / 已提取共用） */
.card-list { display: flex; flex-direction: column; gap: 8px; }
.kitem { border: 2px solid var(--hairline); border-radius: 14px; background: var(--paper); overflow: hidden; transition: border-color 0.2s; }
.kitem.open { border-color: var(--line); }
.kitem-head {
  display: flex; align-items: center; gap: 10px; width: 100%;
  padding: 10px 11px; background: none; border: none; cursor: pointer; text-align: left; font-family: inherit;
}
.kitem-head.plain { border: 2px solid var(--hairline); border-radius: 14px; background: var(--paper); transition: all 0.2s var(--ease-out-quart); }
.kitem-head.plain:hover { transform: translateX(3px); border-color: var(--line); box-shadow: var(--pop-sm); }
.kitem-ic {
  width: 36px; height: 36px; border-radius: 12px; flex: none;
  display: flex; align-items: center; justify-content: center;
  border: 2px solid var(--line);
}
.kitem-ic .icon { width: 17px; height: 17px; }
.kitem-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.kitem-title {
  font-size: 13px; font-weight: 750; color: var(--ink); line-height: 1.4;
  display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden;
}
.kitem-src { font-size: 11px; color: var(--ink3); font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kitem-tag {
  flex: none; font-size: 10.5px; font-weight: 800; padding: 2px 8px; border-radius: 999px;
  border: 2px solid currentColor; opacity: 0.95;
}
.kitem-chev { width: 14px !important; height: 14px !important; flex: none; color: var(--ink3); transition: transform 0.25s var(--ease-out-quart); }
.kitem.open .kitem-chev, .kitem.open > .kitem-chev { transform: rotate(90deg); }
.kitem-body { padding: 2px 11px 12px; border-top: 2px dashed var(--hairline); padding-top: 10px; }
.kitem-edit-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.kitem-edit-row select {
  font-family: inherit; font-size: 12.5px; color: var(--ink); background: var(--cream);
  border: 2px solid var(--line); border-radius: 9px; padding: 3px 8px; outline: none;
}
.gen-conf { font-size: 11.5px; color: var(--mint-d); font-weight: 700; }
.field { display: block; margin-bottom: 10px; }
.field span { display: block; font-size: 12px; font-weight: 750; color: var(--ink2); margin-bottom: 5px; }
.field textarea, .field select {
  width: 100%; font-family: inherit; font-size: 14px; color: var(--ink);
  background: var(--cream); border: 2.5px solid var(--line); border-radius: 11px; padding: 8px 11px; outline: none; resize: vertical;
}
.field textarea:focus { border-color: var(--orange); }
.field select { width: 100%; }
.err { color: var(--berry); font-size: 13px; font-weight: 650; margin-bottom: 10px; }
.gen-actions { display: flex; justify-content: flex-end; align-items: center; gap: 10px; margin-top: 4px; }
.tap-hint { font-size: 12.5px; color: var(--berry); font-weight: 650; margin-bottom: 8px; text-align: right; }

.gen-box { text-align: center; padding: 24px 12px; border: 2px dashed var(--hairline); border-radius: 16px; }
.gen-wait { display: flex; justify-content: center; padding: 14px 0; }
.gen-wait > * { max-width: 100%; }
.gen-ic { width: 44px; height: 44px; margin: 0 auto 10px; border-radius: 14px; background: var(--warm); border: 2px solid var(--line); display: flex; align-items: center; justify-content: center; color: var(--ink3); }
.gen-empty-t { font-size: 14px; font-weight: 800; }
.gen-empty-s { font-size: 12.5px; margin-top: 5px; line-height: 1.6; }
.hint-line { margin-top: 12px; font-size: 12px; color: var(--ink3); line-height: 1.7; font-weight: 600; }

/* 右栏底条 */
.rd-sidefoot {
  display: flex; align-items: center; gap: 10px;
  background: var(--ham-l); border: 2.5px solid var(--line); border-radius: var(--r-md);
  box-shadow: var(--pop-sm); padding: 9px 13px;
}
.rd-sidefoot img { width: 34px; height: 34px; flex: none; }
.rd-sidefoot-txt { flex: 1; font-size: 12.5px; font-weight: 750; color: var(--ink2); }
.rd-sidefoot-btn {
  font-family: inherit; font-size: 12.5px; font-weight: 750; color: var(--ink2);
  background: none; border: none; cursor: pointer; padding: 4px 6px; border-radius: 8px;
}
.rd-sidefoot-btn:hover { color: var(--orange-d); }

/* 弹窗 */
.mask { position: fixed; inset: 0; background: rgba(10, 7, 4, 0.5); z-index: 90; display: flex; align-items: center; justify-content: center; padding: 20px; }
.view-card { width: min(460px, 100%); padding: 22px 22px 18px; box-shadow: var(--pop-lg); background: var(--paper); border-radius: var(--r-lg); border: 2.5px solid var(--line); }
.vc-row { display: flex; align-items: flex-start; gap: 9px; padding: 11px 13px; border-radius: 13px; background: var(--warm); border: 2px solid var(--line); margin-bottom: 9px; }
.vc-row:last-child { margin-bottom: 0; }
.vc-row .pv-tag { width: 22px; height: 22px; }
.pv-tag {
  flex: none; width: 20px; height: 20px; display: grid; place-items: center;
  border-radius: 7px; background: var(--paper); border: 2px solid var(--line);
  font-size: 11px; font-weight: 800; color: var(--orange-d);
}
.pv-tag-b { color: var(--mint-d); }
.pv-text { flex: 1; font-size: 13px; line-height: 1.6; color: var(--ink); font-weight: 600; word-break: break-word; }
.pv-empty { color: var(--ink3); font-weight: 500; }

/* 弹层过渡 */
.pop-enter-active { animation: popIn 0.3s var(--ease-out-quint) both; }
.pop-leave-active { animation: popIn 0.16s var(--ease-in-quart) reverse both; }
@keyframes popIn {
  from { opacity: 0; transform: translateY(-6px) scale(0.97); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

/* ── 屏幕自适应 ── */
@media (max-width: 1160px) {
  .rd-grid { grid-template-columns: minmax(0, 1fr) 320px; }
}
@media (max-width: 1000px) {
  .rd-grid { grid-template-columns: minmax(0, 1fr); }
  .rd-side { order: 2; }
}
@media (max-width: 760px) {
  .rd-top { gap: 9px; padding: 10px; }
  .rd-pager { order: 3; }
  .rd-file { min-width: 0; flex: 1 1 100%; order: 2; }
  .rd-top-actions { order: 4; }
  .rd-top-actions .btn { padding: 9px 12px; }
  .rd-btn-txt { display: none; }
  .rd-top-actions .btn .icon { width: 18px; height: 18px; }
  .doc-body { padding: 16px; height: calc(100vh - 360px); }
  .rd-docfoot { gap: 8px; }
  .rp-logo { width: 32px; height: 32px; top: -6px; }
}
</style>
