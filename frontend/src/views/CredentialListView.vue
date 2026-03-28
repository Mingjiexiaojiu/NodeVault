<template>
  <div class="max-w-4xl mx-auto">
    <!-- 头部 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-xl font-semibold text-gray-900">服务凭据</h1>
        <p class="text-sm text-gray-400 mt-0.5">管理 NodeVault 调用下游服务时使用的鉴权凭据</p>
      </div>
      <button
        @click="openCreateForm"
        class="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-xl hover:bg-indigo-700 active:scale-95 transition-all shadow-sm shadow-indigo-200"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/>
        </svg>
        新建凭据
      </button>
    </div>

    <!-- 列表 -->
    <div class="bg-white rounded-2xl border border-gray-100" style="box-shadow: 0 1px 3px rgba(0,0,0,0.04)">
      <div v-if="loading" class="py-16 text-center text-sm text-gray-400">加载中...</div>
      <div v-else-if="!credentials.length" class="py-16 text-center">
        <div class="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-3">
          <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
          </svg>
        </div>
        <p class="text-sm text-gray-400">暂无服务凭据</p>
        <p class="text-xs text-gray-300 mt-1">点击右上角「新建凭据」添加第一个</p>
      </div>
      <div v-else class="divide-y divide-gray-100">
        <div
          v-for="cred in credentials"
          :key="cred.id"
          class="flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors group"
        >
          <div class="flex items-center gap-4 min-w-0">
            <div class="w-9 h-9 rounded-xl flex items-center justify-center shrink-0" :class="authTypeColor(cred.auth_type)">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
              </svg>
            </div>
            <div class="min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-sm font-medium text-gray-900">{{ cred.name }}</span>
                <span class="px-1.5 py-0.5 text-xs rounded font-mono" :class="authTypeBadge(cred.auth_type)">
                  {{ authTypeLabel(cred.auth_type) }}
                </span>
                <!-- test result badge -->
                <span
                  v-if="testResults[cred.id]"
                  class="px-1.5 py-0.5 text-xs rounded"
                  :class="testResults[cred.id].success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'"
                >
                  {{ testResults[cred.id].success ? `✓ 连接成功 ${testResults[cred.id].latency_ms != null ? testResults[cred.id].latency_ms + 'ms' : ''}` : `✗ ${testResults[cred.id].message}` }}
                </span>
              </div>
              <div class="flex items-center gap-3 mt-0.5 flex-wrap">
                <span class="text-xs text-gray-400 font-mono truncate max-w-xs">{{ cred.base_url }}</span>
                <span class="text-xs text-gray-300">·</span>
                <span class="text-xs text-gray-400">创建于 {{ formatDate(cred.created_at) }}</span>
              </div>
            </div>
          </div>
          <!-- 操作按钮 -->
          <div class="flex items-center gap-1 shrink-0 ml-4">
            <button
              @click="handleTest(cred.id)"
              :disabled="testing[cred.id]"
              class="p-2 text-gray-300 hover:text-indigo-500 hover:bg-indigo-50 rounded-lg transition-colors"
              title="测试连接"
            >
              <svg v-if="!testing[cred.id]" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
              </svg>
              <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
            </button>
            <button
              @click="openEditForm(cred)"
              class="p-2 text-gray-300 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="编辑"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
              </svg>
            </button>
            <button
              @click="handleDelete(cred)"
              class="p-2 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
              title="删除"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 说明 -->
    <div class="mt-4 p-4 bg-gray-50 rounded-2xl border border-dashed border-gray-200">
      <p class="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">工作原理</p>
      <p class="text-xs text-gray-400 leading-relaxed">
        创建凭据后，在 Node 创建/编辑页面绑定到对应 Node，NodeVault 转发请求时将自动附加鉴权信息。
        未显式绑定凭据的 Node，系统会按 <code class="bg-gray-100 px-1 rounded">base_url</code> 前缀自动匹配合适的凭据。
      </p>
    </div>

    <!-- 创建 / 编辑 Modal -->
    <Teleport to="body">
      <div
        v-if="showForm"
        class="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-start justify-center p-4 overflow-y-auto"
        @click.self="closeForm"
      >
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg my-8 p-6">
          <div class="flex items-center justify-between mb-5">
            <h3 class="text-base font-semibold text-gray-900">
              {{ editingId ? '编辑凭据' : '新建凭据' }}
            </h3>
            <button @click="closeForm" class="p-1 text-gray-400 hover:text-gray-600 rounded-lg transition-colors">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <div class="space-y-4">
            <!-- 名称 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">名称 <span class="text-red-500">*</span></label>
              <input
                v-model="form.name"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none"
                placeholder="如：风控服务生产环境"
                maxlength="128"
              />
              <p v-if="formErrors.name" class="mt-1 text-xs text-red-600">{{ formErrors.name }}</p>
            </div>

            <!-- base_url（仅创建时可填） -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">服务 Base URL <span class="text-red-500">*</span></label>
              <input
                v-model="form.base_url"
                :disabled="!!editingId"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none disabled:bg-gray-50 disabled:text-gray-400"
                placeholder="https://risk-service.company.com"
              />
              <p v-if="editingId" class="mt-1 text-xs text-gray-400">Base URL 创建后不可修改</p>
              <p v-if="formErrors.base_url" class="mt-1 text-xs text-red-600">{{ formErrors.base_url }}</p>
            </div>

            <!-- 鉴权类型（仅创建时可选） -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">鉴权类型 <span class="text-red-500">*</span></label>
              <select
                v-model="form.auth_type"
                :disabled="!!editingId"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none disabled:bg-gray-50 disabled:text-gray-400"
              >
                <option value="bearer_login">Bearer Login（账号密码登录获取 Token）</option>
                <option value="bearer_static">Bearer Static（固定 Bearer Token）</option>
                <option value="api_key">API Key</option>
                <option value="basic">HTTP Basic Auth</option>
              </select>
              <p v-if="editingId" class="mt-1 text-xs text-gray-400">鉴权类型创建后不可修改</p>
            </div>

            <!-- bearer_login 字段 -->
            <template v-if="form.auth_type === 'bearer_login'">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1.5">登录端点 <span class="text-red-500">*</span></label>
                <input v-model="form.login_endpoint" :disabled="!!editingId" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none disabled:bg-gray-50 disabled:text-gray-400" placeholder="https://service.com/api/auth/login"/>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1.5">登录请求体模板</label>
                <input v-model="form.login_body_template" :disabled="!!editingId" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none disabled:bg-gray-50 disabled:text-gray-400" placeholder='{"username":"{{username}}","password":"{{password}}"}' />
                <p class="mt-1 text-xs text-gray-400">用 <code>&#123;&#123;username&#125;&#125;</code> 和 <code>&#123;&#123;password&#125;&#125;</code> 作为占位符</p>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1.5">用户名 <span class="text-red-500">*</span></label>
                  <input v-model="form.username" :disabled="!!editingId" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none disabled:bg-gray-50 disabled:text-gray-400" placeholder="admin"/>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1.5">密码 {{ editingId ? '（留空保持不变）' : '*' }}</label>
                  <input v-model="form.password" type="password" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none" :placeholder="editingId ? '不修改则留空' : '••••••••'"/>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1.5">Token JSON 路径</label>
                  <input v-model="form.token_json_path" :disabled="!!editingId" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none disabled:bg-gray-50 disabled:text-gray-400" placeholder="data.access_token"/>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1.5">Token 有效期（秒）</label>
                  <input v-model.number="form.token_ttl" type="number" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none" placeholder="3600"/>
                </div>
              </div>
            </template>

            <!-- bearer_static 字段 -->
            <template v-if="form.auth_type === 'bearer_static'">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1.5">Bearer Token {{ editingId ? '（留空保持不变）' : '*' }}</label>
                <input v-model="form.static_token" type="password" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none" :placeholder="editingId ? '不修改则留空' : 'eyJhbGc...'"/>
              </div>
            </template>

            <!-- api_key 字段 -->
            <template v-if="form.auth_type === 'api_key'">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1.5">Header 名称</label>
                <input v-model="form.api_key_header" :disabled="!!editingId" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none disabled:bg-gray-50 disabled:text-gray-400" placeholder="X-API-Key"/>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1.5">API Key 值 {{ editingId ? '（留空保持不变）' : '*' }}</label>
                <input v-model="form.api_key_value" type="password" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none" :placeholder="editingId ? '不修改则留空' : 'sk-...'"/>
              </div>
            </template>

            <!-- basic 字段 -->
            <template v-if="form.auth_type === 'basic'">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1.5">用户名 <span v-if="!editingId" class="text-red-500">*</span></label>
                  <input v-model="form.username" :disabled="!!editingId" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none disabled:bg-gray-50 disabled:text-gray-400" placeholder="admin"/>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1.5">密码 {{ editingId ? '（留空保持不变）' : '*' }}</label>
                  <input v-model="form.password" type="password" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none" :placeholder="editingId ? '不修改则留空' : '••••••••'"/>
                </div>
              </div>
            </template>

            <p v-if="formErrors.general" class="text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg">{{ formErrors.general }}</p>
          </div>

          <div class="flex gap-3 justify-end mt-6">
            <button @click="closeForm" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors">取消</button>
            <button
              @click="handleSubmit"
              :disabled="submitting"
              class="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {{ submitting ? (editingId ? '保存中...' : '创建中...') : (editingId ? '保存更改' : '创建凭据') }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 删除确认 Modal -->
    <Teleport to="body">
      <div
        v-if="deletingCred"
        class="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        @click.self="deletingCred = null"
      >
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
          <div class="flex items-start gap-3 mb-4">
            <div class="w-9 h-9 rounded-xl bg-red-100 flex items-center justify-center shrink-0">
              <svg class="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
              </svg>
            </div>
            <div>
              <h3 class="text-sm font-semibold text-gray-900 mb-1">确认删除凭据</h3>
              <p class="text-sm text-gray-500">删除「{{ deletingCred.name }}」后，绑定此凭据的 Node 将失去自动鉴权能力，NodeVault 将以无鉴权方式转发请求。</p>
            </div>
          </div>
          <div class="flex gap-3 justify-end">
            <button @click="deletingCred = null" class="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">取消</button>
            <button @click="confirmDelete" :disabled="deleting" class="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors">
              {{ deleting ? '删除中...' : '确认删除' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import {
  listCredentials,
  createCredential,
  updateCredential,
  testCredential,
  deleteCredential,
} from '@/api/credentials'
import type { CredentialResponse, AuthType } from '@/api/credentials'

// ---- state ----

const credentials = ref<CredentialResponse[]>([])
const loading = ref(false)
const testing = reactive<Record<string, boolean>>({})
const testResults = reactive<Record<string, { success: boolean; message: string; latency_ms: number | null }>>({})

const showForm = ref(false)
const editingId = ref<string | null>(null)
const submitting = ref(false)

const form = reactive({
  name: '',
  base_url: '',
  auth_type: 'bearer_login' as AuthType,
  login_endpoint: '',
  login_body_template: '{"username":"{{username}}","password":"{{password}}"}',
  username: '',
  password: '',
  token_json_path: '',
  token_ttl: null as number | null,
  static_token: '',
  api_key_header: 'X-API-Key',
  api_key_value: '',
})

const formErrors = reactive<{ name?: string; base_url?: string; general?: string }>({})

const deletingCred = ref<CredentialResponse | null>(null)
const deleting = ref(false)

// ---- helpers ----

function authTypeLabel(t: AuthType) {
  const m: Record<AuthType, string> = {
    bearer_login: 'Bearer Login',
    bearer_static: 'Bearer Static',
    api_key: 'API Key',
    basic: 'Basic',
  }
  return m[t] ?? t
}

function authTypeColor(t: AuthType) {
  const m: Record<AuthType, string> = {
    bearer_login: 'bg-indigo-100 text-indigo-600',
    bearer_static: 'bg-violet-100 text-violet-600',
    api_key: 'bg-emerald-100 text-emerald-600',
    basic: 'bg-orange-100 text-orange-600',
  }
  return m[t] ?? 'bg-gray-100 text-gray-600'
}

function authTypeBadge(t: AuthType) {
  const m: Record<AuthType, string> = {
    bearer_login: 'bg-indigo-50 text-indigo-600',
    bearer_static: 'bg-violet-50 text-violet-600',
    api_key: 'bg-emerald-50 text-emerald-600',
    basic: 'bg-orange-50 text-orange-600',
  }
  return m[t] ?? 'bg-gray-100 text-gray-500'
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

function resetForm() {
  form.name = ''
  form.base_url = ''
  form.auth_type = 'bearer_login'
  form.login_endpoint = ''
  form.login_body_template = '{"username":"{{username}}","password":"{{password}}"}'
  form.username = ''
  form.password = ''
  form.token_json_path = ''
  form.token_ttl = null
  form.static_token = ''
  form.api_key_header = 'X-API-Key'
  form.api_key_value = ''
  Object.assign(formErrors, { name: undefined, base_url: undefined, general: undefined })
}

// ---- actions ----

async function loadCredentials() {
  loading.value = true
  try {
    const res = await listCredentials()
    credentials.value = res.data
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

function openCreateForm() {
  editingId.value = null
  resetForm()
  showForm.value = true
}

function openEditForm(cred: CredentialResponse) {
  editingId.value = cred.id
  resetForm()
  form.name = cred.name
  form.base_url = cred.base_url
  form.auth_type = cred.auth_type
  form.login_endpoint = cred.login_endpoint ?? ''
  form.token_json_path = cred.token_json_path ?? ''
  form.token_ttl = cred.token_ttl ?? null
  form.api_key_header = cred.api_key_header ?? 'X-API-Key'
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editingId.value = null
}

async function handleSubmit() {
  Object.assign(formErrors, { name: undefined, base_url: undefined, general: undefined })
  if (!form.name.trim()) { formErrors.name = '请输入名称'; return }
  if (!editingId.value && !form.base_url.trim()) { formErrors.base_url = '请输入 Base URL'; return }

  submitting.value = true
  try {
    if (editingId.value) {
      const payload: Record<string, unknown> = { name: form.name }
      if (form.token_ttl != null) payload.token_ttl = form.token_ttl
      if (form.password) payload.password = form.password
      if (form.static_token) payload.static_token = form.static_token
      if (form.api_key_value) payload.api_key_value = form.api_key_value
      await updateCredential(editingId.value, payload)
    } else {
      await createCredential({
        name: form.name,
        base_url: form.base_url,
        auth_type: form.auth_type,
        login_endpoint: form.login_endpoint || undefined,
        login_body_template: form.login_body_template || undefined,
        username: form.username || undefined,
        password: form.password || undefined,
        token_json_path: form.token_json_path || undefined,
        token_ttl: form.token_ttl ?? undefined,
        static_token: form.static_token || undefined,
        api_key_header: form.api_key_header || undefined,
        api_key_value: form.api_key_value || undefined,
      })
    }
    closeForm()
    await loadCredentials()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    formErrors.general = err?.response?.data?.detail || '操作失败，请重试'
  } finally {
    submitting.value = false
  }
}

async function handleTest(id: string) {
  testing[id] = true
  delete testResults[id]
  try {
    const res = await testCredential(id)
    testResults[id] = res.data
    // Auto-clear after 8 seconds
    setTimeout(() => { delete testResults[id] }, 8000)
  } catch {
    testResults[id] = { success: false, message: '请求失败', latency_ms: null }
  } finally {
    testing[id] = false
  }
}

function handleDelete(cred: CredentialResponse) {
  deletingCred.value = cred
}

async function confirmDelete() {
  if (!deletingCred.value) return
  deleting.value = true
  try {
    await deleteCredential(deletingCred.value.id)
    credentials.value = credentials.value.filter(c => c.id !== deletingCred.value!.id)
    deletingCred.value = null
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    alert(err?.response?.data?.detail || '删除失败')
  } finally {
    deleting.value = false
  }
}

onMounted(loadCredentials)
</script>
