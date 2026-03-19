<template>
  <div class="max-w-3xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-xl font-semibold text-gray-900">Agent API Keys</h1>
        <p class="text-sm text-gray-400 mt-0.5">用于 Agent 程序直接调用，无需登录流程</p>
      </div>
      <button
        @click="showCreateKey = true"
        class="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-xl hover:bg-indigo-700 active:scale-95 transition-all shadow-sm shadow-indigo-200"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/>
        </svg>
        创建 Key
      </button>
    </div>

    <!-- 新创建的 Key 一次性展示 -->
    <div v-if="newlyCreatedKey" class="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-2xl">
      <div class="flex items-start gap-3">
        <svg class="w-5 h-5 text-amber-500 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
        </svg>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-amber-800 mb-2">请立即保存此 Key，关闭后将无法再次查看</p>
          <div class="flex items-center gap-2">
            <code class="flex-1 text-xs bg-white border border-amber-200 rounded-lg px-3 py-2 font-mono text-gray-800 break-all select-all">{{ newlyCreatedKey.full_key }}</code>
            <button
              @click="copyKey(newlyCreatedKey.full_key)"
              class="shrink-0 p-2 text-amber-600 hover:text-amber-800 hover:bg-amber-100 rounded-lg transition-colors"
              :title="copied ? '已复制！' : '复制'"
            >
              <svg v-if="!copied" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
              </svg>
              <svg v-else class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
              </svg>
            </button>
            <button @click="newlyCreatedKey = null; copied = false" class="shrink-0 p-2 text-amber-500 hover:text-amber-700 hover:bg-amber-100 rounded-lg transition-colors" title="关闭">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
          <p class="text-xs text-amber-600 mt-2">使用方式：<code class="bg-amber-100 px-1 rounded">Authorization: Bearer {{ newlyCreatedKey.full_key }}</code></p>
        </div>
      </div>
    </div>

    <!-- Key 列表 -->
    <div class="bg-white rounded-2xl border border-gray-100" style="box-shadow: 0 1px 3px rgba(0,0,0,0.04)">
      <div v-if="keysLoading" class="py-16 text-center text-sm text-gray-400">加载中...</div>
      <div v-else-if="!apiKeys.length" class="py-16 text-center">
        <div class="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-3">
          <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
          </svg>
        </div>
        <p class="text-sm text-gray-400">暂无 API Key</p>
        <p class="text-xs text-gray-300 mt-1">点击右上角「创建 Key」生成第一个</p>
      </div>
      <div v-else class="divide-y divide-gray-100">
        <div
          v-for="key in apiKeys"
          :key="key.id"
          class="flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors"
        >
          <div class="flex items-center gap-4 min-w-0">
            <div class="w-9 h-9 rounded-xl bg-indigo-100 flex items-center justify-center shrink-0">
              <svg class="w-4 h-4 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
              </svg>
            </div>
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-gray-900">{{ key.name }}</span>
                <span v-if="!key.is_active" class="px-1.5 py-0.5 text-xs bg-red-100 text-red-600 rounded">已禁用</span>
              </div>
              <div class="flex items-center gap-3 mt-0.5 flex-wrap">
                <code class="text-xs text-gray-400 font-mono bg-gray-100 px-1.5 py-0.5 rounded">{{ key.key_prefix }}...</code>
                <span class="text-xs text-gray-400">创建于 {{ formatDate(key.created_at) }}</span>
                <span v-if="key.last_used_at" class="text-xs text-gray-400">最近使用 {{ formatDate(key.last_used_at) }}</span>
                <span v-else class="text-xs text-gray-300">从未使用</span>
              </div>
            </div>
          </div>
          <button
            @click="handleDeleteKey(key.id, key.name)"
            class="shrink-0 p-2 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors ml-4"
            title="删除"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 用法说明 -->
    <div class="mt-4 p-4 bg-gray-50 rounded-2xl border border-dashed border-gray-200">
      <p class="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">连接方式</p>
      <div class="space-y-1.5 text-xs font-mono">
        <div class="flex items-start gap-2">
          <span class="text-gray-400 shrink-0">REST / Invoke / Export</span>
          <span class="text-gray-300">—</span>
          <code class="text-indigo-600">Authorization: Bearer nvk_xxx</code>
        </div>
        <div class="flex items-start gap-2">
          <span class="text-gray-400 shrink-0">或</span>
          <span class="text-gray-300 shrink-0">——————————</span>
          <code class="text-indigo-600">X-API-Key: nvk_xxx</code>
        </div>
        <div class="flex items-start gap-2">
          <span class="text-gray-400 shrink-0">MCP SSE</span>
          <span class="text-gray-300">——————————</span>
          <code class="text-indigo-600">/mcp/sse?api_key=nvk_xxx</code>
        </div>
      </div>
    </div>

    <!-- 创建 Key 弹窗 -->
    <Teleport to="body">
      <div
        v-if="showCreateKey"
        class="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        @click.self="closeCreateModal"
      >
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
          <h3 class="text-base font-semibold text-gray-900 mb-4">创建 API Key</h3>
          <div class="mb-5">
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Key 名称</label>
            <input
              v-model="newKeyName"
              ref="keyNameInput"
              @keyup.enter="handleCreateKey"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none"
              placeholder="如：生产环境 Agent、测试机器人"
              maxlength="128"
            />
            <p v-if="createKeyError" class="mt-1.5 text-xs text-red-600">{{ createKeyError }}</p>
          </div>
          <div class="flex gap-3 justify-end">
            <button @click="closeCreateModal" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors">取消</button>
            <button @click="handleCreateKey" :disabled="creatingKey" class="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors">
              {{ creatingKey ? '创建中...' : '创建' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from 'vue'
import { listApiKeys, createApiKey, deleteApiKey } from '@/api/auth'
import type { ApiKeyInfo, ApiKeyCreated } from '@/api/auth'

const apiKeys = ref<ApiKeyInfo[]>([])
const keysLoading = ref(false)
const newlyCreatedKey = ref<ApiKeyCreated | null>(null)
const copied = ref(false)

const showCreateKey = ref(false)
const newKeyName = ref('')
const createKeyError = ref('')
const creatingKey = ref(false)
const keyNameInput = ref<HTMLInputElement | null>(null)

async function loadKeys() {
  keysLoading.value = true
  try {
    const res = await listApiKeys()
    apiKeys.value = res.data
  } catch {
    // ignore
  } finally {
    keysLoading.value = false
  }
}

function closeCreateModal() {
  showCreateKey.value = false
  newKeyName.value = ''
  createKeyError.value = ''
}

async function handleCreateKey() {
  const name = newKeyName.value.trim()
  if (!name) { createKeyError.value = '请输入 Key 名称'; return }
  creatingKey.value = true
  createKeyError.value = ''
  try {
    const res = await createApiKey(name)
    newlyCreatedKey.value = res.data
    copied.value = false
    closeCreateModal()
    await loadKeys()
  } catch (e: any) {
    createKeyError.value = e?.response?.data?.error?.message || '创建失败'
  } finally {
    creatingKey.value = false
  }
}

async function handleDeleteKey(id: string, name: string) {
  if (!confirm(`确认删除 API Key「${name}」？删除后相关 Agent 将无法继续使用此 Key。`)) return
  try {
    await deleteApiKey(id)
    apiKeys.value = apiKeys.value.filter(k => k.id !== id)
    if (newlyCreatedKey.value?.id === id) newlyCreatedKey.value = null
  } catch (e: any) {
    alert(e?.response?.data?.error?.message || '删除失败')
  }
}

function copyKey(key: string) {
  navigator.clipboard.writeText(key).catch(() => {
    const el = document.createElement('textarea')
    el.value = key
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
  })
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

watch(showCreateKey, async (v) => {
  if (v) {
    await nextTick()
    keyNameInput.value?.focus()
  }
})

onMounted(loadKeys)
</script>
