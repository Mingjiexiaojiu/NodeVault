<template>
  <div class="flex flex-col gap-1">
    <label v-if="label" :for="id" class="text-sm font-medium text-gray-700">
      {{ label }}
      <span v-if="required" class="text-red-500 ml-0.5">*</span>
    </label>
    <input
      :id="id"
      :value="modelValue"
      :class="[
        'block w-full rounded-md border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
        error ? 'border-red-400 focus:ring-red-500 focus:border-red-500' : 'border-gray-300',
      ]"
      v-bind="$attrs"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <p v-if="error" class="text-xs text-red-500">{{ error }}</p>
    <p v-else-if="hint" class="text-xs text-gray-500">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
import { useId } from 'vue'

defineProps<{
  modelValue?: string
  label?: string
  error?: string
  hint?: string
  required?: boolean
}>()

defineEmits<{ 'update:modelValue': [value: string] }>()

const id = useId()
</script>
