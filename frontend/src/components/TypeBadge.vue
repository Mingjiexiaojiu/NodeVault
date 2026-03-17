<template>
  <span :class="['inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium', colorClass]">
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { NodeType } from '@/api/nodes'

const props = defineProps<{ type: NodeType }>()

const config: Record<NodeType, { label: string; cls: string }> = {
  data_cleaning: { label: '数据清洗', cls: 'bg-blue-100 text-blue-700' },
  analysis: { label: '分析', cls: 'bg-purple-100 text-purple-700' },
  risk: { label: '风控', cls: 'bg-orange-100 text-orange-700' },
  nlp: { label: 'NLP', cls: 'bg-teal-100 text-teal-700' },
  vision: { label: '视觉', cls: 'bg-pink-100 text-pink-700' },
  ml: { label: '机器学习', cls: 'bg-indigo-100 text-indigo-700' },
  tool: { label: '工具', cls: 'bg-gray-100 text-gray-700' },
  utility: { label: '实用程序', cls: 'bg-slate-100 text-slate-700' },
}

const colorClass = computed(() => config[props.type]?.cls ?? 'bg-gray-100 text-gray-700')
const label = computed(() => config[props.type]?.label ?? props.type)
</script>
