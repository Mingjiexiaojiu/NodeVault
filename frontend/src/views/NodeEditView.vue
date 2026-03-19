<template>
  <div class="min-h-screen -m-6 bg-gray-50">
    <div class="max-w-2xl mx-auto px-8 py-8">

      <div v-if="loadingNode" class="space-y-4">
        <div class="h-8 bg-gray-100 rounded w-48 animate-pulse" />
        <div class="h-64 bg-gray-100 rounded animate-pulse" />
      </div>

      <template v-else-if="node">
        <h1 class="text-xl font-bold text-gray-900 mb-1">编辑节点</h1>
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

            <div class="grid grid-cols-2 gap-4">
              <div class="flex flex-col gap-1.5">
                <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">类型</label>
                <select
                  v-model="form.type"
                  class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors appearance-none"
                >
                  <option v-for="t in nodeTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
                </select>
              </div>
              <div class="flex flex-col gap-1.5">
                <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">分类</label>
                <input
                  v-model="form.category"
                  placeholder="finance"
                  class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
                />
              </div>
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

            <!-- 技能集 -->
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">技能集</label>
              <select
                v-model="form.skill_id"
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors appearance-none cursor-pointer"
              >
                <option value="">不归属任何技能集</option>
                <option v-for="sk in skills" :key="sk.id" :value="sk.id">
                  {{ sk.display_name || sk.name }}
                </option>
              </select>
            </div>

            <!-- 用途提示 -->
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">用途提示 (usage_hint)</label>
              <textarea
                v-model="form.usage_hint"
                placeholder="向 AI 解释该节点的具体调用场景..."
                rows="2"
                maxlength="500"
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
              />
              <p class="text-xs text-gray-400 text-right">{{ (form.usage_hint || '').length }}/500</p>
            </div>
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
import { getSkills } from '@/api/skills'
import type { NodeItem, NodeType, NodeStatus } from '@/api/nodes'
import type { SkillItem } from '@/api/skills'
import BaseButton from '@/components/BaseButton.vue'

const route = useRoute()
const router = useRouter()
const nodeId = route.params.id as string

const node = ref<NodeItem | null>(null)
const loadingNode = ref(true)
const saving = ref(false)
const submitError = ref('')
const skills = ref<SkillItem[]>([])

const form = reactive({
  display_name: '',
  description: '',
  type: '' as NodeType,
  category: '',
  status: '' as NodeStatus,
  skill_id: '',
  usage_hint: '',
})
const tagsRaw = ref('')

const nodeTypes = [
  { value: 'data_cleaning', label: '数据清洗' },
  { value: 'analysis', label: '分析' },
  { value: 'risk', label: '风控' },
  { value: 'nlp', label: 'NLP' },
  { value: 'vision', label: '视觉' },
  { value: 'ml', label: '机器学习' },
  { value: 'tool', label: '工具' },
  { value: 'utility', label: '实用程序' },
]

const nodeStatuses: { value: NodeStatus; label: string; icon: string }[] = [
  { value: 'draft', label: '草稿', icon: '📝' },
  { value: 'active', label: '活跃', icon: '✅' },
  { value: 'deprecated', label: '弃用', icon: '⚠️' },
  { value: 'archived', label: '归档', icon: '📦' },
]

onMounted(async () => {
  try {
    const [nodeRes, skillList] = await Promise.all([
      getNode(nodeId),
      getSkills().catch(() => [] as SkillItem[]),
    ])
    node.value = nodeRes.data
    form.display_name = nodeRes.data.display_name || ''
    form.description = nodeRes.data.description || ''
    form.type = nodeRes.data.type
    form.category = nodeRes.data.category || ''
    form.status = nodeRes.data.status
    form.skill_id = nodeRes.data.skill_id || ''
    form.usage_hint = nodeRes.data.usage_hint || ''
    tagsRaw.value = (nodeRes.data.tags ?? []).join(', ')
    skills.value = skillList
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
      type: form.type,
      category: form.category || undefined,
      status: form.status,
      skill_id: form.skill_id || undefined,
      usage_hint: form.usage_hint || undefined,
      tags,
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
