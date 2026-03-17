<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 顶部导航栏 -->
    <nav class="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <!-- Logo -->
          <RouterLink to="/" class="flex items-center gap-2">
            <span class="text-2xl font-bold text-indigo-600">NodeVault</span>
          </RouterLink>

          <!-- 导航链接 -->
          <div class="hidden sm:flex items-center gap-6">
            <RouterLink
              to="/"
              class="text-sm font-medium text-gray-600 hover:text-indigo-600 transition-colors"
              :class="{ 'text-indigo-600': route.name === 'dashboard' }"
            >
              仪表盘
            </RouterLink>
            <RouterLink
              to="/nodes"
              class="text-sm font-medium text-gray-600 hover:text-indigo-600 transition-colors"
              :class="{ 'text-indigo-600': String(route.name).startsWith('node') }"
            >
              节点管理
            </RouterLink>
            <RouterLink
              to="/search"
              class="text-sm font-medium text-gray-600 hover:text-indigo-600 transition-colors"
              :class="{ 'text-indigo-600': route.name === 'search' }"
            >
              搜索
            </RouterLink>
          </div>

          <!-- 用户信息 -->
          <div class="flex items-center gap-4">
            <span class="text-sm text-gray-600">{{ auth.user?.username }}</span>
            <button
              class="text-sm text-gray-500 hover:text-red-500 transition-colors"
              @click="handleLogout"
            >
              退出
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- 主内容 -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <RouterView />
    </main>

    <!-- 全局悬浮返回球 -->
    <button
      v-if="canGoBack"
      class="fixed bottom-8 right-8 w-12 h-12 bg-indigo-600 rounded-full shadow-lg shadow-indigo-300 flex items-center justify-center text-white hover:bg-indigo-700 hover:scale-110 active:scale-95 transition-all duration-200"
      title="返回上一页"
      @click="router.back()"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

// 在仪表盘、节点列表、搜索等主导航页不显示返回球
const canGoBack = computed(() => !['dashboard', 'node-list', 'search'].includes(String(route.name)))

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>
