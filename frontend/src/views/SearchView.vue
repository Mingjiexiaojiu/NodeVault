<template>
  <div>
    <!-- 搜索头 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900 mb-4">搜索节点</h1>
      <div class="flex gap-3">
        <div class="relative flex-1">
          <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0" />
            </svg>
          </div>
          <input
            v-model="query"
            type="text"
            placeholder="搜索节点名称、描述..."
            class="block w-full rounded-xl border border-gray-200 bg-white pl-10 pr-4 py-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 transition-colors"
            @keyup.enter="doSearch(1)"
          />
        </div>
        <button
          class="px-5 py-3 bg-indigo-600 text-white text-sm font-medium rounded-xl hover:bg-indigo-700 transition-colors shadow-sm shadow-indigo-200"
          @click="doSearch(1)"
        >
          搜索
        </button>
      </div>
    </div>

    <!-- 筛选 & 排序 -->
    <div class="flex flex-wrap items-center gap-3 mb-5">
      <div class="flex items-center gap-2">
        <label class="text-xs text-gray-500">类型</label>
        <select
          v-model="filterType"
          class="text-sm border border-gray-200 rounded-lg px-2.5 py-1.5 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-400"
          @change="doSearch(1)"
        >
          <option value="">全部</option>
          <option v-for="t in nodeTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
      </div>
      <div class="flex items-center gap-2">
        <label class="text-xs text-gray-500">排序</label>
        <select
          v-model="sortBy"
          class="text-sm border border-gray-200 rounded-lg px-2.5 py-1.5 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-400"
          @change="doSearch(1)"
        >
          <option value="relevance">相关度</option>
          <option value="latest">最新</option>
          <option value="popular">最热</option>
        </select>
      </div>

      <!-- 热门标签 -->
      <div v-if="popularTags.length" class="flex flex-wrap gap-1.5 ml-auto">
        <button
          v-for="t in popularTags.slice(0, 8)"
          :key="t.tag"
          class="px-2.5 py-1 rounded-full text-xs border transition-colors"
          :class="selectedTag === t.tag
            ? 'bg-indigo-600 text-white border-indigo-600'
            : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300 hover:text-indigo-600'"
          @click="toggleTag(t.tag)"
        >
          {{ t.tag }}
          <span class="opacity-60 ml-0.5">{{ t.node_count }}</span>
        </button>
      </div>
    </div>

    <!-- 结果 -->
    <div v-if="searching" class="space-y-3">
      <div v-for="i in 4" :key="i" class="h-16 bg-gray-100 rounded-xl animate-pulse" />
    </div>

    <div v-else-if="!hasSearched" class="text-center py-20 text-gray-400">
      <svg class="w-12 h-12 mx-auto mb-3 text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0" />
      </svg>
      <p class="text-sm">输入关键词开始搜索</p>
    </div>

    <div v-else-if="results.length === 0" class="text-center py-20 text-gray-400">
      <svg class="w-12 h-12 mx-auto mb-3 text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p class="text-sm">未找到匹配的节点</p>
    </div>

    <div v-else>
      <p class="text-xs text-gray-400 mb-3">共找到 {{ total }} 个节点</p>
      <div class="space-y-2">
        <RouterLink
          v-for="node in results"
          :key="node.id"
          :to="`/nodes/${node.id}`"
          class="flex items-center justify-between bg-white rounded-xl border border-gray-200 px-5 py-4 hover:border-indigo-200 hover:shadow-sm transition-all group"
        >
          <div class="flex items-center gap-4 min-w-0">
            <TypeBadge :type="node.type" />
            <div class="min-w-0">
              <p class="text-sm font-medium text-gray-900 group-hover:text-indigo-600 transition-colors">
                {{ node.display_name || node.name }}
              </p>
              <p class="text-xs text-gray-400 font-mono truncate">{{ node.name }}</p>
            </div>
          </div>
          <div class="flex items-center gap-3 shrink-0 ml-4">
      <!-- 结果卡片中的标签改为可点击链接 -->
              <div v-if="node.tags?.length" class="hidden sm:flex gap-1">
              <RouterLink
                v-for="tag in node.tags.slice(0, 3)"
                :key="tag"
                :to="`/tags/${tag}`"
                class="px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full text-xs hover:bg-indigo-100 hover:text-indigo-700 transition-colors"
                @click.stop
              >{{ tag }}</RouterLink>
            </div>
            <StatusBadge :status="node.status" />
            <svg class="w-4 h-4 text-gray-300 group-hover:text-indigo-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </RouterLink>
      </div>

      <!-- 分页 -->
      <div v-if="totalPages > 1" class="flex justify-center gap-1 mt-6">
        <button
          v-for="p in totalPages"
          :key="p"
          class="w-8 h-8 rounded-lg text-sm transition-colors"
          :class="p === currentPage
            ? 'bg-indigo-600 text-white'
            : 'text-gray-500 hover:bg-gray-100'"
          @click="doSearch(p)"
        >{{ p }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { searchNodes, getPopularTags } from '@/api/nodes'
import type { NodeItem, TagItem } from '@/api/nodes'
import TypeBadge from '@/components/TypeBadge.vue'
import StatusBadge from '@/components/StatusBadge.vue'

const query = ref('')
const filterType = ref('')
const sortBy = ref<'relevance' | 'latest' | 'popular'>('relevance')
const selectedTag = ref('')

const results = ref<NodeItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const searching = ref(false)
const hasSearched = ref(false)
const popularTags = ref<TagItem[]>([])

const totalPages = computed(() => Math.ceil(total.value / pageSize))

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

function toggleTag(tag: string) {
  selectedTag.value = selectedTag.value === tag ? '' : tag
  doSearch(1)
}

async function doSearch(page: number) {
  searching.value = true
  hasSearched.value = true
  currentPage.value = page
  try {
    const params: Record<string, unknown> = {
      q: query.value,
      sort: sortBy.value,
      page,
      page_size: pageSize,
    }
    if (filterType.value) params.type = filterType.value
    if (selectedTag.value) params.tags = [selectedTag.value]

    const res = await searchNodes(params as Parameters<typeof searchNodes>[0])
    results.value = res.data.results
    total.value = res.data.total
  } catch {
    results.value = []
    total.value = 0
  } finally {
    searching.value = false
  }
}

onMounted(async () => {
  try {
    const res = await getPopularTags(10)
    popularTags.value = res.data
  } catch {
    // ignore - tags are optional
  }
})
</script>
