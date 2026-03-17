<template>
  <div class="max-w-4xl">
    <!-- 标题 -->
    <div class="flex items-center gap-3 mb-6">
      <RouterLink :to="`/nodes/${nodeId}`" class="text-gray-400 hover:text-gray-600 transition-colors">
        ← 返回详情
      </RouterLink>
      <span class="text-gray-300">/</span>
      <h1 class="text-xl font-bold text-gray-900">
        调用节点：{{ node?.display_name || node?.name || nodeId }}
      </h1>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 左侧：输入面板 -->
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <h2 class="text-base font-semibold text-gray-900 mb-4">调用参数</h2>

        <!-- 版本选择 -->
        <div class="mb-4">
          <label class="text-sm font-medium text-gray-700 mb-1 block">选择版本</label>
          <select
            v-model="selectedVersion"
            class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option :value="null">默认版本</option>
            <option v-for="v in versions" :key="v.id" :value="v.version">
              {{ v.version }}{{ v.is_default ? ' (默认)' : '' }}
            </option>
          </select>
        </div>

        <!-- JSON 输入 -->
        <JsonEditor
          v-model="inputRaw"
          label="Input (JSON)"
          @valid="(v: unknown) => { parsedInput = v; inputError = false }"
        />
        <p v-if="inputError" class="text-xs text-red-500 mt-1">请修正 JSON 格式错误后再提交</p>

        <div class="mt-6">
          <BaseButton
            :loading="invoking"
            :disabled="inputError"
            class="w-full"
            @click="handleInvoke"
          >
            发起调用
          </BaseButton>
        </div>
      </div>

      <!-- 右侧：结果面板 -->
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <h2 class="text-base font-semibold text-gray-900 mb-4">调用结果</h2>

        <!-- 错误 -->
        <div v-if="invokeError" class="bg-red-50 border border-red-200 rounded-md p-4 text-sm text-red-700">
          {{ invokeError }}
        </div>

        <!-- 空状态 -->
        <div
          v-else-if="!result"
          class="flex items-center justify-center h-48 text-gray-400 text-sm"
        >
          点击"发起调用"查看结果
        </div>

        <!-- 结果 -->
        <div v-else class="space-y-4">
          <div class="flex items-center gap-4 text-sm text-gray-500">
            <span>
              状态：
              <span
                :class="result.status === 'success' ? 'text-green-600 font-medium' : 'text-red-600 font-medium'"
              >
                {{ result.status }}
              </span>
            </span>
            <span v-if="result.latency_ms != null">耗时：{{ result.latency_ms }} ms</span>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Invocation ID</p>
            <p class="font-mono text-xs text-gray-500">{{ result.invocation_id }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-2">输出</p>
            <pre
              class="bg-gray-50 border border-gray-200 rounded-md p-4 text-xs font-mono overflow-auto max-h-72 whitespace-pre-wrap break-all"
            >{{ JSON.stringify(result.output, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getNode, listVersions, invokeNode } from '@/api/nodes'
import type { NodeItem, NodeVersion, InvokeResult } from '@/api/nodes'
import BaseButton from '@/components/BaseButton.vue'
import JsonEditor from '@/components/JsonEditor.vue'

const route = useRoute()
const nodeId = route.params.id as string

const node = ref<NodeItem | null>(null)
const versions = ref<NodeVersion[]>([])
const selectedVersion = ref<string | null>(null)
const inputRaw = ref('{}')
const parsedInput = ref<unknown>({})
const inputError = ref(false)
const invoking = ref(false)
const result = ref<InvokeResult | null>(null)
const invokeError = ref('')

onMounted(async () => {
  const [nodeRes, versionsRes] = await Promise.all([
    getNode(nodeId),
    listVersions(nodeId),
  ])
  node.value = nodeRes.data
  versions.value = versionsRes.data
})

async function handleInvoke() {
  invokeError.value = ''
  result.value = null
  invoking.value = true
  try {
    const payload: { input: unknown; version?: string } = { input: parsedInput.value }
    if (selectedVersion.value) payload.version = selectedVersion.value
    const res = await invokeNode(nodeId, payload)
    result.value = res.data
  } catch (e: unknown) {
    const err = e as { response?: { status?: number; data?: { error?: { message?: string } } } }
    if (err.response?.status === 502) {
      invokeError.value = '上游服务无响应（502 Bad Gateway），请检查节点 Endpoint 是否可用'
    } else if (err.response?.status === 408 || err.response?.status === 504) {
      invokeError.value = '调用超时，请稍后重试'
    } else if (err.response?.data?.error?.message) {
      invokeError.value = err.response.data.error.message
    } else {
      invokeError.value = '调用失败，请稍后重试'
    }
  } finally {
    invoking.value = false
  }
}
</script>
