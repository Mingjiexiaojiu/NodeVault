<template>
  <div class="min-h-screen flex flex-col" style="background: #f5f6fa">

    <!-- 顶部导航栏 -->
    <header class="bg-white shrink-0" style="border-bottom: 1px solid #eaecf0">
      <div class="max-w-screen-xl mx-auto px-8 h-14 grid grid-cols-3 items-center">

        <!-- 左：Logo -->
        <RouterLink to="/" class="flex items-center gap-2.5 shrink-0">
          <div class="w-7 h-7 rounded-lg flex items-center justify-center" style="background: linear-gradient(135deg, #6366f1, #8b5cf6)">
            <img src="/nodevault logo.png" class="w-4 h-4 object-contain" style="filter: brightness(0) invert(1)" />
          </div>
          <span class="text-sm font-semibold text-gray-900">NodeVault</span>
          <span class="text-[11px] font-semibold px-1.5 py-0.5 rounded-md tracking-wider" style="background:#ede9fe; color:#6d28d9">ADMIN</span>
        </RouterLink>

        <!-- 中：Tab 导航 -->
        <nav class="flex items-stretch h-14 gap-0 justify-center">
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="relative flex items-center px-4 text-sm transition-colors duration-150 select-none whitespace-nowrap"
            :class="isActive(item.to)
              ? 'text-indigo-600 font-medium'
              : 'text-gray-500 hover:text-gray-800'"
          >
            {{ item.label }}
            <!-- 激活下划线 -->
            <span v-if="isActive(item.to)"
              class="absolute bottom-0 left-3 right-3 h-0.5 rounded-t-full"
              style="background: #6366f1"
            ></span>
          </RouterLink>
        </nav>

        <!-- 右：用户信息 -->
        <div class="flex items-center gap-2.5 justify-end">
          <div class="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold" style="background: linear-gradient(135deg, #6366f1, #8b5cf6)">
            {{ (auth.user?.display_name || auth.user?.username)?.charAt(0).toUpperCase() }}
          </div>
          <span class="text-sm text-gray-700">{{ auth.user?.display_name || auth.user?.username }}</span>
        </div>
      </div>
    </header>

    <!-- 页面内容 -->
    <main class="flex-1 overflow-y-auto">
      <div class="max-w-screen-xl mx-auto px-8 py-7">
        <RouterView />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()

const navItems = [
  { to: '/admin/users',        label: '用户管理' },
  { to: '/admin/nodes',        label: '全局节点' },
  { to: '/admin/categories',   label: '分类管理' },
  { to: '/admin/analytics',    label: '平台统计' },
  { to: '/admin/namespaces',   label: '部门管理' },
  { to: '/admin/applications', label: '申请管理' },
  { to: '/admin/settings',     label: '系统设置' },
]

function isActive(path: string) {
  return route.path.startsWith(path)
}
</script>
