<template>
  <div class="max-w-3xl">
    <!-- 标题 -->
    <div class="flex items-center gap-3 mb-6">
      <RouterLink to="/nodes" class="text-gray-400 hover:text-gray-600 transition-colors">
        ← 返回列表
      </RouterLink>
      <span class="text-gray-300">/</span>
      <h1 class="text-xl font-bold text-gray-900">注册新节点</h1>
    </div>

    <form class="space-y-6" @submit.prevent="handleSubmit">
      <!-- 基本信息 -->
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <h2 class="text-base font-semibold text-gray-900 mb-4">基本信息</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <BaseInput
            v-model="form.name"
            label="唯一标识 (name)"
            placeholder="my_algorithm_v1"
            required
            hint="小写字母开头，仅含小写字母/数字/下划线，3-64 位"
            :error="errors.name"
          />
          <BaseInput
            v-model="form.version"
            label="版本号"
            placeholder="1.0.0"
            hint="语义化版本号，如 1.0.0"
            :error="errors.version"
          />
          <BaseInput v-model="form.display_name" label="显示名称" placeholder="我的算法 V1" />
          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium text-gray-700">类型 <span class="text-red-500">*</span></label>
            <select
              v-model="form.type"
              class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              required
            >
              <option value="" disabled>请选择类型</option>
              <option v-for="t in nodeTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
            </select>
            <p v-if="errors.type" class="text-xs text-red-500">{{ errors.type }}</p>
          </div>
          <BaseInput v-model="form.category" label="分类" placeholder="finance" />
          <BaseInput
            v-model="form.tagsRaw"
            label="标签"
            placeholder="tag1, tag2, tag3"
            hint="多个标签用逗号分隔"
          />
          <div class="sm:col-span-2">
            <BaseInput
              v-model="form.description"
              label="描述"
              placeholder="简要描述节点的功能..."
            />
          </div>
        </div>
      </div>

      <!-- 运行时配置 -->
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <h2 class="text-base font-semibold text-gray-900 mb-4">运行时配置</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium text-gray-700">运行时类型</label>
            <select
              v-model="form.runtime.type"
              class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="http">HTTP</option>
            </select>
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium text-gray-700">HTTP Method</label>
            <select
              v-model="form.runtime.method"
              class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="POST">POST</option>
              <option value="GET">GET</option>
              <option value="PUT">PUT</option>
              <option value="DELETE">DELETE</option>
            </select>
          </div>
          <div class="sm:col-span-2">
            <BaseInput
              v-model="form.runtime.endpoint"
              label="Endpoint URL"
              placeholder="https://your-service.com/api/predict"
              required
              :error="errors.endpoint"
            />
          </div>
        </div>
      </div>

      <!-- IO Schema -->
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <h2 class="text-base font-semibold text-gray-900 mb-4">输入/输出 Schema</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <JsonEditor
            v-model="form.inputSchemaRaw"
            label="Input Schema (JSON)"
          @valid="(v: unknown) => (parsedInputSchema = v)"
        />
          <JsonEditor
            v-model="form.outputSchemaRaw"
            label="Output Schema (JSON)"
            @valid="(v: unknown) => (parsedOutputSchema = v)"
          />
        </div>
      </div>

      <!-- 错误 & 提交 -->
      <div>
        <p v-if="submitError" class="text-sm text-red-500 bg-red-50 px-4 py-3 rounded-md mb-4">
          {{ submitError }}
        </p>
        <div class="flex gap-3">
          <BaseButton type="submit" :loading="loading">注册节点</BaseButton>
          <RouterLink to="/nodes">
            <BaseButton variant="secondary">取消</BaseButton>
          </RouterLink>
        </div>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createNode } from '@/api/nodes'
import type { NodeType } from '@/api/nodes'
import BaseInput from '@/components/BaseInput.vue'
import BaseButton from '@/components/BaseButton.vue'
import JsonEditor from '@/components/JsonEditor.vue'

const router = useRouter()

const defaultSchema = '{"type":"object","properties":{}}'

const form = reactive({
  name: '',
  version: '1.0.0',
  display_name: '',
  description: '',
  type: '' as NodeType | '',
  category: '',
  tagsRaw: '',
  runtime: { type: 'http', endpoint: '', method: 'POST' },
  inputSchemaRaw: defaultSchema,
  outputSchemaRaw: defaultSchema,
})

const parsedInputSchema = ref<unknown>({})
const parsedOutputSchema = ref<unknown>({})

const errors = reactive({ name: '', version: '', type: '', endpoint: '' })
const submitError = ref('')
const loading = ref(false)

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

function validate(): boolean {
  errors.name = ''
  errors.version = ''
  errors.type = ''
  errors.endpoint = ''

  const nameRegex = /^[a-z][a-z0-9_]{2,63}$/
  if (!nameRegex.test(form.name)) {
    errors.name = '格式：小写字母开头，仅含小写字母/数字/下划线，3-64 位'
    return false
  }
  if (!form.type) {
    errors.type = '请选择类型'
    return false
  }
  if (!form.runtime.endpoint) {
    errors.endpoint = '请输入 Endpoint URL'
    return false
  }
  return true
}

async function handleSubmit() {
  if (!validate()) return
  submitError.value = ''
  loading.value = true

  try {
    const tags = form.tagsRaw
      ? form.tagsRaw.split(',').map((t) => t.trim()).filter(Boolean)
      : []

    const res = await createNode({
      name: form.name,
      version: form.version || undefined,
      display_name: form.display_name || undefined,
      description: form.description || undefined,
      type: form.type as NodeType,
      category: form.category || undefined,
      tags,
      runtime: {
        type: form.runtime.type,
        endpoint: form.runtime.endpoint,
        method: form.runtime.method,
      },
      input_schema: parsedInputSchema.value as Record<string, unknown>,
      output_schema: parsedOutputSchema.value as Record<string, unknown>,
    })

    router.push(`/nodes/${res.data.id}`)
  } catch (e: unknown) {
    const err = e as { response?: { status?: number; data?: { detail?: string | { msg: string }[] } } }
    if (err.response?.status === 409) {
      submitError.value = `节点名称 "${form.name}" 已存在，请换一个名称`
    } else if (err.response?.status === 422) {
      const detail = err.response.data?.detail
      if (Array.isArray(detail)) {
        submitError.value = detail.map((d) => d.msg).join('；')
      } else {
        submitError.value = detail ?? '请检查输入字段'
      }
    } else {
      submitError.value = '注册失败，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}
</script>
