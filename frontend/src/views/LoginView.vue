<template>
  <!-- 渐变背景 + 装饰圆 -->
  <div class="min-h-screen relative flex items-center justify-center px-4 overflow-hidden"
    style="background: linear-gradient(135deg, #eef2ff 0%, #f0f9ff 50%, #faf5ff 100%)">

    <!-- 背景装饰圆 -->
    <div class="absolute -top-32 -left-32 w-96 h-96 rounded-full opacity-30"
      style="background: radial-gradient(circle, #6366f1, transparent 70%)" />
    <div class="absolute -bottom-40 -right-40 w-[30rem] h-[30rem] rounded-full opacity-20"
      style="background: radial-gradient(circle, #8b5cf6, transparent 70%)" />
    <div class="absolute top-1/2 left-10 w-48 h-48 rounded-full opacity-10"
      style="background: radial-gradient(circle, #06b6d4, transparent 70%)" />

    <!-- 卡片 -->
    <div class="relative w-full max-w-md">
      <!-- Logo 区 -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-4"
          style="background: linear-gradient(135deg, #6366f1, #8b5cf6)">
          <img src="/nodevault logo.png" class="w-9 h-9 object-contain" style="filter: brightness(0) invert(1)" />
        </div>
        <h1 class="text-3xl font-extrabold tracking-tight"
          style="background: linear-gradient(135deg, #6366f1, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent">
          NodeVault
        </h1>
        <p class="text-gray-500 mt-1.5 text-sm">企业级 AI 能力注册中心</p>
      </div>

      <!-- 表单卡片 -->
      <div class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl shadow-indigo-100/50 border border-white/60 px-8 py-8">
        <h2 class="text-lg font-semibold text-gray-800 mb-6">欢迎回来</h2>

        <form class="space-y-5" @submit.prevent="handleLogin">
          <div class="space-y-1">
            <label class="text-sm font-medium text-gray-700">用户名 / 邮箱 <span class="text-red-400">*</span></label>
            <div class="relative">
              <div class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                </svg>
              </div>
              <input
                v-model="form.identifier"
                type="text"
                autocomplete="username"
                placeholder="用户名或邮箱地址"
                :class="['w-full pl-10 pr-4 py-2.5 rounded-xl border text-sm transition focus:outline-none focus:ring-2',
                  errors.identifier ? 'border-red-300 focus:ring-red-400' : 'border-gray-200 focus:ring-indigo-400 focus:border-indigo-400']"
              />
            </div>
            <p v-if="errors.identifier" class="text-xs text-red-500">{{ errors.identifier }}</p>
          </div>

          <div class="space-y-1">
            <label class="text-sm font-medium text-gray-700">密码 <span class="text-red-400">*</span></label>
            <div class="relative">
              <div class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <input
                v-model="form.password"
                :type="showPwd ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="••••••••"
                :class="['w-full pl-10 pr-10 py-2.5 rounded-xl border text-sm transition focus:outline-none focus:ring-2',
                  errors.password ? 'border-red-300 focus:ring-red-400' : 'border-gray-200 focus:ring-indigo-400 focus:border-indigo-400']"
              />
              <button type="button" class="absolute inset-y-0 right-3 flex items-center text-gray-400 hover:text-gray-600"
                @click="showPwd = !showPwd">
                <svg v-if="!showPwd" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                </svg>
              </button>
            </div>
            <p v-if="errors.password" class="text-xs text-red-500">{{ errors.password }}</p>
          </div>

          <div v-if="successMsg"
            class="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-100 px-4 py-3 rounded-xl">
            <svg class="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            {{ successMsg }}
          </div>

          <div v-if="errorMsg"
            class="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100 px-4 py-3 rounded-xl">
            <svg class="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
            {{ errorMsg }}
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full py-2.5 rounded-xl text-white text-sm font-semibold transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            style="background: linear-gradient(135deg, #6366f1, #8b5cf6); box-shadow: 0 4px 15px rgba(99,102,241,0.4)"
          >
            <svg v-if="loading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {{ loading ? '登录中...' : '登 录' }}
          </button>
        </form>

        <p class="mt-6 text-center text-sm text-gray-500">
          还没有账号？
          <RouterLink to="/register" class="font-medium text-indigo-600 hover:text-indigo-700">
            立即注册 →
          </RouterLink>
        </p>
      </div>

      <!-- 底部说明 -->
      <p class="mt-6 text-center text-xs text-gray-400">NodeVault · Enterprise AI Capability Registry</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = reactive({ identifier: '', password: '' })
const errors = reactive({ identifier: '', password: '' })
const errorMsg = ref('')
const loading = ref(false)
const showPwd = ref(false)

const successMsg = computed(() => route.query.registered === '1' ? '注册成功，请登录' : '')

async function handleLogin() {
  errors.identifier = ''
  errors.password = ''
  errorMsg.value = ''

  if (!form.identifier) { errors.identifier = '请输入用户名或邮箱'; return }
  if (!form.password) { errors.password = '请输入密码'; return }

  loading.value = true
  try {
    await auth.login({ identifier: form.identifier, password: form.password })
    const redirect = route.query.redirect as string | undefined
    // 超管直接进管理控制台（除非已有明确的 /admin/* 跳转目标）
    if (auth.isSuperAdmin) {
      router.push(redirect?.startsWith('/admin') ? redirect : '/admin/analytics')
    } else {
      router.push(redirect ?? '/')
    }
  } catch (e: unknown) {
    const err = e as { response?: { status?: number } }
    if (err.response?.status === 401) {
      errorMsg.value = '用户名/邮箱或密码错误'
    } else {
      errorMsg.value = '登录失败，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}
</script>
