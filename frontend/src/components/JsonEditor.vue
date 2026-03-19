<template>
  <div class="flex flex-col gap-1">
    <label v-if="label" class="text-sm font-medium text-gray-700">{{ label }}</label>
    <textarea
      :value="modelValue"
      rows="6"
      :class="[
        'block w-full rounded-md border px-3 py-2 text-sm font-mono shadow-sm focus:outline-none focus:ring-2',
        hasError
          ? 'border-red-400 focus:ring-red-500 focus:border-red-500'
          : 'border-gray-300 focus:ring-indigo-500 focus:border-indigo-500',
      ]"
      placeholder="{}"
      spellcheck="false"
      @input="handleInput"
    />
    <p v-if="hasError" class="text-xs text-red-500">{{ parseError }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  modelValue?: string
  label?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  valid: [value: unknown]
}>()

const parseError = ref('')

const hasError = ref(false)

function handleInput(event: Event) {
  const raw = (event.target as HTMLTextAreaElement).value
  emit('update:modelValue', raw)
  try {
    const parsed = JSON.parse(raw)
    hasError.value = false
    parseError.value = ''
    emit('valid', parsed)
  } catch (e: unknown) {
    hasError.value = true
    parseError.value = e instanceof Error ? e.message : 'JSON 格式错误'
  }
}
</script>
