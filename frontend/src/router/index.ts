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
      path: '/departments',
      name: 'department-list',
      component: () => import('@/views/DepartmentListView.vue'),
      meta: { layout: 'app' },
    },
    {
      path: '/departments/:id',
      name: 'department-detail',
      component: () => import('@/views/DepartmentDetailView.vue'),
      meta: { layout: 'app' },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { layout: 'app' },
    },
    {
      path: '/api-keys',
      name: 'api-keys',
      component: () => import('@/views/ApiKeysView.vue'),
      meta: { layout: 'app' },
    },
    {
      path: '/tags/:tag',
      name: 'tag-nodes',
      component: () => import('@/views/TagNodesView.vue'),
      meta: { layout: 'app' },
    },
    {
      path: '/discover',
      name: 'discover',
      component: () => import('@/views/DiscoverySessionListView.vue'),
      meta: { layout: 'app' },
    },
    {
      path: '/discover/new',
      name: 'discover-new',
      component: () => import('@/views/ServiceDiscoveryView.vue'),
      meta: { layout: 'app' },
    },
    {
      path: '/discover/:id',
      name: 'discover-detail',
      component: () => import('@/views/DiscoverySessionDetailView.vue'),
      meta: { layout: 'app' },
    },
    {
      path: '/skills',
      name: 'skill-list',
      component: () => import('@/views/SkillListView.vue'),
      meta: { layout: 'app' },
    },
    {
      path: '/skills/:id',
      name: 'skill-detail',
      component: () => import('@/views/SkillDetailView.vue'),
      meta: { layout: 'app' },
    },
    {
      path: '/ai-config',
      name: 'ai-config',
      component: () => import('@/views/AiConfigView.vue'),
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
