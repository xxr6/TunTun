import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/layouts/BlankLayout.vue'),
    children: [{ path: '', name: 'login-page', component: () => import('@/views/Login.vue') }],
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/today',
    children: [
      { path: 'today', name: 'today', component: () => import('@/views/Today.vue'), meta: { title: '今日' } },
      // 复习页在主布局子路由里显示（不切独立全屏页），样式照 demo
      { path: 'review', name: 'review', component: () => import('@/views/Review.vue'), meta: { title: '复习' } },
      { path: 'decks', name: 'decks', component: () => import('@/views/Decks.vue'), meta: { title: '卡组' } },
      { path: 'library', name: 'library', component: () => import('@/views/Library.vue'), meta: { title: '内容库' } },
      // 阅读器：主布局一级页（对齐 demo），?doc=<documentId> 直达指定文档
      { path: 'reader', name: 'reader', component: () => import('@/views/Reader.vue'), meta: { title: '阅读器' } },
      { path: 'extract', name: 'extract', component: () => import('@/views/Extract.vue'), meta: { title: 'AI 提炼' } },
      // M3+ 逐页实现，先挂占位
      { path: 'qa', name: 'qa', component: () => import('@/views/Placeholder.vue'), meta: { title: '问答' } },
      { path: 'focus', name: 'focus', component: () => import('@/views/Focus.vue'), meta: { title: '专注' } },
      { path: 'stats', name: 'stats', component: () => import('@/views/Stats.vue'), meta: { title: '统计' } },
      { path: 'me', name: 'me', component: () => import('@/views/PersonalCenter.vue'), meta: { title: '个人中心' } },
      { path: 'jobs', name: 'jobs', component: () => import('@/views/Placeholder.vue'), meta: { title: '任务' } },
      { path: 'settings', name: 'settings', component: () => import('@/views/Placeholder.vue'), meta: { title: '设置' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/today' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const userStore = useUserStore()
  // 用 path 导航：name 导航到「带 path:'' 子路由的父路由」时，子路由不会被激活，
  // 导致 BlankLayout 渲染但 router-view 空（登录页白屏）。path 导航则无此问题。
  if (!to.meta.public && !userStore.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.path === '/login' && userStore.isLoggedIn) {
    return { path: '/today' }
  }
})

export default router
