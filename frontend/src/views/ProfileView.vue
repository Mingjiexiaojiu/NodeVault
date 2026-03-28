<template>
  <div class="max-w-3xl mx-auto">
    <div class="mb-6">
      <h1 class="text-xl font-semibold text-gray-900">个人设置</h1>
      <p class="text-sm text-gray-400 mt-0.5">管理你的账户信息与密码</p>
    </div>

    <!-- 身份标识 -->
    <div class="bg-white rounded-2xl border border-gray-200 p-6 mb-6">
      <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">账户信息</h2>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-xs text-gray-400 mb-1">用户名</label>
          <div class="text-sm font-medium text-gray-900 font-mono bg-gray-50 px-3 py-2 rounded-lg">{{ authStore.user?.username }}</div>
        </div>
        <div>
          <label class="block text-xs text-gray-400 mb-1">邮箱</label>
          <div class="text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-lg">{{ authStore.user?.email }}</div>
        </div>
        <div>
          <label class="block text-xs text-gray-400 mb-1">身份</label>
          <div class="flex items-center gap-2">
            <span class="px-2.5 py-1 text-xs font-medium rounded-full" :class="roleBadgeClass">
              {{ authStore.user?.role_label || '普通用户' }}
            </span>
          </div>
        </div>
        <div>
          <label class="block text-xs text-gray-400 mb-1">注册时间</label>
          <div class="text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded-lg">{{ authStore.user?.created_at ? new Date(authStore.user.created_at).toLocaleDateString('zh-CN') : '—' }}</div>
        </div>
      </div>
    </div>

    <!-- 所属部门 -->
    <div class="bg-white rounded-2xl border border-gray-200 p-6 mb-6">
      <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">我的部门</h2>
      <div v-if="!authStore.user?.departments?.length" class="text-sm text-gray-400">暂未加入任何部门</div>
      <div v-else class="space-y-2">
        <RouterLink
          v-for="ns in authStore.user.departments"
          :key="ns.id"
          :to="`/departments/${ns.id}`"
          class="flex items-center justify-between px-4 py-3 bg-gray-50 rounded-lg hover:bg-indigo-50 transition-colors"
        >
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-sm">
              {{ (ns.display_name || ns.slug).charAt(0).toUpperCase() }}
            </div>
            <div>
              <div class="text-sm font-medium text-gray-900">{{ ns.display_name || ns.slug }}</div>
              <div class="text-xs text-gray-400">{{ ns.slug }}</div>
            </div>
          </div>
          <span class="px-2 py-0.5 text-xs rounded-full" :class="ns.role === 'admin' ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-200 text-gray-600'">
            {{ ns.role === 'admin' ? '管理员' : '成员' }}
          </span>
        </RouterLink>
      </div>
    </div>

    <!-- 个人资料表单 -->
    <div class="bg-white rounded-2xl border border-gray-200 p-6 mb-6">
      <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">个人资料</h2>
      <form @submit.prevent="handleSave" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">显示名称</label>
            <input v-model="form.display_name" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500" placeholder="你希望被称呼的名字" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">职位</label>
            <input v-model="form.title" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500" placeholder="如 高级算法工程师" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">所属部门</label>
            <input v-model="form.department" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500" placeholder="如 AI平台部" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">联系电话</label>
            <input v-model="form.phone" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500" placeholder="手机号" />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">头像 URL</label>
          <input v-model="form.avatar_url" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500" placeholder="https://example.com/avatar.jpg" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">个人简介</label>
          <textarea v-model="form.bio" rows="3" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500" placeholder="介绍一下你自己，擅长的方向..." ></textarea>
        </div>

        <div class="flex items-center justify-between pt-2">
          <span v-if="saveMsg" class="text-sm" :class="saveError ? 'text-red-600' : 'text-green-600'">{{ saveMsg }}</span>
          <span v-else></span>
          <button type="submit" :disabled="saving" class="px-5 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors">
            {{ saving ? '保存中...' : '保存资料' }}
          </button>
        </div>
      </form>
    </div>


    <!-- API Key 管理 -->
    <div class="bg-white rounded-2xl border border-gray-200 p-6 mb-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wide">API Keys</h2>
        <button @click="showCreateKey = true" class="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
          创建 API Key
        </button>
      </div>
      <div v-if="newlyCreatedKey" class="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-xl">
        <div class="flex items-start gap-3">
          <svg class="w-5 h-5 text-amber-500 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
          </svg>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-amber-800 mb-1">请立即保存此 Key，关闭后将无法再次查看</p>
            <div class="flex items-center gap-2">
              <code class="flex-1 text-xs bg-white border border-amber-200 rounded-lg px-3 py-2 font-mono text-gray-800 break-all">{{ newlyCreatedKey.full_key }}</code>
              <button @click="copyKey(newlyCreatedKey.full_key)" class="shrink-0 p-2 text-amber-600 hover:text-amber-800 hover:bg-amber-100 rounded-lg transition-colors" title="复制">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                </svg>
              </button>
              <button @click="newlyCreatedKey = null" class="shrink-0 p-2 text-amber-500 hover:text-amber-700 hover:bg-amber-100 rounded-lg transition-colors" title="关闭">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <p class="text-xs text-amber-600 mt-1.5">使用方式：<code class="bg-amber-100 px-1 rounded">X-API-Key: {{ newlyCreatedKey.full_key }}</code> 或 <code class="bg-amber-100 px-1 rounded">Authorization: Bearer {{ newlyCreatedKey.full_key }}</code></p>
          </div>
        </div>
      </div>

      <!-- Key 列表 -->
      <div v-if="keysLoading" class="py-6 text-center text-sm text-gray-400">加载中...</div>
      <div v-else-if="!apiKeys.length" class="py-6 text-center text-sm text-gray-400">暂无 API Key，点击上方按钮创建</div>
      <div v-else class="space-y-2">
        <div
          v-for="key in apiKeys" :key="key.id"
          class="flex items-center justify-between px-4 py-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
        >
          <div class="flex items-center gap-3 min-w-0">
            <div class="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center shrink-0">
              <svg class="w-4 h-4 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
              </svg>
            </div>
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-gray-900 truncate">{{ key.name }}</span>
                <span v-if="!key.is_active" class="px-1.5 py-0.5 text-xs bg-red-100 text-red-600 rounded">已禁用</span>
              </div>
              <div class="flex items-center gap-3 mt-0.5">
                <code class="text-xs text-gray-500 font-mono">{{ key.key_prefix }}...</code>
                <span class="text-xs text-gray-400">创建于 {{ formatDate(key.created_at) }}</span>
                <span v-if="key.last_used_at" class="text-xs text-gray-400">最近使用 {{ formatDate(key.last_used_at) }}</span>
                <span v-else class="text-xs text-gray-400">从未使用</span>
              </div>
            </div>
          </div>
          <button
            @click="handleDeleteKey(key.id, key.name)"
            class="shrink-0 p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors ml-3"
            title="删除此 Key"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- 用法说明 -->
      <div class="mt-4 p-3 bg-gray-50 rounded-xl border border-dashed border-gray-200">
        <p class="text-xs font-medium text-gray-500 mb-1.5">连接方式</p>
        <div class="space-y-1 text-xs text-gray-400 font-mono">
          <div><span class="text-gray-500">REST / Invoke / Export：</span>Authorization: Bearer nvk_xxx</div>
          <div><span class="text-gray-500">MCP SSE：</span>/mcp/sse?api_key=nvk_xxx</div>
        </div>
      </div>
    </div>

    <!-- 创建 Key 弹窗 -->
    <Teleport to="body">
      <div v-if="showCreateKey" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4" @click.self="showCreateKey = false">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
          <h3 class="text-base font-semibold text-gray-900 mb-4">创建 API Key</h3>
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Key 名称</label>
            <input
              v-model="newKeyName"
              ref="keyNameInput"
              @keyup.enter="handleCreateKey"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
              placeholder="如：生产环境 Agent、测试用"
              maxlength="128"
            />
            <p v-if="createKeyError" class="mt-1.5 text-xs text-red-600">{{ createKeyError }}</p>
          </div>
          <div class="flex gap-3 justify-end">
            <button @click="showCreateKey = false; newKeyName = ''; createKeyError = ''" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors">取消</button>
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
import { ref, computed, onMounted, nextTick } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { updateProfile, listApiKeys, createApiKey, deleteApiKey } from '@/api/auth'
import type { ProfilePayload, ApiKeyInfo, ApiKeyCreated } from '@/api/auth'

const authStore = useAuthStore()

const roleBadgeClass = computed(() => {
  const r = authStore.user?.role ?? 2
  if (r === 0) return 'bg-red-100 text-red-700'
  if (r === 1) return 'bg-amber-100 text-amber-700'
  return 'bg-gray-100 text-gray-600'
})

const form = ref<ProfilePayload>({
  display_name: '',
  avatar_url: '',
  bio: '',
  phone: '',
  department: '',
  title: '',
})

const saving = ref(false)
const saveMsg = ref('')
const saveError = ref(false)

function initForm() {
  const u = authStore.user
  if (u) {
    form.value = {
      display_name: u.display_name || '',
      avatar_url: u.avatar_url || '',
      bio: u.bio || '',
      phone: u.phone || '',
      department: u.department || '',
      title: u.title || '',
    }
  }
}

async function handleSave() {
  saving.value = true
  saveMsg.value = ''
  saveError.value = false
  try {
    const payload: Record<string, string> = {}
    for (const [k, v] of Object.entries(form.value)) {
      if (v) payload[k] = v
    }
    await updateProfile(payload as ProfilePayload)
    await authStore.fetchMe()
    saveMsg.value = '保存成功'
  } catch (e: any) {
    saveError.value = true
    saveMsg.value = e?.response?.data?.error?.message || '保存失败'
  } finally {
    saving.value = false
    setTimeout(() => { saveMsg.value = '' }, 3000)
  }
}

// ── API Key 管理 ──────────────────────────────────────────────

const apiKeys = ref<ApiKeyInfo[]>([])
const keysLoading = ref(false)
const newlyCreatedKey = ref<ApiKeyCreated | null>(null)

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

async function handleCreateKey() {
  const name = newKeyName.value.trim()
  if (!name) { createKeyError.value = '请输入 Key 名称'; return }
  creatingKey.value = true
  createKeyError.value = ''
  try {
    const res = await createApiKey(name)
    newlyCreatedKey.value = res.data
    showCreateKey.value = false
    newKeyName.value = ''
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
    // fallback for non-https
    const el = document.createElement('textarea')
    el.value = key
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
  })
}

function formatDate(iso: string) {
  const d = new Date(iso)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

// 弹窗打开时聚焦输入框
import { watch } from 'vue'
watch(showCreateKey, async (v) => {
  if (v) {
    await nextTick()
    keyNameInput.value?.focus()
  }
})

onMounted(() => {
  initForm()
  loadKeys()
})
</script>
