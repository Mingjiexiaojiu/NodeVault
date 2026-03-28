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
      path: '/categories',
      name: 'categories',
      component: () => import('@/views/CategoryManageView.vue'),
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
    {
      path: '/credentials',
      name: 'credentials',
      component: () => import('@/views/CredentialListView.vue'),
      meta: { layout: 'app' },
    },
    // Admin routes
    {
      path: '/admin',
      redirect: '/admin/analytics',
      meta: { requireSuperAdmin: true },
      component: () => import('@/layouts/AdminLayout.vue'),
      children: [
        {
          path: 'users',
          name: 'admin-users',
          component: () => import('@/views/admin/UserManageView.vue'),
          meta: { requireSuperAdmin: true },
        },
        {
          path: 'nodes',
          name: 'admin-nodes',
          component: () => import('@/views/admin/GlobalNodesView.vue'),
          meta: { requireSuperAdmin: true },
        },
        {
          path: 'categories',
          name: 'admin-categories',
          component: () => import('@/views/CategoryManageView.vue'),
          meta: { requireSuperAdmin: true },
        },
        {
          path: 'analytics',
          name: 'admin-analytics',
          component: () => import('@/views/admin/AdminAnalyticsView.vue'),
          meta: { requireSuperAdmin: true },
        },
        {
          path: 'namespaces',
          name: 'admin-namespaces',
          component: () => import('@/views/admin/NamespaceManageView.vue'),
          meta: { requireSuperAdmin: true },
        },
        {
          path: 'applications',
          name: 'admin-applications',
          component: () => import('@/views/admin/ApplicationsView.vue'),
          meta: { requireSuperAdmin: true },
        },
        {
          path: 'settings',
          name: 'admin-settings',
          component: () => import('@/views/admin/AdminSettingsView.vue'),
          meta: { requireSuperAdmin: true },
        },
      ],
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
    // 超管登录后跳管理控制台，普通用户跳 dashboard
    return auth.user?.role === 0 ? { name: 'admin-analytics' } : { name: 'dashboard' }
  }

  // 超管访问非 admin 的受保护页面，重定向到管理控制台
  if (auth.token && auth.user?.role === 0 && !to.meta.requireSuperAdmin) {
    return { name: 'admin-analytics' }
  }

  // Superadmin guard: /admin/* routes require role === 0
  if (to.meta.requireSuperAdmin && auth.user?.role !== 0) {
    return { name: 'dashboard' }
  }
})

export default router
