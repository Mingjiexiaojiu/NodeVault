<template>
  <div class="min-h-screen -m-6 bg-gray-50">
    <div class="max-w-5xl mx-auto px-8 py-8 flex gap-8">
      <!-- 左侧步骤导航 -->
      <aside class="w-52 shrink-0">
        <nav class="sticky top-8 space-y-1">
          <a
            v-for="(section, i) in sections"
            :key="section.id"
            :href="`#${section.id}`"
            class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors group"
            :class="activeSection === section.id
              ? 'bg-indigo-50 text-indigo-700 font-medium'
              : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'"
          >
            <span
              class="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold"
              :class="activeSection === section.id
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-200 text-gray-500 group-hover:bg-gray-300'"
            >{{ i + 1 }}</span>
            {{ section.label }}
          </a>
        </nav>
      </aside>

      <!-- 右侧表单 -->
      <form class="flex-1 min-w-0 space-y-6" @submit.prevent="handleSubmit">

        <!-- ① 基本信息 -->
        <section :id="sections[0].id" class="bg-white rounded-2xl border border-gray-200 overflow-hidden">
          <div class="flex items-center gap-3 px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-indigo-50 to-white">
            <div class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
              <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h2 class="text-sm font-semibold text-gray-900">基本信息</h2>
              <p class="text-xs text-gray-500 mt-0.5">节点的身份标识与元数据</p>
            </div>
          </div>
          <div class="p-6 grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                唯一标识 (name) <span class="text-red-500">*</span>
              </label>
              <div class="relative">
                <input
                  v-model="form.name"
                  placeholder="my_algorithm_v1"
                  :class="[
                    'block w-full rounded-lg border px-3 py-2.5 text-sm transition-colors focus:outline-none focus:ring-2',
                    errors.name
                      ? 'border-red-300 bg-red-50 focus:ring-red-400 focus:border-red-400'
                      : 'border-gray-200 bg-gray-50 focus:bg-white focus:ring-indigo-400 focus:border-indigo-400'
                  ]"
                />
              </div>
              <p v-if="errors.name" class="text-xs text-red-500 flex items-center gap-1">
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
                {{ errors.name }}
              </p>
              <p v-else class="text-xs text-gray-400">小写字母开头，仅含小写字母 / 数字 / 下划线，3–64 位</p>
            </div>

            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">版本号</label>
              <input
                v-model="form.version"
                placeholder="1.0.0"
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
              />
              <p class="text-xs text-gray-400">遵循语义化版本，如 1.0.0</p>
            </div>

            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">显示名称</label>
              <input
                v-model="form.display_name"
                placeholder="我的算法 V1"
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
              />
            </div>

            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                类型 <span class="text-red-500">*</span>
              </label>
              <select
                v-model="form.type"
                :class="[
                  'block w-full rounded-lg border px-3 py-2.5 text-sm focus:outline-none focus:ring-2 transition-colors appearance-none cursor-pointer',
                  errors.type
                    ? 'border-red-300 bg-red-50 focus:ring-red-400'
                    : 'border-gray-200 bg-gray-50 focus:bg-white focus:ring-indigo-400 focus:border-indigo-400'
                ]"
              >
                <option value="" disabled>请选择节点类型</option>
                <option v-for="t in nodeTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
              </select>
              <p v-if="errors.type" class="text-xs text-red-500">{{ errors.type }}</p>
            </div>

            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">分类</label>
              <input
                v-model="form.category"
                placeholder="finance"
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
              />
            </div>

            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">标签</label>
              <input
                v-model="form.tagsRaw"
                placeholder="tag1, tag2, tag3"
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
              />
              <p class="text-xs text-gray-400">多个标签用英文逗号分隔</p>
            </div>

            <div class="sm:col-span-2 flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">描述</label>
              <textarea
                v-model="form.description"
                placeholder="简要描述该节点的功能、使用场景或注意事项..."
                rows="3"
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
              />
            </div>

            <!-- 技能集 -->
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">技能集</label>
              <select
                v-model="form.skill_id"
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors appearance-none cursor-pointer"
              >
                <option value="">不归属任何技能集</option>
                <option v-for="sk in skills" :key="sk.id" :value="sk.id">
                  {{ sk.display_name || sk.name }}
                </option>
              </select>
              <p class="text-xs text-gray-400">将节点归类到某个 Agent 技能集，方便 AI 发现和调用</p>
            </div>

            <!-- 用途提示 -->
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">用途提示 (usage_hint)</label>
              <textarea
                v-model="form.usage_hint"
                placeholder="向 AI 解释该节点的具体应用场景，例如：用于分析信贷申请人的收入流水..."
                rows="2"
                maxlength="500"
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
              />
              <p class="text-xs text-gray-400 text-right">{{ form.usage_hint.length }}/500</p>
            </div>
          </div>
        </section>

        <!-- ② 运行时配置 -->
        <section :id="sections[1].id" class="bg-white rounded-2xl border border-gray-200 overflow-hidden">
          <div class="flex items-center gap-3 px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-violet-50 to-white">
            <div class="w-8 h-8 rounded-lg bg-violet-600 flex items-center justify-center">
              <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h2 class="text-sm font-semibold text-gray-900">运行时配置</h2>
              <p class="text-xs text-gray-500 mt-0.5">节点调用时的连接信息</p>
            </div>
          </div>
          <div class="p-6 space-y-5">
            <div class="grid grid-cols-2 gap-5">
              <div class="flex flex-col gap-1.5">
                <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">运行时类型</label>
                <select
                  v-model="form.runtime.type"
                  class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-400 focus:bg-white transition-colors appearance-none cursor-pointer"
                >
                  <option value="http">HTTP</option>
                </select>
              </div>
              <div class="flex flex-col gap-1.5">
                <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">HTTP Method</label>
                <select
                  v-model="form.runtime.method"
                  class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-400 focus:bg-white transition-colors appearance-none cursor-pointer"
                >
                  <option value="POST">POST</option>
                  <option value="GET">GET</option>
                  <option value="PUT">PUT</option>
                  <option value="DELETE">DELETE</option>
                </select>
              </div>
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                Endpoint URL <span class="text-red-500">*</span>
              </label>
              <div class="relative">
                <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                  <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                </div>
                <input
                  v-model="form.runtime.endpoint"
                  placeholder="https://your-service.com/api/predict"
                  :class="[
                    'block w-full rounded-lg border pl-10 pr-3 py-2.5 text-sm font-mono focus:outline-none focus:ring-2 transition-colors',
                    errors.endpoint
                      ? 'border-red-300 bg-red-50 focus:ring-red-400 focus:border-red-400'
                      : 'border-gray-200 bg-gray-50 focus:bg-white focus:ring-violet-400 focus:border-violet-400'
                  ]"
                />
              </div>
              <p v-if="errors.endpoint" class="text-xs text-red-500 flex items-center gap-1">
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
                {{ errors.endpoint }}
              </p>
            </div>
          </div>
        </section>

        <!-- ③ Schema -->
        <section :id="sections[2].id" class="bg-white rounded-2xl border border-gray-200 overflow-hidden">
          <div class="flex items-center gap-3 px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-emerald-50 to-white">
            <div class="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center">
              <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </div>
            <div>
              <h2 class="text-sm font-semibold text-gray-900">输入 / 输出 Schema</h2>
              <p class="text-xs text-gray-500 mt-0.5">定义节点的 JSON 数据契约（可选）</p>
            </div>
          </div>
          <div class="p-6 grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide flex items-center gap-2">
                <span class="inline-block w-2 h-2 rounded-full bg-blue-400"></span>
                Input Schema
              </label>
              <textarea
                :value="form.inputSchemaRaw"
                rows="8"
                placeholder="{}"
                spellcheck="false"
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-xs font-mono resize-none focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-emerald-400 focus:bg-white transition-colors"
                @input="handleInputSchema"
              />
              <p v-if="inputSchemaError" class="text-xs text-red-500 font-mono">{{ inputSchemaError }}</p>
              <p v-else class="text-xs text-emerald-600 flex items-center gap-1">
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
                JSON 格式正确
              </p>
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide flex items-center gap-2">
                <span class="inline-block w-2 h-2 rounded-full bg-orange-400"></span>
                Output Schema
              </label>
              <textarea
                :value="form.outputSchemaRaw"
                rows="8"
                placeholder="{}"
                spellcheck="false"
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-xs font-mono resize-none focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-emerald-400 focus:bg-white transition-colors"
                @input="handleOutputSchema"
              />
              <p v-if="outputSchemaError" class="text-xs text-red-500 font-mono">{{ outputSchemaError }}</p>
              <p v-else class="text-xs text-emerald-600 flex items-center gap-1">
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
                JSON 格式正确
              </p>
            </div>
          </div>
        </section>

        <!-- 错误提示 & 提交 -->
        <div
          v-if="submitError"
          class="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl px-4 py-3"
        >
          <svg class="w-5 h-5 text-red-500 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
          </svg>
          <p class="text-sm text-red-700">{{ submitError }}</p>
        </div>

        <!-- 提交区 -->
        <div class="pb-8 flex justify-center">
          <BaseButton type="submit" :loading="loading" class="px-10 py-3 text-base shadow-lg shadow-indigo-200">
            <svg v-if="!loading" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            注册节点
          </BaseButton>
        </div>
      </form>
    </div>

  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createNode } from '@/api/nodes'
import { getSkills } from '@/api/skills'
import type { NodeType } from '@/api/nodes'
import type { SkillItem } from '@/api/skills'
import BaseButton from '@/components/BaseButton.vue'

const router = useRouter()

const sections = [
  { id: 'basic', label: '基本信息' },
  { id: 'runtime', label: '运行时配置' },
  { id: 'schema', label: 'Schema' },
]
const activeSection = ref('basic')

const defaultSchema = '{\n  "type": "object",\n  "properties": {}\n}'

const skills = ref<SkillItem[]>([])

onMounted(async () => {
  try {
    skills.value = await getSkills()
  } catch {
    // 非关键性错误，静默处理
  }
})

const form = reactive({
  name: '',
  version: '1.0.0',
  display_name: '',
  description: '',
  type: '' as NodeType | '',
  category: '',
  tagsRaw: '',
  skill_id: '',
  usage_hint: '',
  runtime: { type: 'http', endpoint: '', method: 'POST' },
  inputSchemaRaw: defaultSchema,
  outputSchemaRaw: defaultSchema,
})

const parsedInputSchema = ref<unknown>({})
const parsedOutputSchema = ref<unknown>({})
const inputSchemaError = ref('')
const outputSchemaError = ref('')

function handleInputSchema(e: Event) {
  const raw = (e.target as HTMLTextAreaElement).value
  form.inputSchemaRaw = raw
  try {
    parsedInputSchema.value = JSON.parse(raw)
    inputSchemaError.value = ''
  } catch (err) {
    inputSchemaError.value = err instanceof Error ? err.message : 'JSON 格式错误'
  }
}

function handleOutputSchema(e: Event) {
  const raw = (e.target as HTMLTextAreaElement).value
  form.outputSchemaRaw = raw
  try {
    parsedOutputSchema.value = JSON.parse(raw)
    outputSchemaError.value = ''
  } catch (err) {
    outputSchemaError.value = err instanceof Error ? err.message : 'JSON 格式错误'
  }
}

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
    activeSection.value = 'basic'
    return false
  }
  if (!form.type) {
    errors.type = '请选择类型'
    activeSection.value = 'basic'
    return false
  }
  if (!form.runtime.endpoint) {
    errors.endpoint = '请输入 Endpoint URL'
    activeSection.value = 'runtime'
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
      skill_id: form.skill_id || undefined,
      usage_hint: form.usage_hint || undefined,
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
