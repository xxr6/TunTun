import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'

const ACCESS_KEY = 'zhistack.access_token'
const REFRESH_KEY = 'zhistack.refresh_token'

/** 令牌本地存储（M1 用 localStorage，后续可迁 httpOnly cookie） */
export const tokenStore = {
  get access() {
    return localStorage.getItem(ACCESS_KEY)
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY)
  },
  set(access: string, refresh: string) {
    localStorage.setItem(ACCESS_KEY, access)
    localStorage.setItem(REFRESH_KEY, refresh)
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

export const client: AxiosInstance = axios.create({ baseURL: '/api/v1', timeout: 60000 })

client.interceptors.request.use((config) => {
  const token = tokenStore.access
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 单飞刷新：并发 401 共享同一个刷新请求，避免刷新令牌被轮换多次导致旧令牌失效
let refreshPromise: Promise<string> | null = null

async function doRefresh(): Promise<string> {
  const refresh = tokenStore.refresh
  if (!refresh) throw new Error('no refresh token')
  const { data } = await axios.post<{ access_token: string; refresh_token: string }>(
    '/api/v1/auth/refresh',
    { refresh_token: refresh },
  )
  tokenStore.set(data.access_token, data.refresh_token)
  return data.access_token
}

client.interceptors.response.use(
  (res) => {
    const method = res.config.method?.toLowerCase()
    const path = res.config.url?.split('?')[0] ?? ''
    const changesAchievementProgress = method === 'post' && (
      ['/focus/sessions', '/review/answer', '/checkin', '/cards', '/files', '/extract/from-file', '/ai/cards/from-selection'].includes(path)
      || /^\/extract\/notes\/[^/]+\/split-candidates$/.test(path)
    )
    if (changesAchievementProgress) window.dispatchEvent(new Event('zhistack:achievement-progress'))
    return res
  },
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retried?: boolean }
    if (error.response?.status === 401 && original && !original._retried && tokenStore.refresh) {
      original._retried = true
      try {
        if (!refreshPromise) {
          refreshPromise = doRefresh().finally(() => {
            refreshPromise = null
          })
        }
        const token = await refreshPromise
        original.headers.Authorization = `Bearer ${token}`
        return client(original)
      } catch {
        tokenStore.clear()
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }
    return Promise.reject(error)
  },
)
