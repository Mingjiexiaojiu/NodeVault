<template>
  <span :class="['inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium', colorClass]">
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { NodeStatus } from '@/api/nodes'

const props = defineProps<{ status: NodeStatus }>()

const config: Record<NodeStatus, { label: string; cls: string }> = {
  draft: { label: '草稿', cls: 'bg-gray-100 text-gray-700' },
  active: { label: '活跃', cls: 'bg-green-100 text-green-700' },
  deprecated: { label: '已弃用', cls: 'bg-yellow-100 text-yellow-700' },
  archived: { label: '已归档', cls: 'bg-red-100 text-red-700' },
}

const colorClass = computed(() => config[props.status]?.cls ?? 'bg-gray-100 text-gray-700')
const label = computed(() => config[props.status]?.label ?? props.status)
</script>
