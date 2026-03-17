import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { layout: 'app' },
    },
    {
      path: '/nodes',
      name: 'node-list',
      component: () => import('@/views/NodeListView.vue'),
      meta: { layout: 'app' },
    },
    {
      path: '/nodes/new',
      name: 'node-create',
      component: () => import('@/views/NodeCreateView.vue'),
      meta: { layout: 'app' },
    },
    {
      path: '/nodes/:id',
      name: 'node-detail',
      component: () => import('@/views/NodeDetailView.vue'),
      meta: { layout: 'app' },
    },
    {
      path: '/nodes/:id/invoke',
      name: 'node-invoke',
      component: () => import('@/views/NodeInvokeView.vue'),
      meta: { layout: 'app' },
    },
    {
      path: '/nodes/:id/stats',
      name: 'node-stats',
      component: () => import('@/views/NodeStatsView.vue'),
      meta: { layout: 'app' },
    },
    {
      path: '/nodes/:id/edit',
      name: 'node-edit',
      component: () => import('@/views/NodeEditView.vue'),
      meta: { layout: 'app' },
    },
    {
      path: '/search',
      name: 'search',
      component: () => import('@/views/SearchView.vue'),
      meta: { layout: 'app' },
    },
    {
      path: '/tags/:tag',
      name: 'tag-nodes',
      component: () => import('@/views/TagNodesView.vue'),
      meta: { layout: 'app' },
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (!auth.user && auth.token) {
    await auth.initFromStorage()
  }

  if (!to.meta.public && !auth.token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.public && auth.token) {
    return { name: 'dashboard' }
  }
})

export default router
