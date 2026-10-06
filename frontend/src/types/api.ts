/** 基础 API 类型（M1 手写，后续用 openapi-typescript 生成覆盖 api.d.ts） */

export interface User {
  id: string
  email: string
  username: string
  is_active: boolean
  is_superuser: boolean
  timezone: string
  settings: Record<string, unknown>
  created_at: string
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
}

/** 统一错误体：后端返回 {code, message, detail} */
export interface ApiErrorBody {
  code: string
  message: string
  detail?: string | null
}

/* ── 卡组 ── */
export interface Deck {
  id: string
  name: string
  parent_id: string | null
  description: string
  config: Record<string, unknown>
  position: number
  card_count: number
  created_at: string
}

/* ── 卡片 ── */
export interface Card {
  id: string
  deck_id: string
  card_type: 'basic' | 'cloze' | 'quote' | 'image'
  front: string
  back: string
  hint: string | null
  extra: Record<string, unknown>
  source_file_id: string | null
  source_locator: Record<string, unknown> | null
  tags: string[]
  state: string
  due: string
  created_at: string
}

export interface CardList {
  items: Card[]
  total: number
}

/* ── 复习 ── */
export interface ReviewCard {
  card_id: string
  deck_id: string
  deck_name: string
  card_type: string
  front: string
  back: string
  hint: string | null
  tags: string[]
  state: string
  reps: number
  due: string
}

export interface ReviewQueue {
  items: ReviewCard[]
  remaining_today: number
}

export interface ReviewAnswerOut {
  card_id: string
  state: string
  due: string
  stability: number | null
  difficulty: number | null
  scheduled_days: number
  remaining_today: number
}

export interface ForecastDay {
  date: string
  count: number
}

/* ── 文件 / 文档 ── */
export interface FileItem {
  id: string
  parent_id: string | null
  name: string
  is_dir: boolean
  size: number
  mime_type: string
  ext: string
  created_at: string
  doc_id: string | null
  doc_status: string | null
  doc_error: string | null
  page_count: number | null
}

export interface DocumentContent {
  document_id: string
  file_id: string
  title: string
  page_count: number | null
  text: string
}

/* ── AI 划词成卡 ── */
export interface GeneratedCard {
  card_type: string
  front: string
  back: string
  hint: string | null
  confidence: number
}

export interface CardSelectionOut {
  cards: GeneratedCard[]
  fallback: boolean
}

/* ── AI 提炼 ── */
export interface NoteCandidate {
  id: string
  card_type: string
  front: string
  back: string
  confidence: number
  card_id: string | null
}

export interface Note {
  id: string
  title: string
  content_md: string
  source_file_id: string | null
  source_type: string
  status: string
  created_at: string
}

export interface NoteDetail extends Note {
  candidates: NoteCandidate[]
}

/* ── 专注 / 统计 ── */
export interface FocusSession {
  id: string
  mode: string
  started_at: string
  ended_at: string
  duration_seconds: number
  completed: boolean
  /** 「这一轮啃什么」的卡组快照（可选） */
  deck_id: string | null
  deck_name: string
}

export interface FocusSummary {
  today_seconds: number
  week_seconds: number
  month_seconds: number
  today_count: number
}

export interface StatsOverview {
  total_cards: number
  total_decks: number
  total_reviews: number
  today_reviews: number
  focus_seconds: number
}

/* ── 每日签到 ── */
export interface CheckinStatus {
  checked: boolean
  streak: number
  total_days: number
  month_days: number
  new_achievements: string[]
}

/* ── 今日计划 ── */
export interface PlanTask {
  id: string
  day: string
  title: string
  done: boolean
  created_at: string
}

/* ── 统计页 dashboard ── */
export interface FocusBlock {
  sec: number
  goal: number
  pct: number
  prev_pct: number | null
}
export interface StatsDashboard {
  focus: {
    today: FocusBlock
    week: FocusBlock
    month: FocusBlock
    dist_today: Record<string, number>
    dist_week: Record<string, number>
    dist_month: Record<string, number>
  }
  metrics: {
    total_reviews: number
    accuracy_30d: number
    cards_total: number
    ai_calls_month: number
  }
  avg_stability: number | null
  deck_health: { name: string; pct: number }[]
  achievements: {
    group: string
    name: string
    desc: string
    icon: string
    progress: number
    target: number
    unlocked: boolean
    rarity: '铜' | '银' | '金' | '钻'
  }[]
}





