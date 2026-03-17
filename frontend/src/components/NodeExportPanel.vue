<template>
  <div class="bg-white rounded-2xl border border-gray-200 overflow-hidden">
    <!-- Tab 导航 -->
    <div class="flex border-b border-gray-200 bg-gray-50">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="px-4 py-3 text-xs font-semibold transition-colors border-b-2 -mb-px"
        :class="activeTab === tab.id
          ? 'border-indigo-500 text-indigo-600 bg-white'
          : 'border-transparent text-gray-500 hover:text-gray-700'"
        @click="activeTab = tab.id; loadTab(tab.id)"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 无活跃版本提示 -->
    <div v-if="!hasActiveVersion" class="flex items-center gap-3 px-6 py-8 text-gray-400">
      <svg class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span class="text-sm">暂无活跃版本，无法导出</span>
    </div>

    <template v-else>
      <!-- Skill Package tab -->
      <div v-if="activeTab === 'skill'" class="p-6 flex flex-col items-center gap-3">
        <div class="w-14 h-14 rounded-2xl bg-emerald-50 flex items-center justify-center mb-1">
          <svg class="w-7 h-7 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
        </div>
        <p class="text-sm text-gray-600 text-center">下载包含 <code class="text-indigo-600 font-mono text-xs">skill.yaml</code>、<code class="text-indigo-600 font-mono text-xs">skill.py</code> 和测试的完整 Skill Package</p>
        <button
          class="mt-2 px-6 py-2.5 bg-emerald-600 text-white text-sm font-medium rounded-xl hover:bg-emerald-700 active:scale-95 transition-all"
          @click="handleDownloadZip"
        >
          下载 ZIP
        </button>
      </div>

      <!-- 文本格式 tab -->
      <div v-else class="relative">
        <div v-if="loading" class="px-6 py-8 flex items-center justify-center">
          <div class="h-4 w-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
          <span class="ml-2 text-sm text-gray-400">加载中...</span>
        </div>
        <div v-else-if="loadError" class="px-6 py-6 text-sm text-red-500">{{ loadError }}</div>
        <template v-else>
          <!-- 复制按钮 -->
          <button
            class="absolute top-3 right-3 px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors"
            :class="copied
              ? 'bg-green-50 border-green-200 text-green-600'
              : 'bg-white border-gray-200 text-gray-500 hover:border-indigo-300 hover:text-indigo-600'"
            @click="handleCopy"
          >
            {{ copied ? '已复制 ✓' : '复制' }}
          </button>
          <pre class="overflow-x-auto p-5 pt-4 text-xs leading-relaxed font-mono text-gray-700 max-h-96"><code>{{ content }}</code></pre>
        </template>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { exportNodeOpenAI, exportNodeLangChain, exportNodeMCP, downloadNodeSkillZip } from '@/api/nodes'

const props = defineProps<{
  nodeId: string
  nodeName: string
  hasActiveVersion: boolean
}>()

type TabId = 'openai' | 'langchain' | 'mcp' | 'skill'

const tabs = [
  { id: 'openai' as TabId, label: 'OpenAI' },
  { id: 'langchain' as TabId, label: 'LangChain' },
  { id: 'mcp' as TabId, label: 'MCP' },
  { id: 'skill' as TabId, label: 'Skill Package' },
]

const activeTab = ref<TabId>('openai')
const content = ref('')
const loading = ref(false)
const loadError = ref('')
const copied = ref(false)
const loaded = new Set<TabId>()

async function loadTab(tab: TabId) {
  if (tab === 'skill' || loaded.has(tab) || !props.hasActiveVersion) return
  loading.value = true
  loadError.value = ''
  try {
    if (tab === 'openai') {
      const res = await exportNodeOpenAI(props.nodeId)
      content.value = JSON.stringify(res.data, null, 2)
    } else if (tab === 'langchain') {
      const res = await exportNodeLangChain(props.nodeId)
      content.value = typeof res.data === 'string' ? res.data : JSON.stringify(res.data, null, 2)
    } else if (tab === 'mcp') {
      const res = await exportNodeMCP(props.nodeId)
      content.value = JSON.stringify(res.data, null, 2)
    }
    loaded.add(tab)
  } catch {
    loadError.value = '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function handleCopy() {
  try {
    await navigator.clipboard.writeText(content.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // fallback: create temp textarea
    const el = document.createElement('textarea')
    el.value = content.value
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  }
}

function handleDownloadZip() {
  downloadNodeSkillZip(props.nodeId, props.nodeName)
}

// 面板首次显示时自动加载 OpenAI tab
watch(
  () => props.hasActiveVersion,
  (v) => { if (v) loadTab('openai') },
  { immediate: true },
)
</script>
