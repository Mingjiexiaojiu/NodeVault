<template>
  <div class="space-y-6">
    <!-- 页头 -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-semibold text-gray-900">AI 提供商配置</h1>
        <p class="text-sm text-gray-400 mt-0.5">管理用于 AI 生成的模型提供商，可在生成 SKILL.md 时选择使用。</p>
      </div>
      <button
        class="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-xl hover:bg-indigo-700 active:scale-95 transition-all shadow-sm shadow-indigo-200"
        @click="openCreate"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        新增配置
      </button>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="space-y-3">
      <div v-for="i in 2" :key="i" class="h-24 bg-gray-100 rounded-xl animate-pulse" />
    </div>

    <!-- 空状态 -->
    <div v-else-if="configs.length === 0" class="bg-white rounded-2xl border border-dashed border-gray-200 py-16 text-center">
      <svg class="w-10 h-10 mx-auto text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
      <p class="text-sm text-gray-400">还没有 AI 配置</p>
      <p class="text-xs text-gray-400 mt-1">点击「新增配置」添加你的第一个 AI 提供商</p>
    </div>

    <!-- 配置列表 -->
    <div v-else class="space-y-3">
      <div
        v-for="cfg in configs"
        :key="cfg.id"
        class="bg-white rounded-2xl border border-gray-200 p-5 flex items-center justify-between gap-4 hover:border-indigo-200 transition-colors"
      >
        <div class="flex items-center gap-4 min-w-0">
          <!-- 提供商图标 -->
          <div
            class="w-10 h-10 rounded-xl flex items-center justify-center text-base font-bold shrink-0"
            :class="providerIconClass(cfg.provider)"
          >
            {{ providerIcon(cfg.provider) }}
          </div>
          <div class="min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-sm font-semibold text-gray-900">{{ cfg.name }}</span>
              <span
                v-if="cfg.is_default"
                class="text-[10px] px-1.5 py-0.5 rounded-full bg-indigo-50 text-indigo-600 border border-indigo-200"
              >
                默认
              </span>
            </div>
            <div class="flex items-center gap-3 mt-0.5 text-xs text-gray-400 flex-wrap">
              <span class="capitalize">{{ providerLabel(cfg.provider) }}</span>
              <span class="font-mono">{{ cfg.model }}</span>
              <span class="font-mono">{{ cfg.api_key_masked }}</span>
              <span v-if="cfg.base_url" class="font-mono text-gray-300 truncate max-w-[180px]">{{ cfg.base_url }}</span>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <button
            class="text-xs px-3 py-1.5 text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            @click="openEdit(cfg)"
          >
            编辑
          </button>
          <button
            class="text-xs px-3 py-1.5 text-red-500 border border-red-100 rounded-lg hover:bg-red-50 transition-colors"
            @click="handleDelete(cfg.id)"
          >
            删除
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- 新增 / 编辑 Modal -->
  <Teleport to="body">
    <div
      v-if="showModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
      @click.self="showModal = false"
    >
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 class="text-base font-semibold text-gray-900">{{ editingId ? '编辑配置' : '新增 AI 配置' }}</h3>
          <button class="text-gray-400 hover:text-gray-600" @click="showModal = false">✕</button>
        </div>
        <div class="px-6 py-5 space-y-4">
          <!-- 名称 -->
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-gray-600">名称 <span class="text-red-500">*</span></label>
            <input
              v-model="form.name"
              placeholder="例如：我的 GPT-4o"
              class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:bg-white"
            />
          </div>

          <!-- 提供商 -->
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-gray-600">提供商 <span class="text-red-500">*</span></label>
            <select
              v-model="form.provider"
              class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:bg-white"
            >
              <option value="openai">OpenAI（官方 / Azure OpenAI）</option>
              <option value="claude">Anthropic Claude</option>
              <option value="custom">自定义（OpenAI 兼容接口）</option>
            </select>
          </div>

          <!-- 模型 -->
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-gray-600">模型名称 <span class="text-red-500">*</span></label>
            <input
              v-model="form.model"
              :placeholder="modelPlaceholder"
              class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:bg-white"
            />
          </div>

          <!-- API Key + 测试按钮 -->
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-gray-600">
              API Key <span class="text-red-500">*</span>
            </label>
            <div class="flex gap-2">
              <input
                v-model="form.api_key"
                type="password"
                :placeholder="editingId ? '留空则不更改' : 'sk-...'"
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:bg-white"
              />
              <!-- 测试按钮 -->
              <button
                v-if="showTestButton"
                type="button"
                :disabled="testState === 'testing' || !canTest"
                @click="handleTest"
                class="shrink-0 px-3 py-2 text-xs font-medium rounded-lg border transition-colors disabled:cursor-not-allowed"
                :class="testButtonClass"
              >
                <span v-if="testState === 'testing'" class="flex items-center gap-1.5">
                  <svg class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                  </svg>
                  测试中
                </span>
                <span v-else-if="testState === 'success'" class="flex items-center gap-1">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/>
                  </svg>
                  已通过
                </span>
                <span v-else-if="testState === 'failed'" class="flex items-center gap-1">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                  重新测试
                </span>
                <span v-else>测试连接</span>
              </button>
            </div>

            <!-- 测试结果提示 -->
            <div v-if="testState === 'success' && testResult" class="flex items-center gap-1.5 text-xs text-green-600">
              <svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              连接成功，响应时间 {{ testResult.latency_ms }}ms
            </div>
            <div v-else-if="testState === 'failed' && testResult" class="flex items-start gap-1.5 text-xs text-red-500">
              <svg class="w-3.5 h-3.5 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              {{ testResult.message || '测试失败，请检查配置' }}
            </div>
            <!-- 新建配置的提示 -->
            <p v-else-if="!editingId && testState === 'idle'" class="text-xs text-amber-600">
              需先通过连接测试才能保存
            </p>
          </div>

          <!-- Base URL（openai / custom 需要时可选） -->
          <div v-if="form.provider === 'openai' || form.provider === 'custom'" class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-gray-600">
              Base URL
              <span v-if="form.provider === 'custom'" class="text-red-500">*</span>
              <span v-else class="text-gray-400 ml-1">（留空使用官方地址）</span>
            </label>
            <input
              v-model="form.base_url"
              placeholder="https://api.openai.com/v1"
              class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:bg-white"
            />
          </div>

          <!-- 设为默认 -->
          <label class="flex items-center gap-2 cursor-pointer select-none">
            <input
              v-model="form.is_default"
              type="checkbox"
              class="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            <span class="text-sm text-gray-600">设为默认 AI 配置</span>
          </label>

          <!-- 错误提示 -->
          <p v-if="modalError" class="text-xs text-red-500">{{ modalError }}</p>
        </div>
        <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
          <button class="px-4 py-2 text-sm text-gray-600 hover:text-gray-900" @click="showModal = false">取消</button>
          <button
            class="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            :disabled="!canSave"
            @click="handleSubmit"
          >
            {{ submitting ? '保存中...' : (editingId ? '保存' : '创建') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  getAIConfigs,
  createAIConfig,
  updateAIConfig,
  deleteAIConfig,
  testAIConfig,
} from '@/api/ai-config'
import type { AIConfigItem, AIConfigTestResult, AIProvider } from '@/api/ai-config'

const configs = ref<AIConfigItem[]>([])
const loading = ref(true)
const showModal = ref(false)
const editingId = ref<string | null>(null)
const submitting = ref(false)
const modalError = ref('')

// 测试状态
type TestState = 'idle' | 'testing' | 'success' | 'failed'
const testState = ref<TestState>('idle')
const testResult = ref<AIConfigTestResult | null>(null)

const form = reactive({
  name: '',
  provider: 'openai' as AIProvider,
  model: '',
  api_key: '',
  base_url: '',
  is_default: false,
})

// 当影响连接的字段变化时，重置测试状态
watch(
  () => [form.api_key, form.model, form.base_url, form.provider],
  () => {
    testState.value = 'idle'
    testResult.value = null
  },
)

// 是否显示测试按钮：新建时有 api_key；编辑时 api_key 有值（表示要更改）
const showTestButton = computed(() => {
  if (!editingId.value) return true         // 新建：始终显示
  return form.api_key.trim().length > 0     // 编辑：只有填了新 key 才显示
})

// 测试按钮是否可点击
const canTest = computed(
  () => form.model.trim().length > 0 && form.api_key.trim().length > 0,
)

// 是否允许保存
const canSave = computed(() => {
  if (submitting.value) return false
  // 编辑模式且未填入新 api_key → 无需测试，直接允许保存
  if (editingId.value && !form.api_key.trim()) return true
  // 其他情况需通过测试
  return testState.value === 'success'
})

// 测试按钮样式
const testButtonClass = computed(() => {
  if (testState.value === 'success')
    return 'border-green-200 bg-green-50 text-green-700 hover:bg-green-100'
  if (testState.value === 'failed')
    return 'border-red-200 bg-red-50 text-red-600 hover:bg-red-100'
  if (testState.value === 'testing')
    return 'border-gray-200 bg-gray-50 text-gray-400'
  return 'border-indigo-200 bg-indigo-50 text-indigo-600 hover:bg-indigo-100'
})

const modelPlaceholder = computed(() => {
  if (form.provider === 'openai') return 'gpt-4o'
  if (form.provider === 'claude') return 'claude-opus-4-5'
  return 'your-model-name'
})

onMounted(async () => {
  await refresh()
})

async function refresh() {
  loading.value = true
  try {
    configs.value = await getAIConfigs()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, { name: '', provider: 'openai', model: '', api_key: '', base_url: '', is_default: false })
  modalError.value = ''
  testState.value = 'idle'
  testResult.value = null
  showModal.value = true
}

function openEdit(cfg: AIConfigItem) {
  editingId.value = cfg.id
  Object.assign(form, {
    name: cfg.name,
    provider: cfg.provider,
    model: cfg.model,
    api_key: '',
    base_url: cfg.base_url ?? '',
    is_default: cfg.is_default,
  })
  modalError.value = ''
  testState.value = 'idle'
  testResult.value = null
  showModal.value = true
}

async function handleTest() {
  if (!canTest.value) return
  modalError.value = ''
  testState.value = 'testing'
  testResult.value = null
  try {
    const result = await testAIConfig({
      provider: form.provider,
      model: form.model,
      api_key: form.api_key,
      base_url: form.base_url || undefined,
    })
    testResult.value = result
    testState.value = result.ok ? 'success' : 'failed'
  } catch (e: unknown) {
    const err = e as { uiMessage?: string }
    testResult.value = { ok: false, message: err.uiMessage || '测试请求失败，请稍后重试' }
    testState.value = 'failed'
  }
}

async function handleSubmit() {
  modalError.value = ''
  if (!form.name.trim()) { modalError.value = '请填写名称'; return }
  if (!form.model.trim()) { modalError.value = '请填写模型名称'; return }
  if (!editingId.value && !form.api_key.trim()) { modalError.value = '请填写 API Key'; return }
  if (form.provider === 'custom' && !form.base_url.trim()) { modalError.value = '自定义提供商需要填写 Base URL'; return }

  submitting.value = true
  try {
    if (editingId.value) {
      const payload: Record<string, unknown> = {
        name: form.name,
        provider: form.provider,
        model: form.model,
        base_url: form.base_url || undefined,
        is_default: form.is_default,
      }
      if (form.api_key.trim()) payload.api_key = form.api_key
      await updateAIConfig(editingId.value, payload)
    } else {
      await createAIConfig({
        name: form.name,
        provider: form.provider,
        model: form.model,
        api_key: form.api_key,
        base_url: form.base_url || undefined,
        is_default: form.is_default,
      })
    }
    showModal.value = false
    await refresh()
  } catch (e: unknown) {
    const err = e as { uiMessage?: string; response?: { data?: { detail?: string; error?: { message?: string } } } }
    modalError.value =
      err.uiMessage ||
      err.response?.data?.error?.message ||
      err.response?.data?.detail ||
      '操作失败，请重试'
  } finally {
    submitting.value = false
  }
}

async function handleDelete(id: string) {
  if (!confirm('确定删除此 AI 配置？')) return
  try {
    await deleteAIConfig(id)
    await refresh()
  } catch {
    alert('删除失败，请稍后重试')
  }
}

function providerLabel(p: AIProvider) {
  if (p === 'openai') return 'OpenAI'
  if (p === 'claude') return 'Claude'
  return '自定义'
}

function providerIcon(p: AIProvider) {
  if (p === 'openai') return 'O'
  if (p === 'claude') return 'A'
  return '⚙'
}

function providerIconClass(p: AIProvider) {
  if (p === 'openai') return 'bg-teal-50 text-teal-600'
  if (p === 'claude') return 'bg-orange-50 text-orange-600'
  return 'bg-gray-50 text-gray-500'
}
</script>
