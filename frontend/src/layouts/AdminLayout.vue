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

        <!-- 右：用户信息 + 下拉菜单 -->
        <div class="flex items-center gap-2.5 justify-end relative" ref="avatarRef">
          <button
            @click="menuOpen = !menuOpen"
            class="flex items-center gap-2.5 rounded-xl px-2 py-1 hover:bg-gray-100 transition-colors"
          >
            <div class="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold" style="background: linear-gradient(135deg, #6366f1, #8b5cf6)">
              {{ (auth.user?.display_name || auth.user?.username)?.charAt(0).toUpperCase() }}
            </div>
            <span class="text-sm text-gray-700">{{ auth.user?.display_name || auth.user?.username }}</span>
            <svg class="w-3.5 h-3.5 text-gray-400 transition-transform" :class="menuOpen ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
          </button>

          <!-- 下拉菜单 -->
          <div
            v-if="menuOpen"
            class="absolute right-0 top-10 w-44 bg-white rounded-xl shadow-lg border border-gray-100 py-1 z-50"
          >
            <RouterLink
              to="/"
              @click="menuOpen = false"
              class="flex items-center gap-2.5 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
            >
              <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
              返回首页
            </RouterLink>
            <div class="border-t border-gray-100 my-1"></div>
            <button
              @click="handleLogout"
              class="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-red-500 hover:bg-red-50 transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
              退出登录
            </button>
          </div>
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
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const menuOpen = ref(false)
const avatarRef = ref<HTMLElement | null>(null)

function handleClickOutside(e: MouseEvent) {
  if (avatarRef.value && !avatarRef.value.contains(e.target as Node)) {
    menuOpen.value = false
  }
}

onMounted(() => document.addEventListener('mousedown', handleClickOutside))
onUnmounted(() => document.removeEventListener('mousedown', handleClickOutside))

async function handleLogout() {
  menuOpen.value = false
  await auth.logout()
  router.push('/login')
}

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
