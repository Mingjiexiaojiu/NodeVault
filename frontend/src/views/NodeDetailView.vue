<template>
  <div>
    <!-- 加载骨架 -->
    <div v-if="loading" class="space-y-4">
      <div class="h-8 bg-gray-100 rounded w-64 animate-pulse" />
      <div class="h-40 bg-gray-100 rounded animate-pulse" />
    </div>

    <!-- 404 -->
    <div v-else-if="notFound" class="text-center py-20">
      <p class="text-gray-500 mb-4">节点未找到</p>
      <RouterLink to="/nodes">
        <BaseButton variant="secondary">返回列表</BaseButton>
      </RouterLink>
    </div>

    <template v-else-if="node">
      <!-- 操作栏 -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <RouterLink to="/nodes" class="text-gray-400 hover:text-gray-600 transition-colors">
            ← 返回列表
          </RouterLink>
          <span class="text-gray-300">/</span>
          <h1 class="text-xl font-bold text-gray-900">
            {{ node.display_name || node.name }}
          </h1>
        </div>
        <div class="flex items-center gap-2">
          <RouterLink :to="`/nodes/${node.id}/stats`">
            <BaseButton variant="secondary">📊 统计</BaseButton>
          </RouterLink>
          <RouterLink :to="`/nodes/${node.id}/edit`">
            <BaseButton variant="secondary">✏️ 编辑</BaseButton>
          </RouterLink>
          <BaseButton variant="secondary" @click="showExportPanel = !showExportPanel">
            {{ showExportPanel ? '▲ 收起导出' : '📤 导出' }}
          </BaseButton>
          <RouterLink :to="`/nodes/${node.id}/invoke`">
            <BaseButton>调用此节点</BaseButton>
          </RouterLink>
        </div>
      </div>

      <!-- 元信息卡片 -->
      <div class="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <p class="text-xs text-gray-400 mb-1">唯一标识</p>
            <p class="text-sm font-mono text-gray-700">{{ node.name }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">显示名称</p>
            <p class="text-sm text-gray-700">{{ node.display_name || '—' }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">类型</p>
            <TypeBadge :type="node.type" />
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">状态</p>
            <StatusBadge :status="node.status" />
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">分类</p>
            <p class="text-sm text-gray-700">{{ node.category || '—' }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">创建时间</p>
            <p class="text-sm text-gray-700">{{ formatDate(node.created_at) }}</p>
          </div>
          <div class="sm:col-span-2">
            <p class="text-xs text-gray-400 mb-1">描述</p>
            <p class="text-sm text-gray-700">{{ node.description || '暂无描述' }}</p>
          </div>
          <div v-if="node.tags?.length" class="sm:col-span-2">
            <p class="text-xs text-gray-400 mb-2">标签</p>
            <div class="flex flex-wrap gap-2">
              <RouterLink
                v-for="tag in node.tags"
                :key="tag"
                :to="`/tags/${tag}`"
                class="px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full text-xs hover:bg-indigo-100 hover:text-indigo-700 transition-colors"
              >
                {{ tag }}
              </RouterLink>
            </div>
          </div>
        </div>
      </div>

      <!-- 导出面板 -->
      <NodeExportPanel
        v-if="showExportPanel"
        :nodeId="node.id"
        :nodeName="node.name"
        :hasActiveVersion="hasActiveVersion"
        class="mb-6"
      />

      <!-- 版本列表 -->
      <div class="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">版本列表</h2>
          <BaseButton variant="secondary" @click="showVersionForm = !showVersionForm">
            {{ showVersionForm ? '取消' : '+ 新增版本' }}
          </BaseButton>
        </div>

        <!-- 新增版本表单 -->
        <div v-if="showVersionForm" class="mb-5 p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1.5">版本号 *</label>
              <input
                v-model="versionForm.version"
                placeholder="1.0.0"
                class="block w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
            <div class="flex items-end pb-2">
              <label class="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                <input type="checkbox" v-model="versionForm.is_default" class="rounded" />
                设为默认版本
              </label>
            </div>
          </div>
          <div>
            <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1.5">变更日志</label>
            <input
              v-model="versionForm.changelog"
              placeholder="本版本的主要变更内容..."
              class="block w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>
          <div>
            <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1.5">Runtime 配置 (JSON) *</label>
            <textarea
              v-model="versionForm.runtime_config_raw"
              rows="4"
              placeholder='{"type": "http", "endpoint": "https://...", "method": "POST"}'
              class="block w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-mono resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1.5">输入 Schema (JSON)</label>
              <textarea
                v-model="versionForm.input_schema_raw"
                rows="4"
                placeholder='{"type": "object", "properties": {}}'
                class="block w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-mono resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
            <div>
              <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1.5">输出 Schema (JSON)</label>
              <textarea
                v-model="versionForm.output_schema_raw"
                rows="4"
                placeholder='{"type": "object", "properties": {}}'
                class="block w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-mono resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
          </div>
          <p v-if="versionFormError" class="text-red-500 text-xs">{{ versionFormError }}</p>
          <div class="flex justify-end gap-3">
            <BaseButton variant="secondary" @click="showVersionForm = false; versionFormError = ''">取消</BaseButton>
            <BaseButton :disabled="submittingVersion" @click="handleCreateVersion">
              {{ submittingVersion ? '提交中...' : '发布版本' }}
            </BaseButton>
          </div>
        </div>

        <EmptyState v-if="versions.length === 0" description="暂无版本记录" />
        <table v-else class="w-full text-sm">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-2 text-left font-medium text-gray-500">版本号</th>
              <th class="px-4 py-2 text-left font-medium text-gray-500">变更日志</th>
              <th class="px-4 py-2 text-left font-medium text-gray-500">默认</th>
              <th class="px-4 py-2 text-left font-medium text-gray-500">创建时间</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="v in versions" :key="v.id">
              <td class="px-4 py-3 font-mono text-gray-700">
                {{ v.version }}
                <span v-if="v.is_deprecated" class="ml-1 px-1.5 py-0.5 bg-red-100 text-red-600 rounded text-xs">已废弃</span>
              </td>
              <td class="px-4 py-3 text-gray-500 text-xs max-w-xs truncate">{{ v.changelog || '—' }}</td>
              <td class="px-4 py-3">
                <span
                  v-if="v.is_default"
                  class="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-full text-xs font-medium"
                >
                  默认
                </span>
                <button
                  v-else
                  class="text-xs text-gray-400 hover:text-indigo-600 transition-colors"
                  :disabled="settingDefault === v.version"
                  @click="handleSetDefault(v.version)"
                >
                  {{ settingDefault === v.version ? '设置中...' : '设为默认' }}
                </button>
              </td>
              <td class="px-4 py-3 text-gray-400">{{ formatDate(v.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 调用日志 -->
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">最近调用日志</h2>
        <EmptyState v-if="logs.length === 0" description="暂无调用记录" />
        <table v-else class="w-full text-sm">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-2 text-left font-medium text-gray-500">调用时间</th>
              <th class="px-4 py-2 text-left font-medium text-gray-500">状态</th>
              <th class="px-4 py-2 text-left font-medium text-gray-500">耗时 (ms)</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="log in logs" :key="log.id">
              <td class="px-4 py-3 text-gray-500">{{ formatDate(log.created_at) }}</td>
              <td class="px-4 py-3">
                <span
                  :class="[
                    'px-2 py-0.5 rounded-full text-xs font-medium',
                    log.status === 'success'
                      ? 'bg-green-100 text-green-700'
                      : log.status === 'timeout'
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-red-100 text-red-700',
                  ]"
                >
                  {{ log.status }}
                </span>
              </td>
              <td class="px-4 py-3 text-gray-500">{{ log.latency_ms ?? '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue'
import { useRoute } from 'vue-router'
import { getNode, listVersions, getLogs, createVersion, setDefaultVersion } from '@/api/nodes'
import type { NodeItem, NodeVersion, InvocationLog } from '@/api/nodes'
import BaseButton from '@/components/BaseButton.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import TypeBadge from '@/components/TypeBadge.vue'
import EmptyState from '@/components/EmptyState.vue'
import NodeExportPanel from '@/components/NodeExportPanel.vue'

const route = useRoute()
const id = route.params.id as string

const node = ref<NodeItem | null>(null)
const versions = ref<NodeVersion[]>([])
const logs = ref<InvocationLog[]>([])
const loading = ref(true)
const notFound = ref(false)
const showExportPanel = ref(false)

// 版本管理状态
const showVersionForm = ref(false)
const submittingVersion = ref(false)
const versionFormError = ref('')
const settingDefault = ref<string | null>(null)
const versionForm = reactive({
  version: '',
  changelog: '',
  is_default: false,
  runtime_config_raw: '',
  input_schema_raw: '{"type": "object", "properties": {}}',
  output_schema_raw: '{"type": "object", "properties": {}}',
})

const hasActiveVersion = computed(() =>
  versions.value.some(v => v.is_default)
)

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

async function handleCreateVersion() {
  versionFormError.value = ''
  if (!versionForm.version.trim()) {
    versionFormError.value = '版本号不能为空'
    return
  }
  let runtime_config: Record<string, unknown>
  let input_schema: Record<string, unknown>
  let output_schema: Record<string, unknown>
  try {
    runtime_config = JSON.parse(versionForm.runtime_config_raw || '{}')
  } catch {
    versionFormError.value = 'Runtime 配置不是合法的 JSON'
    return
  }
  try {
    input_schema = JSON.parse(versionForm.input_schema_raw || '{}')
  } catch {
    versionFormError.value = '输入 Schema 不是合法的 JSON'
    return
  }
  try {
    output_schema = JSON.parse(versionForm.output_schema_raw || '{}')
  } catch {
    versionFormError.value = '输出 Schema 不是合法的 JSON'
    return
  }
  submittingVersion.value = true
  try {
    await createVersion(id, {
      version: versionForm.version.trim(),
      changelog: versionForm.changelog || undefined,
      is_default: versionForm.is_default,
      runtime_config,
      input_schema,
      output_schema,
    })
    const res = await listVersions(id)
    versions.value = res.data
    showVersionForm.value = false
    versionForm.version = ''
    versionForm.changelog = ''
    versionForm.is_default = false
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    versionFormError.value = err.response?.data?.detail || '发布失败，请检查填写内容'
  } finally {
    submittingVersion.value = false
  }
}

async function handleSetDefault(version: string) {
  settingDefault.value = version
  try {
    await setDefaultVersion(id, version)
    const res = await listVersions(id)
    versions.value = res.data
  } catch {
    // ignore
  } finally {
    settingDefault.value = null
  }
}

onMounted(async () => {
  try {
    const [nodeRes, versionsRes, logsRes] = await Promise.all([
      getNode(id),
      listVersions(id),
      getLogs(id, { page_size: 10 }),
    ])
    node.value = nodeRes.data
    versions.value = versionsRes.data
    logs.value = logsRes.data
    // 预填充 runtime_config 来自最新版本
    if (versionsRes.data.length > 0) {
      const latest = versionsRes.data[versionsRes.data.length - 1]
      versionForm.runtime_config_raw = JSON.stringify(latest.runtime_config, null, 2)
      versionForm.input_schema_raw = JSON.stringify(latest.input_schema, null, 2)
      versionForm.output_schema_raw = JSON.stringify(latest.output_schema, null, 2)
    }
  } catch (e: unknown) {
    const err = e as { response?: { status?: number } }
    if (err.response?.status === 404) {
      notFound.value = true
    }
  } finally {
    loading.value = false
  }
})
</script>
