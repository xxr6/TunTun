import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { useUserStore } from './stores/user'
import { useFocusStore } from './stores/focus'

import 'uno.css'
import './styles/index.css'

async function start() {
  const app = createApp(App)

  app.use(createPinia())

  // 先恢复登录态，再装 router。关键：vue-router 的首次导航在 `app.use(router)` 时
  // 就异步触发（不是 mount 时），若顺序颠倒，守卫会在 user 恢复前就误判「未登录」，
  // 刷新页面时被踢回登录页。
  const userStore = useUserStore()
  await userStore.bootstrap()
  if (userStore.user) useFocusStore().restore(userStore.user.id)

  app.use(router)
  app.mount('#app')
}

start()
