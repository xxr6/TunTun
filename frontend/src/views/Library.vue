<template>
  <div>
    <div class="row between wrap gap12 rise" style="margin-bottom:18px">
      <div>
        <div class="h-page">内容库</div>
        <div class="h-sub">{{ files.length }} 份资料 · 已解析 {{ doneCount }} 份</div>
      </div>
      <div class="row gap8">
        <div class="row gap8 search-box">
          <svg class="icon" style="width:17px;height:17px;color:var(--ink3)"><use href="#i-search" /></svg>
          <input v-model="keyword" placeholder="搜文件或内容" />
        </div>
        <button class="btn btn-primary" @click="folderModal = true">
          <svg class="icon"><use href="#i-plus" /></svg>新建
        </button>
      </div>
    </div>

    <!-- 拖拽上传 -->
    <div class="dropzone rise" style="margin-bottom:20px" @click="triggerUpload" @dragover.prevent @drop.prevent="onDrop">
      <div class="dz-ic"><svg class="icon"><use href="#i-upload" /></svg></div>
      <div style="font-size:15px;font-weight:800">把资料丢进来，自动帮你解析</div>
      <div class="muted" style="font-size:13px;margin-top:5px">PDF · Word · PPT · EPUB · Markdown · TXT，进来就自动解析</div>
      <input ref="fileInput" type="file" multiple hidden @change="onFileChange" />
    </div>

    <!-- 上传 / 解析等待 chips -->
    <div v-if="uploads.length" class="up-chips rise">
      <CallChip
        v-for="u in uploads" :key="u.id" icon="#i-doc" :name="u.name"
        :argument="uploadArg(u)" :status="u.status" :expected-ms="u.expectedMs"
        @retry="runUpload(u)"
      />
    </div>

    <!-- 筛选 -->
    <div class="row gap8 wrap rise" style="margin-bottom:16px">
      <button class="chip chip-o" :style="filter === 'all' ? chipOn : ''" @click="filter = 'all'">全部 {{ files.length }}</button>
      <button class="chip chip-g" :style="filter === 'done' ? chipOn : ''" @click="filter = 'done'">已解析</button>
      <button class="chip chip-g" :style="filter === 'failed' ? chipOn : ''" @click="filter = 'failed'">还没处理</button>
    </div>

    <!-- 文件卡片网格 -->
    <div class="masonry">
      <div v-for="f in filteredFiles" :key="f.id" class="fcard rise" @click="onOpen(f)">
        <div class="fi" :style="{ background: typeMeta(f.ext).bg, color: typeMeta(f.ext).fg }">
          <svg class="icon"><use :href="typeMeta(f.ext).icon" /></svg>
        </div>
        <div class="fn">{{ f.name }}</div>
        <div class="fm">{{ f.ext.toUpperCase() || '文件' }} · {{ formatSize(f.size) }} · {{ timeAgo(f.created_at) }}</div>
        <div class="row gap8" style="margin-top:9px">
          <span class="chip" :class="statusChip(f.doc_status)">{{ statusLabel(f.doc_status) }}</span>
          <button v-if="f.doc_status === 'failed'" class="chip chip-o retry-btn"
                  :disabled="retrying === f.id" @click.stop="retry(f)">
            {{ retrying === f.id ? '重试中…' : '重试' }}
          </button>
        </div>
        <div v-if="f.doc_status === 'failed' && f.doc_error" class="ferr" :title="f.doc_error">{{ f.doc_error }}</div>
        <div class="fbar"><i :style="{ width: statusWidth(f.doc_status), background: statusColor(f.doc_status) }"></i></div>
      </div>
      <div v-if="!filteredFiles.length" class="fcard" style="text-align:center">
        <div class="muted" style="font-size:13.5px">还没有文件，把资料拖进来试试。</div>
      </div>
    </div>

    <!-- 新建文件夹弹窗 -->
    <div v-if="folderModal" class="mask" @click.self="folderModal = false">
      <div class="card modal-card">
        <h3 class="modal-title">新建文件夹</h3>
        <label class="field"><span>名称</span><input v-model="folderName" placeholder="考研资料" @keyup.enter="createFolder" /></label>
        <p class="err" v-if="err">{{ err }}</p>
        <div class="modal-actions">
          <button class="btn" @click="folderModal = false">取消</button>
          <button class="btn btn-primary" @click="createFolder">创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, markRaw, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { documentsApi, filesApi } from '@/api/files'
import CallChip from '@/components/common/CallChip.vue'
import type { FileItem } from '@/types/api'

const router = useRouter()
const files = ref<FileItem[]>([])
const keyword = ref('')
const filter = ref<'all' | 'done' | 'failed'>('all')
const fileInput = ref<HTMLInputElement>()
const folderModal = ref(false)
const folderName = ref('')
const err = ref('')
const retrying = ref('')
const chipOn = 'box-shadow: var(--pop-sm); background: var(--paper); color: var(--ink)'

const doneCount = computed(() => files.value.filter((f) => f.doc_status === 'done').length)

// 搜索走后端（可命中解析正文、跨目录），这里只做状态筛选
const filteredFiles = computed(() => {
  let list = files.value
  if (filter.value === 'done') list = list.filter((f) => f.doc_status === 'done')
  if (filter.value === 'failed') list = list.filter((f) => f.doc_status !== 'done')
  return list
})

function typeMeta(ext: string) {
  const m: Record<string, { icon: string; bg: string; fg: string }> = {
    pdf: { icon: '#i-doc', bg: 'var(--grape-l)', fg: 'var(--grape-d)' },
    docx: { icon: '#i-doc', bg: 'var(--sky-l)', fg: 'var(--sky)' },
    pptx: { icon: '#i-film', bg: 'var(--berry-l)', fg: 'var(--berry)' },
    epub: { icon: '#i-book', bg: 'var(--orange-l)', fg: 'var(--orange-d)' },
    md: { icon: '#i-code', bg: 'var(--mint-l)', fg: 'var(--mint-d)' },
    txt: { icon: '#i-doc', bg: 'var(--sky-l)', fg: 'var(--sky)' },
    xlsx: { icon: '#i-doc', bg: 'var(--ham-l)', fg: 'var(--ham-d)' },
  }
  return m[ext] || { icon: '#i-doc', bg: 'var(--berry-l)', fg: 'var(--berry)' }
}
function statusLabel(s: string | null) {
  return { done: '已解析', parsing: '解析中', failed: '失败', queued: '排队中' }[s ?? ''] ?? '—'
}
function statusChip(s: string | null) {
  return { done: 'chip-m', parsing: 'chip-g', failed: 'chip-o', queued: 'chip-g' }[s ?? ''] ?? 'chip-g'
}
function statusWidth(s: string | null) {
  return { done: '100%', parsing: '50%', failed: '0%', queued: '10%' }[s ?? ''] ?? '0%'
}
function statusColor(s: string | null) {
  return { done: 'var(--mint)', parsing: 'var(--orange)', failed: 'var(--berry)', queued: 'var(--ham)' }[s ?? ''] ?? 'var(--mint)'
}
function formatSize(n: number) {
  if (n < 1024) return n + ' B'
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB'
  return (n / 1024 / 1024).toFixed(1) + ' MB'
}
function timeAgo(t: string) {
  const d = Date.now() - new Date(t).getTime()
  const day = 86400000
  if (d < day) return '今天'
  if (d < 2 * day) return '昨天'
  if (d < 7 * day) return Math.floor(d / day) + ' 天前'
  return Math.floor(d / (7 * day)) + ' 周前'
}

let seq = 0
let searchTimer: ReturnType<typeof setTimeout> | null = null

async function load() {
  const my = ++seq
  try {
    const res = await filesApi.list({ q: keyword.value.trim() || undefined })
    if (my !== seq) return // 请求竞态守卫：只采纳最后一次
    files.value = res.data.filter((f) => !f.is_dir)
  } catch {
    if (my === seq) err.value = '加载文件列表失败'
  }
}

// 搜索防抖：停顿 350ms 后走后端全库搜索
watch(keyword, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(load, 350)
})

/** 解析失败重试：重新触发解析管道 */
async function retry(f: FileItem) {
  if (!f.doc_id || retrying.value) return
  retrying.value = f.id
  try {
    await documentsApi.reparse(f.doc_id)
    await load()
  } catch {
    err.value = '重试失败'
  } finally {
    retrying.value = ''
  }
}

function triggerUpload() {
  fileInput.value?.click()
}

/* ── 上传等待 chips：每个文件一枚，进度走到 90% 悬停等真实结果，失败可点重试 ── */
interface UploadItem {
  id: number
  name: string
  status: 'idle' | 'running' | 'done' | 'error'
  expectedMs: number
  file?: File
  errorText?: string
}
const uploads = ref<UploadItem[]>([])
let uploadSeq = 0

const ACCEPTED_EXTS = ['pdf', 'docx', 'pptx', 'epub', 'md', 'markdown', 'txt']

/** 按体积粗估解析耗时：进度条走到 90% 的节奏参考 */
function estimateMs(size: number) {
  return Math.min(6000, Math.max(1500, 1200 + size / 1024))
}
function uploadArg(u: UploadItem) {
  if (u.status === 'done') return '解析完成'
  if (u.status === 'error') return u.errorText ?? '没解析出来，点一下重试'
  return '正在解析'
}

/** 初始状态必须是 idle：runUpload 的防重入守卫见到 running 会直接短路（血泪教训） */
async function runUpload(item: UploadItem) {
  if (item.status === 'running' || !item.file) return
  item.status = 'running'
  try {
    await filesApi.upload(item.file)
    item.status = 'done'
    setTimeout(() => {
      uploads.value = uploads.value.filter((u) => u.id !== item.id)
    }, 1600)
  } catch {
    item.errorText = ''
    item.status = 'error'
  }
  await load()
}

function enqueueFiles(list: File[]) {
  for (const f of list) {
    const ext = (f.name.includes('.') ? f.name.split('.').pop()! : '').toLowerCase()
    // reactive 只包状态字段；File 必须 markRaw——被代理的 File 交给 FormData/XHR 时
    // 浏览器读不到内部字节流（Proxy 透传不了内部 slot），请求会永远挂起
    const item = reactive<UploadItem>({
      id: ++uploadSeq,
      name: f.name,
      status: 'idle',
      expectedMs: estimateMs(f.size),
      file: markRaw(f),
    })
    if (!ACCEPTED_EXTS.includes(ext)) {
      item.file = undefined // 格式问题重试无意义
      item.status = 'error'
      item.errorText =
        ext === 'doc'
          ? '.doc 是老版 Word，另存为 .docx 再传'
          : `.${ext || '???'} 还不支持，可传：PDF / Word / PPT / EPUB / MD / TXT`
    }
    uploads.value.push(item)
    if (item.file) runUpload(item)
  }
}

async function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  enqueueFiles(Array.from(input.files || []))
  input.value = ''
}
async function onDrop(e: DragEvent) {
  enqueueFiles(Array.from(e.dataTransfer?.files || []))
}
function onOpen(f: FileItem) {
  if (f.doc_id) router.push({ path: '/reader', query: { doc: f.doc_id } })
}
async function createFolder() {
  if (!folderName.value.trim()) return
  try {
    await filesApi.createFolder(folderName.value.trim())
    folderName.value = ''
    folderModal.value = false
  } catch {
    err.value = '创建失败'
  }
}

onMounted(load)
</script>

<style scoped>
.search-box {
  background: var(--paper); border: 2.5px solid var(--line); border-radius: 999px;
  padding: 7px 16px; box-shadow: var(--pop-sm);
}
.search-box input { border: none; outline: none; font-size: 14px; width: 150px; background: none; color: var(--ink); }

.retry-btn { cursor: pointer; font-family: inherit; }
.retry-btn:disabled { opacity: 0.6; cursor: default; }
.ferr { font-size: 12px; color: var(--berry); margin-top: 6px; font-weight: 650; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.up-chips { display: flex; flex-direction: column; gap: 8px; align-items: flex-start; margin-bottom: 18px; }
.up-chips > * { width: fit-content; max-width: 100%; }

.mask { position: fixed; inset: 0; background: rgba(10, 7, 4, 0.5); z-index: 90; display: flex; align-items: center; justify-content: center; padding: 20px; }
.modal-card { width: min(400px, 100%); padding: 26px 26px 22px; box-shadow: var(--pop-lg); background: var(--paper); border-radius: var(--r-lg); border: 2.5px solid var(--line); }
.modal-title { font-size: 19px; font-weight: 800; margin-bottom: 18px; letter-spacing: -0.4px; }
.field { display: block; margin-bottom: 14px; }
.field span { display: block; font-size: 12.5px; font-weight: 750; color: var(--ink2); margin-bottom: 6px; }
.field input { width: 100%; padding: 10px 12px; font-family: inherit; font-size: 14px; color: var(--ink); background: var(--cream); border: 2.5px solid var(--line); border-radius: 12px; outline: none; }
.field input:focus { border-color: var(--orange); }
.err { color: var(--berry); font-size: 13px; font-weight: 650; margin-bottom: 10px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; }
</style>
