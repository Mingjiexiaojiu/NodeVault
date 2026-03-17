<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '@/layouts/AppLayout.vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

function goLogin() {
  authStore.dismissSessionExpired()
  router.push('/login')
}
</script>

<template>
  <AppLayout v-if="route.meta.layout === 'app'" />
  <RouterView v-else />

  <!-- Token 失效全局弹窗 -->
  <Transition name="modal-fade">
    <div
      v-if="authStore.sessionExpired"
      class="fixed inset-0 z-[9999] flex items-center justify-center"
    >
      <!-- 遮罩 -->
      <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" />

      <!-- 弹窗卡片 -->
      <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-sm mx-4 p-8 flex flex-col items-center gap-5">
        <!-- 图标 -->
        <div class="w-16 h-16 rounded-full bg-amber-50 flex items-center justify-center">
          <svg class="w-8 h-8 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
          </svg>
        </div>

        <div class="text-center">
          <h2 class="text-lg font-semibold text-gray-800 mb-1">登录已失效</h2>
          <p class="text-sm text-gray-500 leading-relaxed">您的登录凭证已过期或失效，<br>请重新登录以继续使用。</p>
        </div>

        <button
          @click="goLogin"
          class="w-full py-2.5 px-6 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-xl transition-colors"
        >
          重新登录
        </button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>

