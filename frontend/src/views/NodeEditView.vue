<template>
  <div class="min-h-screen -m-6 bg-gray-50">
    <div class="max-w-2xl mx-auto px-8 py-8">

      <div v-if="loadingNode" class="space-y-4">
        <div class="h-8 bg-gray-100 rounded w-48 animate-pulse" />
        <div class="h-64 bg-gray-100 rounded animate-pulse" />
      </div>

      <template v-else-if="node">
        <h1 class="text-xl font-semibold text-gray-900 mb-1">编辑节点</h1>
        <p class="text-sm text-gray-400 font-mono mb-6">{{ node.name }}</p>

        <form class="space-y-5" @submit.prevent="handleSubmit">
          <!-- 显示名称 -->
          <div class="bg-white rounded-2xl border border-gray-200 p-6 space-y-4">
            <h2 class="text-sm font-semibold text-gray-700">基本信息</h2>

            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">显示名称</label>
              <input
                v-model="form.display_name"
                placeholder="我的算法 V1"
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
              />
            </div>

            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">描述</label>
              <textarea
                v-model="form.description"
                rows="3"
                placeholder="简要描述该节点的功能..."
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
              />
            </div>

            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">分类</label>
              <select
                v-model="form.category_id"
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors appearance-none cursor-pointer"
              >
                <option value="" disabled>请选择分类</option>
                <option v-for="c in categoryList" :key="c.id" :value="c.id">{{ c.display_name }}</option>
              </select>
            </div>

            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">标签</label>
              <input
                v-model="tagsRaw"
                placeholder="tag1, tag2, tag3"
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
              />
              <p class="text-xs text-gray-400">多个标签用英文逗号分隔</p>
            </div>

          </div>

          <!-- 凭据绑定 -->
          <div class="bg-white rounded-2xl border border-gray-200 p-6">
            <h2 class="text-sm font-semibold text-gray-700 mb-1">服务凭据</h2>
            <p class="text-xs text-gray-400 mb-3">绑定后调用此 Node 时自动附加鉴权头。未绑定则按 base_url 前缀自动匹配。</p>
            <select
              v-model="form.credential_id"
              class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors appearance-none cursor-pointer"
            >
              <option :value="null">不绑定（使用自动匹配）</option>
              <option v-for="cred in credentials" :key="cred.id" :value="cred.id">
                {{ cred.name }} — {{ cred.base_url }} ({{ cred.auth_type }})
              </option>
            </select>
          </div>

          <!-- 状态 -->
          <div class="bg-white rounded-2xl border border-gray-200 p-6">
            <h2 class="text-sm font-semibold text-gray-700 mb-4">发布状态</h2>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <button
                v-for="s in nodeStatuses"
                :key="s.value"
                type="button"
                class="flex flex-col items-center gap-1 py-3 px-2 rounded-xl border-2 text-xs font-medium transition-all"
                :class="form.status === s.value
                  ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                  : 'border-gray-200 text-gray-500 hover:border-gray-300'"
                @click="form.status = s.value"
              >
                <span class="text-base">{{ s.icon }}</span>
                {{ s.label }}
              </button>
            </div>
          </div>

          <!-- 错误提示 -->
          <div
            v-if="submitError"
            class="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl px-4 py-3"
          >
            <svg class="w-5 h-5 text-red-500 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            <p class="text-sm text-red-700">{{ submitError }}</p>
          </div>

          <div class="flex justify-center pb-8">
            <BaseButton type="submit" :loading="saving" class="px-10 py-3 text-base shadow-lg shadow-indigo-200">
              <svg v-if="!saving" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              保存修改
            </BaseButton>
          </div>
        </form>
      </template>
    </div>

    <!-- 悬浮返回球 由 AppLayout 提供 -->
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getNode, updateNode } from '@/api/nodes'
import { listCategories } from '@/api/categories'
import type { Category } from '@/api/categories'
import type { NodeItem, NodeStatus } from '@/api/nodes'
import BaseButton from '@/components/BaseButton.vue'
import { listCredentials } from '@/api/credentials'
import type { CredentialResponse } from '@/api/credentials'

const route = useRoute()
const router = useRouter()
const nodeId = route.params.id as string

const node = ref<NodeItem | null>(null)
const loadingNode = ref(true)
const saving = ref(false)
const submitError = ref('')
const categoryList = ref<Category[]>([])
const credentials = ref<CredentialResponse[]>([])

const form = reactive({
  display_name: '',
  description: '',
  category_id: '',
  status: '' as NodeStatus,
  credential_id: null as string | null,
})
const tagsRaw = ref('')

const nodeStatuses: { value: NodeStatus; label: string; icon: string }[] = [
  { value: 'draft', label: '草稿', icon: '📝' },
  { value: 'active', label: '活跃', icon: '✅' },
  { value: 'deprecated', label: '弃用', icon: '⚠️' },
  { value: 'archived', label: '归档', icon: '📦' },
]

onMounted(async () => {
  try {
    const [nodeRes, catRes, credRes] = await Promise.all([
      getNode(nodeId),
      listCategories().catch(() => ({ data: [] as Category[] })),
      listCredentials().catch(() => ({ data: [] as CredentialResponse[] })),
    ])
    node.value = nodeRes.data
    form.display_name = nodeRes.data.display_name || ''
    form.description = nodeRes.data.description || ''
    form.category_id = nodeRes.data.category_id || ''
    form.status = nodeRes.data.status
    form.credential_id = nodeRes.data.credential_id ?? null
    tagsRaw.value = (nodeRes.data.tags ?? []).join(', ')
    categoryList.value = catRes.data
    credentials.value = credRes.data
  } finally {
    loadingNode.value = false
  }
})

async function handleSubmit() {
  submitError.value = ''
  saving.value = true
  try {
    const tags = tagsRaw.value
      ? tagsRaw.value.split(',').map(t => t.trim()).filter(Boolean)
      : []

    await updateNode(nodeId, {
      display_name: form.display_name || undefined,
      description: form.description || undefined,
      category_id: form.category_id || undefined,
      status: form.status,
      tags,
      credential_id: form.credential_id,
    })
    router.push(`/nodes/${nodeId}`)
  } catch (e: unknown) {
    const err = e as { uiMessage?: string }
    submitError.value = err.uiMessage ?? '保存失败，请稍后重试'
  } finally {
    saving.value = false
  }
}
</script>
