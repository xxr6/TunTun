<template>
  <div>
    <!-- 顶栏：标题 + logo · 统计 | 搜索 + 新建 -->
    <div class="lib-top rise">
      <div class="lib-headline">
        <div class="lib-title-row">
          <div class="h-page">内容库</div>
          <img :src="logoUrl" class="lib-logo" alt="" aria-hidden="true" />
        </div>
        <div class="h-sub">{{ fileCount }} 份资料 <span class="lib-dot" aria-hidden="true"></span> {{ folderCount }} 个文件夹 <span class="lib-dot" aria-hidden="true"></span> 已解析 {{ doneCount }} 份</div>
      </div>
      <div class="lib-actions">
        <div class="search-box">
          <svg class="icon" style="width:17px;height:17px;color:var(--ink3)"><use href="#i-search" /></svg>
          <input v-model="keyword" placeholder="搜索文件名、内容或标签..." aria-label="搜索文件" />
        </div>
        <button class="btn btn-primary" @click="openCreateFolder">
          <svg class="icon"><use href="#i-plus" /></svg>新建文件夹
        </button>
      </div>
    </div>

    <nav class="lib-breadcrumb" aria-label="文件夹路径">
      <button :class="{ on: !folderTrail.length && !keyword.trim() }" @click="goToFolder(-1)">全部资料</button>
      <template v-for="(folder, index) in folderTrail" :key="folder.id">
        <span aria-hidden="true">/</span>
        <button :class="{ on: index === folderTrail.length - 1 && !keyword.trim() }" @click="goToFolder(index)">{{ folder.name }}</button>
      </template>
      <span v-if="keyword.trim()" class="lib-search-scope">全库搜索结果</span>
    </nav>

    <!-- 拖拽上传：云图标 + 文案 | 右侧 logo -->
    <div class="dropzone2 rise" @click="triggerUpload" @dragover.prevent @drop.prevent="onDrop">
      <div class="dz-body">
        <div class="dz-ic2"><svg class="icon"><use href="#i-cloud" /></svg></div>
        <div class="dz-t1">拖拽文件到此处，或点击上传{{ currentFolderName ? `到「${currentFolderName}」` : '' }}</div>
        <div class="dz-t2">支持 PDF · Word · PPT · Excel · Markdown · TXT · 其他常见格式</div>
      </div>
      <img :src="logoUrl" class="dz-logo" alt="" aria-hidden="true" />
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

    <!-- 筛选：带图标 + 计数 -->
    <div class="lib-filters rise">
      <button class="fchip f-o" :class="{ on: filter === 'all' }" @click="filter = 'all'">
        <svg class="icon"><use href="#i-folder" /></svg>全部<b>{{ files.length }}</b>
      </button>
      <button class="fchip f-m" :class="{ on: filter === 'done' }" @click="filter = 'done'">
        <svg class="icon"><use href="#i-check" /></svg>已解析<b>{{ doneCount }}</b>
      </button>
      <button class="fchip f-p" :class="{ on: filter === 'failed' }" @click="filter = 'failed'">
        <svg class="icon"><use href="#i-clock" /></svg>还没处理<b>{{ pendingCount }}</b>
      </button>
    </div>

    <!-- 文件卡片网格 -->
    <div class="lib-grid">
      <div v-for="f in filteredFiles" :key="f.id" class="fcard2 rise" :class="{ 'is-folder': f.is_dir, highlighted: f.id === highlightedFileId }" @click="onOpen(f)">
        <div class="fc-head">
          <div class="fi2" :style="{ background: f.is_dir ? 'var(--orange-l)' : typeMeta(f.ext).bg, color: f.is_dir ? 'var(--orange-d)' : typeMeta(f.ext).fg }">
            <svg class="icon"><use :href="f.is_dir ? '#i-folder' : typeMeta(f.ext).icon" /></svg>
          </div>
          <button v-if="!f.is_dir" class="fc-more" :aria-label="`移动 ${f.name} 到文件夹`" title="移动到文件夹" @click.stop="openMove(f)">
            <svg class="icon"><use href="#i-folder" /></svg>
          </button>
          <svg v-else class="icon fc-folder-arrow"><use href="#i-chev" /></svg>
        </div>
        <div class="fc-name" :title="f.name">{{ f.name }}</div>
        <div class="fc-meta">
          <span><svg class="icon"><use href="#i-calendar" /></svg>{{ formatTime(f.created_at) }}</span>
          <span v-if="!f.is_dir"><svg class="icon"><use href="#i-doc" /></svg>{{ formatSize(f.size) }}</span>
          <span v-else>文件夹 · 点击打开</span>
        </div>
        <div v-if="!f.is_dir" class="fc-foot">
          <span class="chip" :class="statusChip(f.doc_status)">
            <svg v-if="f.doc_status === 'done'" class="icon fc-ok"><use href="#i-check" /></svg>
            {{ statusLabel(f.doc_status) }}
          </span>
          <button v-if="f.doc_status === 'failed'" class="chip chip-o retry-btn"
                  :disabled="retrying === f.id" @click.stop="retry(f)">
            {{ retrying === f.id ? '重试中…' : '重试' }}
          </button>
        </div>
        <div v-if="f.doc_status === 'failed' && f.doc_error" class="ferr" :title="f.doc_error">{{ f.doc_error }}</div>
        <div v-if="f.doc_status === 'parsing' || f.doc_status === 'queued'" class="fbar"><i :style="{ width: statusWidth(f.doc_status), background: statusColor(f.doc_status) }"></i></div>
        <div class="fc-deco" aria-hidden="true"><img :src="logoUrl" alt="" /></div>
      </div>
        <div v-if="!filteredFiles.length" class="lib-empty rise">
        <img :src="logoUrl" class="lib-empty-logo" alt="" />
        <div class="lib-empty-t">{{ keyword.trim() ? '没有找到匹配的资料' : filter !== 'all' ? '这个筛选下还没有文件' : currentFolderName ? '文件夹还是空的，把资料传进来吧' : '还没有资料，把文件拖进来试试' }}</div>
      </div>
    </div>

    <!-- 新建文件夹弹窗 -->
    <div v-if="folderModal" class="mask" @click.self="folderModal = false">
      <div class="card modal-card">
        <h3 class="modal-title">新建文件夹</h3>
        <p class="modal-context">创建在：{{ currentFolderName || '全部资料' }}</p>
        <label class="field"><span>名称</span><input v-model="folderName" maxlength="255" placeholder="例如：考研资料" @keyup.enter="createFolder" /></label>
        <p class="err" v-if="folderError">{{ folderError }}</p>
        <div class="modal-actions">
          <button class="btn" @click="folderModal = false">取消</button>
          <button class="btn btn-primary" :disabled="savingFolder || !folderName.trim()" @click="createFolder">{{ savingFolder ? '创建中…' : '创建并进入' }}</button>
        </div>
      </div>
    </div>

    <div v-if="movingFile" class="mask" @click.self="movingFile = null">
      <div class="card modal-card">
        <h3 class="modal-title">移动到文件夹</h3>
        <p class="modal-context">{{ movingFile.name }}</p>
        <label class="field"><span>目标位置</span>
          <select v-model="moveTargetId">
            <option :value="null">全部资料（根目录）</option>
            <option v-for="folder in folderOptions" :key="folder.id" :value="folder.id">{{ folderPath(folder) }}</option>
          </select>
        </label>
        <p class="err" v-if="moveError">{{ moveError }}</p>
        <div class="modal-actions">
          <button class="btn" @click="movingFile = null">取消</button>
          <button class="btn btn-primary" :disabled="moving || moveTargetId === movingFile.parent_id" @click="moveFile">{{ moving ? '移动中…' : '移动' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, markRaw, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { documentsApi, filesApi } from '@/api/files'
import CallChip from '@/components/common/CallChip.vue'
import type { FileItem } from '@/types/api'
import logoUrl from '@/assets/logo.png'

const router = useRouter()
const route = useRoute()
const files = ref<FileItem[]>([])
const highlightedFileId = ref<string | null>(null)
const folderTrail = ref<{ id: string; name: string }[]>([])
const keyword = ref('')
const filter = ref<'all' | 'done' | 'failed'>('all')
const fileInput = ref<HTMLInputElement>()
const folderModal = ref(false)
const folderName = ref('')
const folderError = ref('')
const savingFolder = ref(false)
const movingFile = ref<FileItem | null>(null)
const moveTargetId = ref<string | null>(null)
const moveError = ref('')
const moving = ref(false)
const folderOptions = ref<FileItem[]>([])
const err = ref('')
const retrying = ref('')

const currentFolderId = computed(() => folderTrail.value.at(-1)?.id ?? null)
const currentFolderName = computed(() => folderTrail.value.at(-1)?.name ?? '')
const fileCount = computed(() => files.value.filter((f) => !f.is_dir).length)
const folderCount = computed(() => files.value.filter((f) => f.is_dir).length)
const doneCount = computed(() => files.value.filter((f) => !f.is_dir && f.doc_status === 'done').length)
const pendingCount = computed(() => files.value.filter((f) => !f.is_dir && f.doc_status !== 'done').length)

// 搜索走后端（可命中解析正文、跨目录），这里只做状态筛选
const filteredFiles = computed(() => {
  let list = files.value
  if (filter.value === 'done') list = list.filter((f) => !f.is_dir && f.doc_status === 'done')
  if (filter.value === 'failed') list = list.filter((f) => !f.is_dir && f.doc_status !== 'done')
  return list
})

/** 类型外观：实色块 + 对比安全的图标色（亮黄底用深墨，其余白图标） */
function typeMeta(ext: string) {
  const white = '#ffffff'
  const ink = 'var(--onfill)'
  const m: Record<string, { icon: string; bg: string; fg: string }> = {
    pdf: { icon: '#i-doc', bg: 'var(--grape)', fg: white },
    docx: { icon: '#i-doc', bg: 'var(--sky)', fg: white },
    pptx: { icon: '#i-film', bg: 'var(--berry)', fg: white },
    epub: { icon: '#i-book', bg: 'var(--orange)', fg: white },
    md: { icon: '#i-code', bg: 'var(--mint)', fg: white },
    txt: { icon: '#i-doc', bg: 'var(--ham)', fg: ink },
    xlsx: { icon: '#i-doc', bg: 'var(--ham)', fg: ink },
  }
  return m[ext] || { icon: '#i-doc', bg: 'var(--berry)', fg: white }
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
/** 绝对时间：YYYY-MM-DD HH:mm（对齐效果图 meta 行） */
function formatTime(t: string) {
  const d = new Date(t)
  if (Number.isNaN(d.getTime())) return '—'
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

let seq = 0
let searchTimer: ReturnType<typeof setTimeout> | null = null

async function load() {
  const my = ++seq
  try {
    const res = await filesApi.list({
      parentId: keyword.value.trim() ? undefined : currentFolderId.value ?? undefined,
      q: keyword.value.trim() || undefined,
    })
    if (my !== seq) return // 请求竞态守卫：只采纳最后一次
    files.value = res.data
  } catch {
    if (my === seq) err.value = '加载文件列表失败'
  }
}

async function loadLinkedFile() {
  const fileId = typeof route.query.file === 'string' ? route.query.file : null
  if (fileId) {
    try {
      const allFiles = (await filesApi.list({ all: true })).data
      const target = allFiles.find((file) => file.id === fileId && !file.is_dir)
      if (target) {
        highlightedFileId.value = fileId
        const folders = new Map(allFiles.filter((file) => file.is_dir).map((file) => [file.id, file]))
        const trail: { id: string; name: string }[] = []
        const visited = new Set<string>()
        let parentId = target.parent_id
        while (parentId && !visited.has(parentId)) {
          visited.add(parentId)
          const folder = folders.get(parentId)
          if (!folder) break
          trail.unshift({ id: folder.id, name: folder.name })
          parentId = folder.parent_id
        }
        folderTrail.value = trail
      }
    } catch { /* 正常加载根目录供用户继续操作 */ }
  }
  await load()
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

function openFolder(folder: FileItem) {
  folderTrail.value.push({ id: folder.id, name: folder.name })
  keyword.value = ''
  filter.value = 'all'
  load()
}

function goToFolder(index: number) {
  folderTrail.value = folderTrail.value.slice(0, index + 1)
  keyword.value = ''
  filter.value = 'all'
  load()
}

/* ── 上传等待 chips：每个文件一枚，进度走到 90% 悬停等真实结果，失败可点重试 ── */
interface UploadItem {
  id: number
  name: string
  status: 'idle' | 'running' | 'done' | 'error'
  expectedMs: number
  file?: File
  parentId?: string
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
    await filesApi.upload(item.file, item.parentId)
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
      parentId: currentFolderId.value ?? undefined,
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
  if (f.is_dir) return openFolder(f)
  if (f.doc_id) router.push({ path: '/reader', query: { doc: f.doc_id } })
}

function openCreateFolder() {
  folderName.value = ''
  folderError.value = ''
  folderModal.value = true
}

async function createFolder() {
  const name = folderName.value.trim()
  if (!name || savingFolder.value) return
  savingFolder.value = true
  folderError.value = ''
  try {
    const res = await filesApi.createFolder(name, currentFolderId.value ?? undefined)
    folderName.value = ''
    folderModal.value = false
    openFolder(res.data)
  } catch (error: any) {
    folderError.value = error?.response?.data?.message || '创建失败，请重试'
  } finally {
    savingFolder.value = false
  }
}

async function openMove(file: FileItem) {
  movingFile.value = file
  moveTargetId.value = file.parent_id
  moveError.value = ''
  try {
    folderOptions.value = (await filesApi.folders()).data
  } catch {
    moveError.value = '加载文件夹失败，请重试'
  }
}

function folderPath(folder: FileItem) {
  const byId = new Map(folderOptions.value.map((item) => [item.id, item]))
  const names = [folder.name]
  let parentId = folder.parent_id
  while (parentId && names.length < 20) {
    const parent = byId.get(parentId)
    if (!parent) break
    names.unshift(parent.name)
    parentId = parent.parent_id
  }
  return names.join(' / ')
}

async function moveFile() {
  const file = movingFile.value
  if (!file || moving.value || moveTargetId.value === file.parent_id) return
  moving.value = true
  moveError.value = ''
  try {
    await filesApi.move(file.id, moveTargetId.value)
    movingFile.value = null
    await load()
  } catch (error: any) {
    moveError.value = error?.response?.data?.message || '移动失败，请重试'
  } finally {
    moving.value = false
  }
}

onMounted(loadLinkedFile)
</script>

<style scoped>
/* ── 顶栏 ── */
.lib-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; flex-wrap: wrap; margin-bottom: 20px; }
.lib-title-row { display: flex; align-items: center; gap: 12px; }
.lib-logo { width: 44px; height: 44px; transform: rotate(-8deg); filter: drop-shadow(2px 2px 0 var(--line)); }
.lib-dot { display: inline-block; width: 5px; height: 5px; border-radius: 99px; background: var(--ink3); vertical-align: 3px; margin: 0 7px; }
.lib-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.search-box {
  background: var(--paper); border: 2.5px solid var(--line); border-radius: 999px;
  padding: 8px 16px; box-shadow: var(--pop-sm); display: flex; align-items: center; gap: 8px;
}
.search-box input { border: none; outline: none; font-size: 13.5px; width: 200px; background: none; color: var(--ink); }
.search-box input::placeholder { color: var(--ink3); }
.lib-breadcrumb { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin: -5px 0 17px; color: var(--ink3); font-size: 13px; }
.lib-breadcrumb button { border: 0; background: none; color: var(--ink2); font: inherit; font-weight: 700; cursor: pointer; padding: 3px 5px; border-radius: 6px; }
.lib-breadcrumb button:hover, .lib-breadcrumb button.on { color: var(--orange-d); background: var(--orange-l); }
.lib-search-scope { color: var(--orange-d); font-weight: 700; }

/* ── 上传区：大圆角 + 右侧 logo ── */
.dropzone2 {
  position: relative; overflow: hidden;
  border: 2.5px dashed var(--hairline); border-radius: var(--r-xl);
  background: var(--cream); padding: 30px 34px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.35s var(--ease);
  margin-bottom: 22px;
}
.dropzone2:hover { border-color: var(--orange); background: var(--orange-l); }
.dropzone2:hover .dz-ic2 { transform: translateY(-5px) rotate(-8deg); }
.dz-body { text-align: center; }
.dz-ic2 {
  width: 54px; height: 54px; margin: 0 auto 12px; border-radius: 50%;
  background: var(--ham-l); border: 2.5px solid var(--line); color: var(--ham-d);
  display: flex; align-items: center; justify-content: center;
  transition: transform 0.45s var(--ease-out-quart);
}
.dz-ic2 .icon { width: 26px; height: 26px; }
.dz-t1 { font-size: 15.5px; font-weight: 800; }
.dz-t2 { font-size: 12.5px; color: var(--ink3); margin-top: 6px; font-weight: 600; }
.dz-logo {
  position: absolute; right: 4%; bottom: 2px; width: 100px; height: 100px;
  transform: rotate(8deg); opacity: 0.95; pointer-events: none;
  filter: drop-shadow(3px 3px 0 rgba(61, 43, 28, 0.14));
}

/* ── 筛选 chips ── */
.lib-filters { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 18px; }
.fchip {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 8px 16px; border-radius: 999px; font-family: inherit;
  font-size: 13.5px; font-weight: 750; color: var(--ink2);
  background: var(--paper); border: 2.5px solid var(--line); box-shadow: var(--pop-sm);
  cursor: pointer; transition: all 0.22s var(--ease-out-quart);
}
.fchip .icon { width: 16px; height: 16px; }
.fchip b { font-size: 12.5px; font-weight: 800; opacity: 0.75; }
.fchip.f-o .icon { color: var(--orange-d); }
.fchip.f-m .icon { color: var(--mint-d); }
.fchip.f-p .icon { color: var(--grape-d); }
.fchip:hover { transform: translateY(-2px); }
.fchip.on { color: var(--onfill); }
.fchip.f-o.on { background: var(--orange); }
.fchip.f-m.on { background: var(--mint); }
.fchip.f-p.on { background: var(--grape); }
.fchip.on .icon { color: var(--onfill); }
.fchip.on b { opacity: 0.85; }

/* ── 文件卡片网格 ── */
.lib-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(272px, 1fr)); gap: 16px; }
.fcard2 {
  position: relative; overflow: hidden;
  background: var(--paper); border: 2.5px solid var(--line); border-radius: var(--r-md);
  padding: 15px 16px 14px; box-shadow: var(--pop-sm); cursor: pointer;
  transition: transform 0.34s var(--ease-out-quart), box-shadow 0.34s var(--ease-out-quart);
}
.fcard2:hover { transform: translate(-3px, -4px) rotate(-0.8deg); box-shadow: var(--pop); }
.fcard2.is-folder { background: var(--cream); border-color: var(--orange); }
.fcard2.highlighted { border-color: var(--orange); box-shadow: 0 0 0 3px var(--orange-l), var(--pop); }
.fc-folder-arrow { width: 18px; height: 18px; color: var(--orange-d); margin: 5px; }
.fc-head { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 11px; }
.fi2 {
  width: 44px; height: 44px; border-radius: 14px; flex: none;
  display: flex; align-items: center; justify-content: center;
  border: 2.5px solid var(--line); box-shadow: var(--pop-sm);
}
.fi2 .icon { width: 21px; height: 21px; stroke-width: 2.1; }
.fc-more {
  width: 28px; height: 28px; border-radius: 10px; border: none; background: none;
  color: var(--ink3); display: flex; align-items: center; justify-content: center; cursor: pointer;
  transition: all 0.2s var(--ease-out-quart);
}
.fc-more .icon { width: 18px; height: 18px; }
.fc-more:hover { background: var(--warm); color: var(--ink); }
.fc-name {
  font-size: 14.5px; font-weight: 800; line-height: 1.45; letter-spacing: -0.1px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  min-height: 42px; word-break: break-all; padding-right: 4px;
}
.fc-meta { display: flex; align-items: center; gap: 14px; margin-top: 8px; flex-wrap: wrap; }
.fc-meta span { display: inline-flex; align-items: center; gap: 5px; font-size: 12px; color: var(--ink3); font-weight: 600; font-variant-numeric: tabular-nums; }
.fc-meta .icon { width: 13px; height: 13px; stroke-width: 2; }
.fc-foot { display: flex; align-items: center; gap: 8px; margin-top: 11px; flex-wrap: wrap; }
.fc-ok { width: 13px !important; height: 13px !important; stroke-width: 3; }
.retry-btn { cursor: pointer; font-family: inherit; }
.retry-btn:disabled { opacity: 0.6; cursor: default; }
.ferr { font-size: 12px; color: var(--berry); margin-top: 7px; font-weight: 650; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fbar { height: 9px; border-radius: 99px; background: var(--warm); border: 2px solid var(--line); margin-top: 11px; overflow: hidden; }
.fbar i { display: block; height: 100%; transition: width 1s var(--ease-out); }

/* 卡片右下角 logo 装饰：奶油色弧形地面 + 小 logo */
.fc-deco { position: absolute; right: 10px; bottom: 0; width: 64px; height: 38px; pointer-events: none; }
.fc-deco::before {
  content: ''; position: absolute; right: -6px; bottom: -16px; width: 74px; height: 42px;
  background: var(--ham-l); border: 2.5px solid var(--hairline); border-radius: 50% 50% 0 0;
}
.fc-deco img {
  position: absolute; right: 4px; bottom: 5px; width: 32px; height: 32px;
  transform: rotate(-6deg); filter: drop-shadow(1.5px 1.5px 0 rgba(61, 43, 28, 0.16));
}

/* 空态 */
.lib-empty { grid-column: 1 / -1; text-align: center; padding: 34px 16px 30px; background: var(--paper); border: 2.5px dashed var(--hairline); border-radius: var(--r-lg); }
.lib-empty-logo { width: 74px; height: 74px; opacity: 0.9; }
.lib-empty-t { font-size: 13.5px; color: var(--ink2); font-weight: 650; margin-top: 8px; }

.up-chips { display: flex; flex-direction: column; gap: 8px; align-items: flex-start; margin-bottom: 18px; }
.up-chips > * { width: fit-content; max-width: 100%; }

.mask { position: fixed; inset: 0; background: rgba(10, 7, 4, 0.5); z-index: 90; display: flex; align-items: center; justify-content: center; padding: 20px; }
.modal-card { width: min(400px, 100%); padding: 26px 26px 22px; box-shadow: var(--pop-lg); background: var(--paper); border-radius: var(--r-lg); border: 2.5px solid var(--line); }
.modal-title { font-size: 19px; font-weight: 800; margin-bottom: 18px; letter-spacing: -0.4px; }
.field { display: block; margin-bottom: 14px; }
.field span { display: block; font-size: 12.5px; font-weight: 750; color: var(--ink2); margin-bottom: 6px; }
.field input { width: 100%; padding: 10px 12px; font-family: inherit; font-size: 14px; color: var(--ink); background: var(--cream); border: 2.5px solid var(--line); border-radius: 12px; outline: none; }
.field input:focus { border-color: var(--orange); }
.field select { width: 100%; padding: 10px 12px; font: inherit; font-size: 14px; color: var(--ink); background: var(--cream); border: 2.5px solid var(--line); border-radius: 12px; outline: none; }
.field select:focus { border-color: var(--orange); }
.modal-context { color: var(--ink2); font-size: 13px; margin: -10px 0 16px; overflow-wrap: anywhere; }
.err { color: var(--berry); font-size: 13px; font-weight: 650; margin-bottom: 10px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; }

/* ── 屏幕自适应 ── */
@media (max-width: 860px) {
  .dz-logo { display: none; }
  .dropzone2 { padding: 26px 20px; }
  .search-box input { width: min(46vw, 200px); }
}
@media (max-width: 560px) {
  .lib-top { flex-direction: column; }
  .lib-actions { width: 100%; }
  .search-box { flex: 1; }
  .search-box input { width: 100%; flex: 1; min-width: 0; }
  .lib-grid { grid-template-columns: 1fr; }
  .lib-logo { width: 36px; height: 36px; }
}
</style>
