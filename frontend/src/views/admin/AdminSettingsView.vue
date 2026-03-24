<template>
  <div class="max-w-2xl space-y-6">
    <p class="text-sm text-gray-500">修改平台全局配置项，每项保存后立即生效。</p>

    <div v-if="loading" class="flex items-center justify-center h-40">
      <div class="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
    </div>

    <template v-else>
      <!-- 开放注册 -->
      <div class="bg-white rounded-2xl p-5 space-y-4" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
        <div>
          <h3 class="font-semibold text-gray-800">开放用户注册</h3>
          <p class="text-xs text-gray-400 mt-0.5">关闭后新用户将无法注册账号。</p>
        </div>
        <label class="inline-flex items-center gap-3 cursor-pointer select-none">
          <div class="relative" @click="toggleRegistration">
            <div class="w-11 h-6 rounded-full transition-colors" :class="enableRegistration ? 'bg-indigo-600' : 'bg-gray-200'"></div>
            <div class="absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform"
              :class="enableRegistration ? 'translate-x-5' : 'translate-x-0'"></div>
          </div>
          <span class="text-sm text-gray-700">{{ enableRegistration ? '已开放' : '已关闭' }}</span>
        </label>
        <div class="flex justify-end">
          <button @click="saveSetting('enable_registration', String(enableRegistration))"
            :disabled="saving['enable_registration']"
            class="text-sm font-medium px-4 py-2 rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 transition-colors disabled:opacity-60">
            {{ saving['enable_registration'] ? '保存中…' : '保存' }}
          </button>
        </div>
      </div>

      <!-- 平台公告 -->
      <div class="bg-white rounded-2xl p-5 space-y-4" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
        <div>
          <h3 class="font-semibold text-gray-800">平台公告</h3>
          <p class="text-xs text-gray-400 mt-0.5">显示在所有用户首页顶部的通知横幅，留空则不显示。</p>
        </div>
        <textarea v-model="announcement" rows="3"
          class="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-300 resize-none"
          placeholder="在此输入公告内容…"></textarea>
        <div class="flex justify-end">
          <button @click="saveSetting('platform_announcement', announcement)"
            :disabled="saving['platform_announcement']"
            class="text-sm font-medium px-4 py-2 rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 transition-colors disabled:opacity-60">
            {{ saving['platform_announcement'] ? '保存中…' : '保存' }}
          </button>
        </div>
      </div>

      <!-- 默认用户角色 -->
      <div class="bg-white rounded-2xl p-5 space-y-4" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
        <div>
          <h3 class="font-semibold text-gray-800">新用户默认角色</h3>
          <p class="text-xs text-gray-400 mt-0.5">新注册用户被分配的初始角色。</p>
        </div>
        <select v-model="defaultRole"
          class="text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-300 w-52">
          <option value="2">普通用户</option>
          <option value="1">管理员</option>
        </select>
        <div class="flex justify-end">
          <button @click="saveSetting('default_user_role', defaultRole)"
            :disabled="saving['default_user_role']"
            class="text-sm font-medium px-4 py-2 rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 transition-colors disabled:opacity-60">
            {{ saving['default_user_role'] ? '保存中…' : '保存' }}
          </button>
        </div>
      </div>
    </template>

    <!-- Toast -->
    <div v-if="toast" class="fixed bottom-6 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-sm px-5 py-2.5 rounded-full shadow-lg z-50">
      {{ toast }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getSettings, updateSetting } from '@/api/admin'

const loading = ref(false)
const enableRegistration = ref(true)
const announcement = ref('')
const defaultRole = ref('2')
const saving = ref<Record<string, boolean>>({})
const toast = ref('')
let toastTimer: ReturnType<typeof setTimeout>

async function loadSettings() {
  loading.value = true
  try {
    const res = await getSettings()
    const items = res.data
    for (const item of items) {
      if (item.key === 'enable_registration') enableRegistration.value = item.value === 'true'
      if (item.key === 'platform_announcement') announcement.value = item.value ?? ''
      if (item.key === 'default_user_role') defaultRole.value = item.value ?? '2'
    }
  } finally {
    loading.value = false
  }
}

function toggleRegistration() {
  enableRegistration.value = !enableRegistration.value
}

async function saveSetting(key: string, value: string) {
  saving.value[key] = true
  try {
    await updateSetting(key, value)
    showToast('设置已保存')
  } catch (e: unknown) {
    const err = e as { uiMessage?: string }
    showToast(err?.uiMessage || '保存失败')
  } finally {
    saving.value[key] = false
  }
}

function showToast(msg: string) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 2500)
}

onMounted(loadSettings)
</script>
