import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'
import { tokenStore } from '@/api/client'
import { useExtractStore } from '@/stores/extract'
import { useFocusStore } from '@/stores/focus'
import type { User } from '@/types/api'

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null as User | null,
    ready: false,
  }),
  getters: {
    isLoggedIn: (s) => !!s.user,
  },
  actions: {
    async login(account: string, password: string) {
      const res = await authApi.login({ account, password })
      tokenStore.set(res.data.access_token, res.data.refresh_token)
      await this.fetchMe()
      if (this.user) useFocusStore().restore(this.user.id)
    },
    async register(email: string, username: string, password: string) {
      const res = await authApi.register({ email, username, password })
      tokenStore.set(res.data.access_token, res.data.refresh_token)
      await this.fetchMe()
      if (this.user) useFocusStore().restore(this.user.id)
    },
    async fetchMe() {
      const res = await authApi.me()
      this.user = res.data
      this.ready = true
    },
    /** 启动时恢复登录态；有 token 但失效则清空 */
    async bootstrap() {
      if (!tokenStore.access) {
        this.ready = true
        return
      }
      try {
        await this.fetchMe()
      } catch {
        tokenStore.clear()
        this.user = null
        this.ready = true
      }
    },
    async logout() {
      const rt = tokenStore.refresh
      if (rt) {
        try {
          await authApi.logout(rt)
        } catch {
          /* 登出失败也照常清理本地 */
        }
      }
      tokenStore.clear()
      this.user = null
      useExtractStore().resetSession()
      useFocusStore().forgetLocal()
    },
  },
})
