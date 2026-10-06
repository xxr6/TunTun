import { client } from './client'
import type { PlanTask } from '@/types/api'

export const plansApi = {
  list(day?: string) {
    return client.get<PlanTask[]>('/plans', { params: { day } })
  },
  create(title: string, day?: string) {
    return client.post<PlanTask>('/plans', { title, day })
  },
  update(id: string, payload: { title?: string; done?: boolean }) {
    return client.patch<PlanTask>(`/plans/${id}`, payload)
  },
  remove(id: string) {
    return client.delete(`/plans/${id}`)
  },
}
