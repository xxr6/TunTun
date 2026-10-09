import type { StatsDashboard } from '@/types/api'

export type Badge = StatsDashboard['achievements'][number]

const badgeFiles = import.meta.glob('../assets/badges/*.webp', { eager: true, query: '?url', import: 'default' }) as Record<string, string>

export const badgeArt: Record<string, string> = Object.fromEntries([
  ['初火', 'first-flame'], ['不灭', 'undying'], ['百日炉火', 'hundred-day-fire'], ['满月', 'full-moon'],
  ['百卡仓', 'hundred-cards'], ['积少成多', 'little-by-little'], ['千卡仓', 'thousand-cards'],
  ['一日十卡', 'ten-cards-day'], ['万卡仓', 'five-thousand-cards'], ['书山有路', 'road-of-books'],
  ['小憩', 'little-rest'], ['沉浸', 'immersion'], ['心流', 'flow'], ['百炼', 'hundred-hours'],
  ['番茄初心', 'tomato-beginner'], ['番茄大师', 'tomato-master'],
  ['初试啼声', 'first-note'], ['AI 拆解 100', 'ai-hundred'], ['十卷笔记', 'ten-notes'], ['AI 拆解 500', 'ai-five-hundred'],
  ['学而时习', 'practice-review'], ['博览群书', 'many-books'],
].map(([name, slug]) => [name, badgeFiles[`../assets/badges/${slug}.webp`]]))

badgeArt['初来乍到'] = new URL('../assets/badges/first-checkin.svg', import.meta.url).href
badgeArt['七日之约'] = new URL('../assets/badges/seven-day-promise.svg', import.meta.url).href
badgeArt['月满勤'] = new URL('../assets/badges/full-month-checkin.svg', import.meta.url).href
badgeArt['百日常客'] = new URL('../assets/badges/hundred-day-visitor.svg', import.meta.url).href
