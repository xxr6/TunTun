import { client } from './client'
import type { CheckinStatus } from '@/types/api'

export const checkinApi = {
  status() {
    return client.get<CheckinStatus>('/checkin')
  },
  checkin() {
    return client.post<CheckinStatus>('/checkin')
  },
}
