<template>
  <div class="min-h-screen" style="background: #f7f8fc">
    <!-- 顶部导航栏 -->
    <nav class="bg-white/95 backdrop-blur-md border-b border-gray-100 sticky top-0 z-10" style="box-shadow: 0 1px 0 rgba(0,0,0,0.04)">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <!-- Logo -->
          <RouterLink to="/" class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0" style="background: linear-gradient(135deg, #6366f1, #8b5cf6)">
              <img src="/nodevault logo.png" class="w-5 h-5 object-contain" style="filter: brightness(0) invert(1)" />
            </div>
            <span class="text-lg font-bold" style="background: linear-gradient(135deg, #6366f1, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent">NodeVault</span>
          </RouterLink>

          <!-- 导航链接 -->
          <div class="hidden sm:flex items-center gap-0.5">
            <RouterLink to="/" class="px-3.5 py-1.5 text-sm font-medium rounded-lg transition-all duration-150"
              :class="route.name === 'dashboard' ? 'text-indigo-700 bg-indigo-50 font-semibold' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'">看板</RouterLink>
            <RouterLink to="/nodes" class="px-3.5 py-1.5 text-sm font-medium rounded-lg transition-all duration-150"
              :class="String(route.name).startsWith('node') ? 'text-indigo-700 bg-indigo-50 font-semibold' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'">节点</RouterLink>
            <RouterLink to="/search" class="px-3.5 py-1.5 text-sm font-medium rounded-lg transition-all duration-150"
              :class="route.name === 'search' ? 'text-indigo-700 bg-indigo-50 font-semibold' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'">搜索</RouterLink>
            <RouterLink to="/departments" class="px-3.5 py-1.5 text-sm font-medium rounded-lg transition-all duration-150"
              :class="String(route.name).startsWith('department') ? 'text-indigo-700 bg-indigo-50 font-semibold' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'">部门</RouterLink>
            <RouterLink to="/discover" class="px-3.5 py-1.5 text-sm font-medium rounded-lg transition-all duration-150"
              :class="String(route.name).startsWith('discover') ? 'text-indigo-700 bg-indigo-50 font-semibold' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'">发现</RouterLink>
            <RouterLink to="/skills" class="px-3.5 py-1.5 text-sm font-medium rounded-lg transition-all duration-150"
              :class="String(route.name).startsWith('skill') ? 'text-indigo-700 bg-indigo-50 font-semibold' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'">技能</RouterLink>
            <RouterLink v-if="auth.user && auth.user.role <= 1" to="/categories" class="px-3.5 py-1.5 text-sm font-medium rounded-lg transition-all duration-150"
              :class="route.name === 'categories' ? 'text-indigo-700 bg-indigo-50 font-semibold' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'">分类</RouterLink>
          </div>

          <!-- 用户信息 -->
          <div class="relative flex items-center">
            <button
              class="flex items-center gap-2 px-2.5 py-1.5 rounded-xl hover:bg-gray-50 transition-colors"
              @click="showUserMenu = !showUserMenu"
            >
              <div class="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0" style="background: linear-gradient(135deg, #6366f1, #8b5cf6)">
                {{ auth.user?.username?.charAt(0).toUpperCase() }}
              </div>
              <span class="text-sm font-medium text-gray-700 max-w-[100px] truncate">{{ auth.user?.display_name || auth.user?.username }}</span>
              <svg class="w-3.5 h-3.5 text-gray-400 transition-transform duration-150" :class="showUserMenu ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
              </svg>
            </button>
            <!-- 下拉菜单 -->
            <div v-if="showUserMenu" class="absolute right-0 top-full mt-2 w-52 bg-white rounded-2xl border border-gray-100 py-1.5 z-50" style="box-shadow: 0 8px 32px rgba(0,0,0,0.10), 0 2px 8px rgba(0,0,0,0.06)" @mouseleave="showUserMenu = false">
              <div class="px-4 py-3 border-b border-gray-100 mb-1">
                <p class="text-sm font-semibold text-gray-900 truncate">{{ auth.user?.display_name || auth.user?.username }}</p>
                <p class="text-xs text-gray-400 mt-0.5 truncate">{{ auth.user?.email }}</p>
              </div>
              <RouterLink to="/profile" class="flex items-center gap-2.5 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors" @click="showUserMenu = false">
                <svg class="w-3.5 h-3.5 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
                个人设置
              </RouterLink>
              <RouterLink to="/api-keys" class="flex items-center gap-2.5 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors" @click="showUserMenu = false">
                <svg class="w-3.5 h-3.5 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/></svg>
                API Keys
              </RouterLink>
              <RouterLink to="/ai-config" class="flex items-center gap-2.5 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors" @click="showUserMenu = false">
                <svg class="w-3.5 h-3.5 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
                AI 配置
              </RouterLink>
              <div class="border-t border-gray-100 mt-1.5 mb-1"></div>
              <button class="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-red-500 hover:bg-red-50 transition-colors" @click="handleLogout">
                <svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
                退出登录
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>

    <!-- 主内容 -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <RouterView />
    </main>

    <!-- 悬浮返回按钮 -->
    <button
      class="fixed bottom-6 right-6 flex items-center gap-1.5 px-3.5 py-2.5 rounded-full transition-all duration-200 hover:scale-105 active:scale-95 group"
      style="background: rgba(255,255,255,0.92); border: 1px solid rgba(99,102,241,0.15); box-shadow: 0 4px 24px rgba(99,102,241,0.12), 0 1px 6px rgba(0,0,0,0.05); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px)"
      title="返回上一页"
      @click="router.back()"
    >
      <svg class="w-4 h-4 text-indigo-600 transition-transform duration-150 group-hover:-translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
      </svg>
      <span class="text-xs font-semibold text-indigo-600">返回</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const showUserMenu = ref(false)

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>
