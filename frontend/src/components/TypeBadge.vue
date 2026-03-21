<template>
  <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-700">
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CategoryBrief } from '@/api/nodes'

const props = defineProps<{ category?: CategoryBrief | null; fallback?: string }>()

const label = computed(() => props.category?.display_name || props.fallback || '未分类')
</script>
