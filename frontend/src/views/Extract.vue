<template>
  <div>
    <div class="ex-head rise">
      <div>
        <div class="h-page">AI 提炼</div>
        <div class="h-sub">丢进一份文件，AI 通读后产出一份 Markdown 笔记，你再把知识点拆成卡片</div>
      </div>
      <span class="chip chip-o">
        <svg class="icon" style="width:14px;height:14px"><use href="#i-spark" /></svg>
        提炼引擎已就绪
      </span>
    </div>

    <div class="ex-grid">
      <!-- ── 左栏：1 选择来源 + 2 处理进度 ── -->
      <div class="ex-left">
        <div class="card pad rise">
          <div class="step-sec"><span class="step-no">1</span><span class="h-sec">选择来源</span></div>

          <div class="src-tabs">
            <button class="src-tab on">
              <svg class="icon"><use href="#i-doc" /></svg>
              <span>文件<small>PDF / EPUB / DOCX / MD</small></span>
            </button>
            <button class="src-tab" disabled title="视频转写需要语音识别服务，即将支持">
              <svg class="icon"><use href="#i-film" /></svg>
              <span>视频<small>即将支持</small></span>
            </button>
          </div>

          <!-- 拖拽上传：传完自动解析 + 提炼 -->
          <div class="dropzone" @click="triggerUpload" @dragover.prevent @drop.prevent="onDrop">
            <div class="dz-ic"><svg class="icon"><use href="#i-upload" /></svg></div>
            <div class="dz-t">把文件丢进来</div>
            <div class="muted dz-s">解析完自动开始提炼</div>
            <input ref="fileInput" type="file" hidden @change="onFileChange" />
          </div>
          <div v-if="uploadItem.visible" style="margin-top:10px">
            <CallChip icon="#i-doc" :name="uploadItem.name" :status="uploadItem.status"
                      :expected-ms="uploadItem.expectedMs" @retry="runUpload" />
          </div>

          <div class="or-line"><span>或从已解析的文件选</span></div>
          <select v-model="sourceDocId" class="src-select">
            <option :value="null" disabled>选一份已解析的文件</option>
            <option v-for="f in files" :key="f.doc_id!" :value="f.doc_id!">{{ f.name }}</option>
          </select>
          <button class="btn btn-primary ex-run" :disabled="!sourceDocId || loading" @click="run(sourceDocId)">
            <svg class="icon"><use href="#i-spark" /></svg>{{ loading ? '提炼中…' : '开始提炼' }}
          </button>
        </div>

        <!-- 2 处理进度 -->
        <div class="card pad rise" style="margin-top:14px">
          <div class="step-sec"><span class="step-no">2</span><span class="h-sec">处理进度</span></div>
          <div class="steps">
            <div v-for="(s, i) in STEPS" :key="i" class="step-row" :data-state="stepState(i)">
              <span class="step-dot">
                <svg v-if="stepState(i) === 'done'" class="icon"><use href="#i-check" /></svg>
                <template v-else>{{ i + 1 }}</template>
              </span>
              <span class="step-info">
                <b>{{ s.name }}</b>
                <small>{{ s.desc }}</small>
              </span>
            </div>
          </div>
          <p class="err" v-if="err">{{ err }}</p>
        </div>

        <!-- 历史笔记（紧凑） -->
        <div class="card pad rise" style="margin-top:14px">
          <div class="h-sec" style="margin-bottom:10px">历史笔记</div>
          <div v-if="!notes.length" class="muted" style="font-size:12.5px">还没有笔记。</div>
          <div v-for="n in notes" :key="n.id" class="hist-item" :class="{ on: currentNote?.id === n.id }" @click="openNote(n.id)">
            {{ n.title }}
          </div>
        </div>
      </div>

      <!-- ── 右栏：3 提炼结果 + 4 拆卡 ── -->
      <div class="ex-right">
        <div class="card pad rise">
          <div class="res-head">
            <div class="step-sec"><span class="step-no">3</span><span class="h-sec">提炼结果</span></div>
            <div v-if="currentNote" class="res-tools">
              <div class="view-tabs">
                <button :class="{ on: viewMode === 'read' }" @click="viewMode = 'read'">阅读</button>
                <button :class="{ on: viewMode === 'source' }" @click="viewMode = 'source'">源码</button>
              </div>
              <button class="mini-btn" @click="copyMd">{{ copied ? '已复制' : '复制' }}</button>
              <button class="mini-btn" @click="downloadMd">
                <svg class="icon" style="width:13px;height:13px"><use href="#i-download" /></svg>下载 .md
              </button>
            </div>
          </div>

          <!-- 空态 -->
          <div v-if="!currentNote && !loading" class="res-empty">
            <div class="res-empty-ic"><svg class="icon"><use href="#i-md" /></svg></div>
            <div class="gen-empty-t">还没有产出</div>
            <div class="muted gen-empty-s">左边选一个来源，或直接把文件拖进来<br />几十秒后这里会出一份 Markdown 笔记</div>
          </div>

          <!-- 产出 -->
          <template v-if="currentNote">
            <div class="note-title-row">
              <h3 class="note-title">{{ currentNote.title }}</h3>
            </div>
            <!-- 阅读视图：轻量 md 渲染 -->
            <div v-if="viewMode === 'read'" class="note-read" v-html="renderedMd"></div>
            <!-- 源码视图 -->
            <pre v-else class="note-source">{{ currentNote.content_md }}</pre>
          </template>
        </div>

        <!-- 4 拆卡 -->
        <div class="card pad rise" style="margin-top:18px">
          <div class="res-head">
            <div class="step-sec"><span class="step-no">4</span><span class="h-sec">把知识点拆成卡片</span></div>
            <button
              v-if="currentNote && selectable.length"
              class="btn btn-primary"
              :disabled="!selectedIds.length || !targetDeckId || saving"
              @click="splitCards"
            >
              <svg class="icon"><use href="#i-scissor" /></svg>{{ saving ? '拆卡中…' : `拆成卡片${selectedIds.length ? `（${selectedIds.length}）` : ''}` }}
            </button>
          </div>

          <template v-if="currentNote && currentNote.candidates.length">
            <div class="cand-sub">
              AI 标出了 <b>{{ currentNote.candidates.length }}</b> 个适合出卡的考点，勾选你想要的<span v-if="selectedIds.length">，已选 {{ selectedIds.length }} 个</span>
            </div>
            <div class="row gap8" style="margin-bottom:12px">
              <select v-model="targetDeckId" class="deck-select">
                <option :value="null" disabled>选择存入的卡组</option>
                <option v-for="d in decks" :key="d.id" :value="d.id">{{ d.name }}</option>
              </select>
              <button class="mini-btn" @click="toggleAll">{{ allSelected ? '取消全选' : '全选' }}</button>
            </div>
            <div class="cand-list">
              <label v-for="c in currentNote.candidates" :key="c.id" class="cand-item" :class="{ done: !!c.card_id }">
                <input v-if="!c.card_id" type="checkbox" v-model="selectedIds" :value="c.id" />
                <span v-else class="cand-done-tag">已入库</span>
                <div class="cand-body">
                  <div class="cand-front">{{ c.front }}</div>
                  <div class="cand-back" v-if="c.back">{{ c.back }}</div>
                </div>
                <span class="cand-meta">
                  <span class="cand-type">{{ typeLabel(c.card_type) }}</span>
                  <span class="cand-conf">{{ Math.round(c.confidence * 100) }}%</span>
                </span>
              </label>
            </div>
            <p class="err" v-if="err">{{ err }}</p>
          </template>
          <div v-else-if="currentNote" class="muted" style="font-size:13px">
            这份笔记里没有找到适合出卡的考点。
          </div>
          <div v-else class="cand-empty">
            <div class="res-empty-ic" style="width:40px;height:40px"><svg class="icon"><use href="#i-cards" /></svg></div>
            <div style="font-size:13.5px;font-weight:800">等笔记出来才有东西可拆</div>
            <div class="muted" style="font-size:12.5px;margin-top:4px">每条候选都标了建议题型和置信度</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { decksApi } from '@/api/decks'
import { extractApi } from '@/api/extract'
import { filesApi } from '@/api/files'
import CallChip from '@/components/common/CallChip.vue'
import type { Deck, FileItem, Note, NoteDetail } from '@/types/api'

/* ── 数据 ── */
const files = ref<FileItem[]>([])
const notes = ref<Note[]>([])
const currentNote = ref<NoteDetail | null>(null)
const decks = ref<Deck[]>([])
const sourceDocId = ref<string | null>(null)
const loading = ref(false)
const saving = ref(false)
const err = ref('')
const selectedIds = ref<string[]>([])
const targetDeckId = ref<string | null>(null)
const viewMode = ref<'read' | 'source'>('read')
const copied = ref(false)

/* ── 来源上传（复用内容库解析，解析完自动提炼）── */
const fileInput = ref<HTMLInputElement>()
const uploadItem = reactive({
  visible: false,
  name: '',
  status: 'idle' as 'idle' | 'running' | 'done' | 'error',
  expectedMs: 1500,
})
let lastUploadFile: File | null = null

function triggerUpload() {
  fileInput.value?.click()
}
function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const f = input.files?.[0]
  if (f) startFromUpload(f)
  input.value = ''
}
function onDrop(e: DragEvent) {
  const f = e.dataTransfer?.files?.[0]
  if (f) startFromUpload(f)
}
const ACCEPTED_EXTS = ['pdf', 'docx', 'pptx', 'epub', 'md', 'markdown', 'txt']

async function startFromUpload(f: File) {
  const ext = (f.name.includes('.') ? f.name.split('.').pop()! : '').toLowerCase()
  // 预检：不支持的格式（含视频）直接明确提示，不发起无意义的上传
  if (!ACCEPTED_EXTS.includes(ext)) {
    lastUploadFile = null
    uploadItem.visible = true
    uploadItem.name = f.name
    uploadItem.status = 'error'
    uploadItem.expectedMs = 1500
    err.value = ext === 'mp4' || ext === 'mov' || ext === 'mkv'
      ? '视频提炼暂未支持，先传一份文档吧'
      : `.${ext || '???'} 暂时提炼不了，支持：PDF / Word / PPT / EPUB / MD / TXT`
    return
  }
  lastUploadFile = f
  uploadItem.visible = true
  uploadItem.name = f.name
  uploadItem.expectedMs = Math.min(6000, Math.max(1500, 1200 + f.size / 1024))
  uploadItem.status = 'running'
  err.value = ''
  try {
    const res = await filesApi.upload(f)
    await load()
    const fresh = files.value.find((x) => x.name === f.name && x.doc_id)
    if (fresh?.doc_id) {
      uploadItem.status = 'done'
      await run(fresh.doc_id)
    } else {
      // 上传了但没解析出正文（扫描件/损坏文件），给明确原因
      uploadItem.status = 'error'
      err.value = res.data.doc_error || '这份文件没解析出正文，提炼不了'
    }
  } catch {
    uploadItem.status = 'error'
    err.value = '上传或解析失败，点 chip 重试'
  }
}
function runUpload() {
  if (lastUploadFile) startFromUpload(lastUploadFile)
}

/* ── 五步处理进度（AI 步悬停等真实结果，CallChip 同款时序）── */
const STEPS = [
  { name: '读取来源', desc: '找到你选的文件' },
  { name: '提取正文', desc: '解析文字，图表转文字' },
  { name: '切分段落', desc: '按主题与篇幅切成小块' },
  { name: 'AI 提炼知识点', desc: '去重、合并、标注置信度' },
  { name: '生成 Markdown', desc: '输出带目录的笔记' },
]
const stepIdx = ref(-1) // -1 idle；0..4 进行到第几步；5 全部完成
const stepTimers: ReturnType<typeof setTimeout>[] = []

function stepState(i: number): 'pending' | 'active' | 'done' {
  if (stepIdx.value > i) return 'done'
  if (stepIdx.value === i) return 'active'
  return 'pending'
}
function startSteps() {
  stopSteps()
  stepIdx.value = 0
  const delays = [700, 900, 700, 0, 0] // 第 4 步（AI）悬停直到返回；第 5 步随返回跳完
  let acc = 0
  delays.forEach((d, i) => {
    acc += d
    if (d > 0) stepTimers.push(setTimeout(() => (stepIdx.value = i + 1), acc))
  })
}
function finishSteps() {
  stopSteps()
  stepIdx.value = 5
  stepTimers.push(setTimeout(() => (loading.value = false), 450))
}
function stopSteps() {
  stepTimers.forEach(clearTimeout)
  stepTimers.length = 0
}

/* ── 提炼 ── */
async function run(docId: string | null) {
  if (!docId || loading.value) return
  loading.value = true
  err.value = ''
  currentNote.value = null
  selectedIds.value = []
  viewMode.value = 'read'
  startSteps()
  try {
    const res = await extractApi.fromFile(docId)
    currentNote.value = res.data
    selectedIds.value = res.data.candidates.filter((c) => c.confidence >= 0.8 && !c.card_id).map((c) => c.id)
    finishSteps()
    await load()
  } catch (e: any) {
    stopSteps()
    stepIdx.value = -1
    loading.value = false
    err.value = e?.response?.data?.message || '提炼失败'
  }
}

async function openNote(id: string) {
  if (loading.value) return
  err.value = ''
  const res = await extractApi.getNote(id)
  currentNote.value = res.data
  selectedIds.value = []
  viewMode.value = 'read'
}

/* ── 结果工具：渲染 / 复制 / 下载 ── */
const renderedMd = computed(() => (currentNote.value ? renderMd(currentNote.value.content_md) : ''))

function renderMd(md: string): string {
  // 页面标题行已单独展示，跳过管线生成的首个 `# 标题` 避免重复
  const body = md.replace(/^#[^\n]*\n+/, '')
  const esc = body.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  const inline = (s: string) => s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  const out: string[] = []
  let inList = false
  for (const line of esc.split('\n')) {
    const li = line.match(/^\s*[-*] (.+)$/)
    if (li) {
      if (!inList) { out.push('<ul>'); inList = true }
      out.push(`<li>${inline(li[1])}</li>`)
      continue
    }
    if (inList) { out.push('</ul>'); inList = false }
    const h = line.match(/^(#{1,4}) (.+)$/)
    if (h) { out.push(`<h${Math.min(4, h[1].length + 1)}>${inline(h[2])}</h${Math.min(4, h[1].length + 1)}>`); continue }
    if (!line.trim()) { out.push(''); continue }
    out.push(`<p>${inline(line)}</p>`)
  }
  if (inList) out.push('</ul>')
  return out.join('\n')
}

async function copyMd() {
  if (!currentNote.value) return
  await navigator.clipboard.writeText(currentNote.value.content_md)
  copied.value = true
  setTimeout(() => (copied.value = false), 1500)
}
function downloadMd() {
  if (!currentNote.value) return
  const blob = new Blob([currentNote.value.content_md], { type: 'text/markdown;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${currentNote.value.title}.md`
  a.click()
  URL.revokeObjectURL(a.href)
}

/* ── 考点候选 ── */
const selectable = computed(() => (currentNote.value?.candidates || []).filter((c) => !c.card_id))
const allSelected = computed(() => selectable.value.length > 0 && selectable.value.every((c) => selectedIds.value.includes(c.id)))

function toggleAll() {
  if (allSelected.value) selectedIds.value = []
  else selectedIds.value = selectable.value.map((c) => c.id)
}

async function splitCards() {
  if (!currentNote.value || !targetDeckId.value || !selectedIds.value.length) return
  saving.value = true
  err.value = ''
  try {
    await extractApi.splitCandidates(currentNote.value.id, selectedIds.value, targetDeckId.value)
    const res = await extractApi.getNote(currentNote.value.id)
    currentNote.value = res.data
    selectedIds.value = []
  } catch (e: any) {
    err.value = e?.response?.data?.message || '拆卡失败'
  } finally {
    saving.value = false
  }
}

function typeLabel(t: string) {
  return { basic: '问答', cloze: '挖空', quote: '书摘' }[t] || t
}

async function load() {
  const [f, n, d] = await Promise.all([filesApi.list(), extractApi.listNotes(), decksApi.list()])
  files.value = f.data.filter((x) => x.doc_id && x.doc_status === 'done' && !x.is_dir)
  notes.value = n.data
  decks.value = d.data
  if (!sourceDocId.value && files.value.length) sourceDocId.value = files.value[0].doc_id!
}

onMounted(load)
</script>

<style scoped>
.ex-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 18px; }

.ex-grid { display: grid; grid-template-columns: 320px 1fr; gap: 18px; align-items: start; }
@media (max-width: 980px) { .ex-grid { grid-template-columns: 1fr; } }

.pad { padding: 18px 20px; }
.muted { color: var(--ink2); font-size: 13px; }
.h-sec { font-size: 15px; font-weight: 800; }

/* 步骤编号 + 标题 */
.step-sec { display: flex; align-items: center; gap: 9px; margin-bottom: 14px; }
.step-no {
  width: 26px; height: 26px; display: grid; place-items: center; flex: none;
  border-radius: 9px; background: var(--orange); color: var(--onfill);
  border: 2px solid var(--line); box-shadow: var(--pop-sm);
  font-size: 13px; font-weight: 800;
}

/* 来源 tab：文件 / 视频 */
.src-tabs { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 14px; }
.src-tab {
  display: flex; align-items: center; gap: 9px; padding: 10px 12px;
  border: 2.5px solid var(--line); border-radius: var(--r-md); background: var(--paper);
  box-shadow: var(--pop-sm); cursor: pointer; font-family: inherit; color: var(--ink);
  transition: transform 0.2s var(--ease-out-quart), background 0.2s ease;
}
.src-tab span { display: flex; flex-direction: column; align-items: flex-start; font-size: 13.5px; font-weight: 800; line-height: 1.25; }
.src-tab small { font-size: 10.5px; font-weight: 650; color: var(--ink3); }
.src-tab .icon { width: 20px; height: 20px; flex: none; color: var(--orange-d); }
.src-tab:disabled { opacity: 0.5; cursor: not-allowed; box-shadow: none; background: var(--cream); }
.src-tab:disabled .icon { color: var(--ink3); }

/* 拖拽区 */
.dropzone {
  text-align: center; padding: 20px 12px; cursor: pointer;
  border: 2.5px dashed var(--line); border-radius: var(--r-md); background: var(--cream);
  transition: background 0.2s ease, transform 0.2s var(--ease-out-quart);
}
.dropzone:hover { background: var(--ham-l); transform: translateY(-1px); }
.dz-ic {
  width: 38px; height: 38px; margin: 0 auto 8px; display: grid; place-items: center;
  border-radius: 12px; background: var(--paper); border: 2px solid var(--line); box-shadow: var(--pop-sm);
  color: var(--orange-d);
}
.dz-t { font-size: 14px; font-weight: 800; }
.dz-s { font-size: 12px; margin-top: 3px; }

.or-line { display: flex; align-items: center; gap: 10px; margin: 14px 0 10px; color: var(--ink3); font-size: 11.5px; font-weight: 700; }
.or-line::before, .or-line::after { content: ''; flex: 1; height: 2px; background: var(--hairline); border-radius: 2px; }

.src-select, .deck-select {
  width: 100%; font-family: inherit; font-size: 13.5px; color: var(--ink);
  background: var(--cream); border: 2.5px solid var(--line); border-radius: 11px; padding: 9px 11px; outline: none;
}
.ex-run { width: 100%; margin-top: 10px; justify-content: center; display: inline-flex; align-items: center; gap: 7px; }

/* 五步进度 */
.steps { display: flex; flex-direction: column; gap: 4px; }
.step-row { display: flex; align-items: center; gap: 11px; padding: 7px 8px; border-radius: 12px; }
.step-dot {
  width: 28px; height: 28px; flex: none; display: grid; place-items: center;
  border-radius: 10px; border: 2px solid var(--line);
  font-size: 12.5px; font-weight: 800; background: var(--cream); color: var(--ink3);
  transition: all 0.3s var(--ease-out-quart);
}
.step-dot .icon { width: 14px; height: 14px; }
.step-info { display: flex; flex-direction: column; min-width: 0; }
.step-info b { font-size: 13.5px; font-weight: 750; color: var(--ink3); transition: color 0.3s ease; }
.step-info small { font-size: 11.5px; color: var(--ink3); font-weight: 600; }
.step-row[data-state='active'] .step-dot {
  background: var(--orange); color: var(--onfill);
  animation: stepBreath 1.6s var(--ease) infinite;
}
.step-row[data-state='active'] .step-info b { color: var(--ink); }
.step-row[data-state='done'] .step-dot { background: var(--mint); color: var(--onfill); }
.step-row[data-state='done'] .step-info b { color: var(--ink); }
@keyframes stepBreath {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.55; }
}

.hist-item {
  padding: 8px 11px; border-radius: 10px; border: 2px solid var(--hairline);
  font-size: 12.5px; font-weight: 700; color: var(--ink2); cursor: pointer;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: 6px;
  transition: background 0.15s ease;
}
.hist-item:hover { background: var(--warm); }
.hist-item.on { border-color: var(--orange); color: var(--ink); background: var(--orange-l); }

/* 结果卡 */
.res-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; }
.res-tools { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.view-tabs { display: inline-flex; gap: 3px; padding: 3px; background: var(--warm); border: 2px solid var(--line); border-radius: 999px; }
.view-tabs button { padding: 4px 13px; border-radius: 999px; font-size: 12px; font-weight: 750; color: var(--ink2); background: none; border: none; cursor: pointer; }
.view-tabs button.on { background: var(--paper); color: var(--ink); box-shadow: var(--pop-sm); border: 2px solid var(--line); }
.mini-btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 12px; font-family: inherit; font-size: 12px; font-weight: 750;
  color: var(--ink2); background: var(--paper); border: 2px solid var(--line);
  border-radius: 9px; cursor: pointer; white-space: nowrap;
  transition: all 0.2s var(--ease-out-quart);
}
.mini-btn:hover { color: var(--ink); box-shadow: var(--pop-sm); transform: translateY(-1px); }

.res-empty { text-align: center; padding: 42px 16px; border: 2.5px dashed var(--hairline); border-radius: var(--r-md); }
.res-empty-ic {
  width: 44px; height: 44px; margin: 0 auto 10px; display: grid; place-items: center;
  border-radius: 13px; background: var(--ham-l); border: 2px solid var(--line);
  color: var(--ham-d); font-weight: 800; font-size: 12px;
}
.res-empty-ic .icon { width: 22px; height: 22px; }
.gen-empty-t { font-size: 14.5px; font-weight: 800; }
.gen-empty-s { font-size: 12.5px; margin-top: 6px; line-height: 1.65; }

.note-title-row { margin-bottom: 10px; }
.note-title { font-size: 19px; font-weight: 800; letter-spacing: -0.4px; }

/* 阅读视图（轻量 md 渲染） */
.note-read {
  font-size: 14px; line-height: 1.8; color: var(--ink);
  background: var(--cream); border: 2px solid var(--hairline); border-radius: 14px;
  padding: 18px 20px; max-height: 380px; overflow: auto;
}
.note-read :deep(h2) { font-size: 17px; font-weight: 800; margin: 4px 0 8px; }
.note-read :deep(h3) { font-size: 14.5px; font-weight: 800; margin: 12px 0 6px; color: var(--ink); }
.note-read :deep(h4) { font-size: 13.5px; font-weight: 800; margin: 10px 0 4px; }
.note-read :deep(ul) { margin: 4px 0 8px; padding-left: 20px; }
.note-read :deep(li) { margin-bottom: 4px; }
.note-read :deep(p) { margin-bottom: 6px; }
.note-read :deep(strong) { font-weight: 800; }

.note-source {
  font-family: inherit; font-size: 13px; line-height: 1.7; white-space: pre-wrap;
  background: var(--cream); border: 2px solid var(--hairline); border-radius: 14px;
  padding: 16px 18px; max-height: 380px; overflow: auto; margin: 0;
}

/* 拆卡 */
.cand-sub { font-size: 13px; color: var(--ink2); font-weight: 650; margin-bottom: 12px; }
.cand-sub b { color: var(--orange-d); }
.cand-list { display: flex; flex-direction: column; gap: 8px; }
.cand-item {
  display: flex; align-items: flex-start; gap: 10px; padding: 11px 13px;
  border: 2px solid var(--hairline); border-radius: 12px; cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}
.cand-item:hover { background: var(--warm); }
.cand-item:has(input:checked) { border-color: var(--orange); background: var(--orange-l); }
.cand-item input { margin-top: 4px; flex: none; accent-color: var(--orange); }
.cand-item.done { opacity: 0.55; cursor: default; }
.cand-done-tag { flex: none; font-size: 11px; font-weight: 800; color: var(--mint-d); background: var(--mint-l); border-radius: 99px; padding: 1px 8px; margin-top: 2px; border: 1.5px solid var(--line); }
.cand-body { flex: 1; min-width: 0; }
.cand-front { font-size: 13.5px; font-weight: 700; }
.cand-back { font-size: 12px; color: var(--ink2); margin-top: 3px; }
.cand-meta { flex: none; display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.cand-type { font-size: 11px; font-weight: 800; color: var(--ink3); border: 1.5px solid var(--line); border-radius: 99px; padding: 1px 8px; }
.cand-conf { font-size: 11px; font-weight: 800; color: var(--mint-d); font-variant-numeric: tabular-nums; }
.cand-empty { text-align: center; padding: 26px 12px; border: 2.5px dashed var(--hairline); border-radius: var(--r-md); }

.err { color: var(--berry); font-size: 13px; font-weight: 650; margin-top: 10px; }
</style>
