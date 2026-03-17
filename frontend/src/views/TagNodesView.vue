<template>
  <div>
    <!-- 标题栏 -->
    <div class="flex items-center gap-4 mb-6">
      <RouterLink to="/search" class="text-gray-400 hover:text-gray-600 transition-colors text-sm">
        ← 搜索
      </RouterLink>
      <span class="text-gray-300">/</span>
      <div class="flex items-center gap-2">
        <span class="text-xl font-bold text-gray-900">#</span>
        <h1 class="text-xl font-bold text-gray-900">{{ tag }}</h1>
        <span v-if="total > 0" class="px-2 py-0.5 bg-indigo-100 text-indigo-700 text-xs font-medium rounded-full">
          {{ total }} 个节点
        </span>
      </div>
    </div>

    <!-- 骨架加载 -->
    <div v-if="loading" class="space-y-3">
      <div v-for="i in 5" :key="i" class="h-16 bg-gray-100 rounded-xl animate-pulse" />
    </div>

    <!-- 空状态 -->
    <div v-else-if="nodes.length === 0" class="text-center py-20">
      <p class="text-gray-400 text-sm mb-2">标签 #{{ tag }} 下暂无节点</p>
      <RouterLink to="/nodes/new" class="text-indigo-600 text-sm hover:underline">注册新节点</RouterLink>
    </div>

    <!-- 节点列表 -->
    <div v-else class="space-y-2">
      <RouterLink
        v-for="node in nodes"
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
          <p v-if="node.description" class="hidden lg:block text-xs text-gray-400 max-w-xs truncate">
            {{ node.description }}
          </p>
          <div class="hidden sm:flex gap-1">
            <RouterLink
              v-for="t in node.tags.filter(t => t !== tag).slice(0, 2)"
              :key="t"
              :to="`/tags/${t}`"
              class="px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full text-xs hover:bg-indigo-100 hover:text-indigo-700 transition-colors"
              @click.stop
            >{{ t }}</RouterLink>
          </div>
          <StatusBadge :status="node.status" />
          <svg class="w-4 h-4 text-gray-300 group-hover:text-indigo-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </RouterLink>
    </div>

    <!-- 分页 -->
    <div
      v-if="total > pageSize"
      class="flex items-center justify-between mt-6"
    >
      <span class="text-sm text-gray-500">共 {{ total }} 个节点</span>
      <div class="flex gap-2">
        <button
          class="px-4 py-2 text-sm rounded-lg border border-gray-200 bg-white text-gray-600 hover:border-indigo-300 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          :disabled="page <= 1"
          @click="changePage(page - 1)"
        >
          上一页
        </button>
        <button
          class="px-4 py-2 text-sm rounded-lg border border-gray-200 bg-white text-gray-600 hover:border-indigo-300 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          :disabled="page * pageSize >= total"
          @click="changePage(page + 1)"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getNodesByTag } from '@/api/nodes'
import type { NodeItem } from '@/api/nodes'
import TypeBadge from '@/components/TypeBadge.vue'
import StatusBadge from '@/components/StatusBadge.vue'

const route = useRoute()
const tag = ref(route.params.tag as string)

const nodes = ref<NodeItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(true)

async function fetchNodes() {
  loading.value = true
  try {
    const res = await getNodesByTag(tag.value, { page: page.value, page_size: pageSize })
    // backend returns { tag, total, page, page_size, nodes }
    const d = res.data as unknown as { nodes?: NodeItem[]; total?: number } | NodeItem[]
    if (Array.isArray(d)) {
      nodes.value = d
      total.value = d.length
    } else {
      nodes.value = d.nodes ?? []
      total.value = d.total ?? nodes.value.length
    }
  } catch {
    nodes.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function changePage(p: number) {
  page.value = p
  fetchNodes()
}

watch(() => route.params.tag, (newTag) => {
  tag.value = newTag as string
  page.value = 1
  fetchNodes()
})

onMounted(fetchNodes)
</script>
