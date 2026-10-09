import { client } from './client'
import type { StatsDashboard, StatsOverview } from '@/types/api'

export const statsApi = {
  overview() {
    return client.get<StatsOverview>('/stats/overview')
  },
  heatmap() {
    return client.get<{ date: string; count: number }[]>('/stats/heatmap')
  },
  dashboard() {
    return client.get<StatsDashboard>('/stats/dashboard')
  },
  claimNewBadges() {
    return client.post<StatsDashboard['achievements']>('/stats/achievements/claim')
  },
}
