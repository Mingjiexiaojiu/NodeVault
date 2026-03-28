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

      <!-- API 密钥管理 -->
      <div class="bg-white rounded-2xl overflow-hidden" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
        <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h3 class="font-semibold text-gray-800">API 密钥管理</h3>
            <p class="text-xs text-gray-400 mt-0.5">平台所有用户的 API Key 只读审计视图</p>
          </div>
        </div>
        <div v-if="keysLoading" class="flex items-center justify-center h-40">
          <div class="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
        <table v-else class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">名称</th>
              <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">所属用户</th>
              <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">前缀</th>
              <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">状态</th>
              <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">最后使用</th>
              <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">创建时间</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="key in apiKeys" :key="key.id" class="hover:bg-gray-50/60 transition-colors">
              <td class="px-5 py-3.5 font-medium text-gray-900">{{ key.name }}</td>
              <td class="px-4 py-3.5 text-gray-600">{{ key.username }}</td>
              <td class="px-4 py-3.5 font-mono text-xs text-gray-500">{{ key.key_prefix }}…</td>
              <td class="px-4 py-3.5">
                <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium"
                  :class="key.is_active ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'">
                  <span class="w-1.5 h-1.5 rounded-full" :class="key.is_active ? 'bg-green-500' : 'bg-gray-400'"></span>
                  {{ key.is_active ? '启用' : '停用' }}
                </span>
              </td>
              <td class="px-4 py-3.5 text-xs text-gray-400">{{ key.last_used_at?.slice(0, 10) || '从未' }}</td>
              <td class="px-4 py-3.5 text-xs text-gray-400">{{ key.created_at?.slice(0, 10) }}</td>
            </tr>
            <tr v-if="!keysLoading && apiKeys.length === 0">
              <td colspan="6" class="text-center py-10 text-gray-400">暂无 API 密钥数据</td>
            </tr>
          </tbody>
        </table>
        <div v-if="keysTotalPages > 1" class="flex items-center justify-center gap-2 py-3">
          <button v-for="p in keysTotalPages" :key="p" @click="keysPage = p; loadKeys()"
            class="w-7 h-7 rounded-lg text-sm font-medium transition-colors"
            :class="p === keysPage ? 'bg-indigo-600 text-white' : 'text-gray-500 hover:bg-gray-100'">
            {{ p }}
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
import { ref, computed, onMounted } from 'vue'
import { getSettings, updateSetting, listAllApiKeys, type AdminApiKeyListItem } from '@/api/admin'

const apiKeys = ref<AdminApiKeyListItem[]>([])
const keysTotal = ref(0)
const keysPage = ref(1)
const keysPageSize = 20
const keysLoading = ref(false)
const keysTotalPages = computed(() => Math.ceil(keysTotal.value / keysPageSize))

async function loadKeys() {
  keysLoading.value = true
  try {
    const res = await listAllApiKeys({ page: keysPage.value, page_size: keysPageSize })
    apiKeys.value = res.data.items
    keysTotal.value = res.data.total
  } finally {
    keysLoading.value = false
  }
}

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

onMounted(() => {
  loadSettings()
  loadKeys()
})
</script>
