<template>
  <div v-if="loading" class="space-y-4">
    <div class="h-32 bg-gray-100 rounded-xl animate-pulse" />
    <div class="h-48 bg-gray-100 rounded-xl animate-pulse" />
  </div>

  <div v-else-if="!skill" class="text-center py-16 text-gray-400">
    <p class="text-sm">技能集不存在或已被删除</p>
  </div>

  <div v-else class="space-y-6">
    <!-- 头部卡片 -->
    <div class="bg-white rounded-2xl border border-gray-200 p-6">
      <div class="flex items-start justify-between gap-4">
        <div class="min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <h1 class="text-xl font-semibold text-gray-900">{{ skill.display_name || skill.name }}</h1>
            <span class="font-mono text-sm text-gray-400">{{ skill.name }}</span>
            <span
              v-if="skill.is_stale"
              class="text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-600 border border-amber-200"
            >
              需更新 SKILL.md
            </span>
          </div>
          <p v-if="skill.description" class="text-sm text-gray-500 mt-1.5">{{ skill.description }}</p>
          <div class="flex items-center gap-4 mt-3 text-xs text-gray-400">
            <span>{{ skill.node_count }} 个节点</span>
            <span>{{ skill.versions.length }} 个版本</span>
            <span v-if="skill.latest_version" class="text-indigo-500 font-mono">最新版本: v{{ skill.latest_version }}</span>
          </div>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <button
            v-if="skill.versions.length > 0"
            class="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            @click="handleExport"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            导出 ZIP
          </button>
          <button
            class="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
            :disabled="generating"
            @click="handleGenerate"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            {{ generating ? 'AI 生成中...' : 'AI 生成 SKILL.md' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 节点列表 -->
    <div class="bg-white rounded-2xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100">
        <h2 class="text-sm font-semibold text-gray-900">节点（{{ skill.nodes.length }}）</h2>
      </div>
      <div v-if="skill.nodes.length === 0" class="px-6 py-8 text-center text-sm text-gray-400">
        暂无节点。在节点编辑页将节点归属到此技能集即可。
      </div>
      <ul v-else class="divide-y divide-gray-50">
        <li
          v-for="node in skill.nodes"
          :key="node.id"
          class="flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors"
        >
          <div class="min-w-0">
            <RouterLink
              :to="`/nodes/${node.id}`"
              class="text-sm font-medium text-gray-900 hover:text-indigo-600 transition-colors"
            >
              {{ node.display_name || node.name }}
            </RouterLink>
            <p class="text-xs text-gray-400 font-mono">{{ node.name }}</p>
            <p v-if="node.usage_hint" class="text-xs text-gray-500 mt-0.5 line-clamp-1">{{ node.usage_hint }}</p>
            <p v-else class="text-xs text-amber-500 mt-0.5">⚠ 建议填写 usage_hint 以提升 AI 生成质量</p>
          </div>
          <RouterLink
            :to="`/nodes/${node.id}/edit`"
            class="text-xs text-indigo-500 hover:underline ml-4 shrink-0"
          >
            编辑
          </RouterLink>
        </li>
      </ul>
    </div>

    <!-- 版本历史 -->
    <div class="bg-white rounded-2xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h2 class="text-sm font-semibold text-gray-900">版本历史（{{ skill.versions.length }}）</h2>
        <button
          class="text-xs text-indigo-600 hover:underline"
          @click="showPublish = true"
        >
          发布新版本
        </button>
      </div>
      <div v-if="skill.versions.length === 0" class="px-6 py-8 text-center text-sm text-gray-400">
        暂无版本，点击「AI 生成 SKILL.md」后发布第一个版本。
      </div>
      <ul v-else class="divide-y divide-gray-50">
        <li
          v-for="ver in skill.versions"
          :key="ver.id"
          class="px-6 py-4"
        >
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <span class="font-mono text-sm text-gray-900">v{{ ver.version }}</span>
              <span
                v-if="ver.is_default"
                class="text-xs px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-600 border border-indigo-200"
              >
                默认
              </span>
            </div>
            <button
              class="text-xs text-gray-400 hover:text-indigo-600 transition-colors"
              @click="downloadVersion(ver.version)"
            >
              下载
            </button>
          </div>
          <p v-if="ver.release_notes" class="text-xs text-gray-500 mt-1">{{ ver.release_notes }}</p>
          <p class="text-xs text-gray-400 mt-1">{{ ver.node_snapshot.length }} 个节点快照 · {{ new Date(ver.created_at).toLocaleDateString() }}</p>
        </li>
      </ul>
    </div>

    <!-- AI 配置选择器 Modal -->
    <Teleport to="body">
      <div
        v-if="showConfigPicker"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
        @click.self="showConfigPicker = false"
      >
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-md">
          <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 class="text-base font-semibold text-gray-900">选择 AI 配置</h3>
            <button class="text-gray-400 hover:text-gray-600" @click="showConfigPicker = false">✕</button>
          </div>
          <div class="px-6 py-4 space-y-2">
            <!-- 使用系统默认 -->
            <label
              class="flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-colors"
              :class="selectedConfigId === null ? 'border-indigo-400 bg-indigo-50' : 'border-gray-200 hover:border-gray-300'"
            >
              <input
                type="radio"
                :value="null"
                v-model="selectedConfigId"
                class="text-indigo-600"
              />
              <div>
                <p class="text-sm font-medium text-gray-900">使用系统默认</p>
                <p class="text-xs text-gray-400">使用服务器环境变量中配置的 LLM</p>
              </div>
            </label>

            <!-- 无自定义配置提示 -->
            <p v-if="aiConfigs.length === 0" class="text-xs text-gray-400 text-center py-2">
              暂无自定义 AI 配置，
              <RouterLink to="/ai-config" class="text-indigo-500 hover:underline">点此添加</RouterLink>
            </p>

            <!-- 自定义配置列表 -->
            <label
              v-for="cfg in aiConfigs"
              :key="cfg.id"
              class="flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-colors"
              :class="selectedConfigId === cfg.id ? 'border-indigo-400 bg-indigo-50' : 'border-gray-200 hover:border-gray-300'"
            >
              <input
                type="radio"
                :value="cfg.id"
                v-model="selectedConfigId"
                class="text-indigo-600"
              />
              <div class="min-w-0">
                <div class="flex items-center gap-1.5 flex-wrap">
                  <p class="text-sm font-medium text-gray-900">{{ cfg.name }}</p>
                  <span v-if="cfg.is_default" class="text-[10px] px-1.5 py-0.5 rounded-full bg-indigo-50 text-indigo-600 border border-indigo-200">默认</span>
                </div>
                <p class="text-xs text-gray-400 font-mono truncate">{{ cfg.model }} · {{ cfg.api_key_preview }}</p>
              </div>
            </label>
          </div>
          <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
            <button class="px-4 py-2 text-sm text-gray-600 hover:text-gray-900" @click="showConfigPicker = false">取消</button>
            <button
              class="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
              @click="confirmGenerate"
            >
              开始生成
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- AI 生成结果预览 Modal -->
    <Teleport to="body">
      <div
        v-if="showGenResult"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
        @click.self="showGenResult = false"
      >
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col">
          <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 class="text-base font-semibold text-gray-900">SKILL.md 草稿</h3>
            <button class="text-gray-400 hover:text-gray-600" @click="showGenResult = false">✕</button>
          </div>
          <div class="flex-1 overflow-auto p-6">
            <pre class="text-xs text-gray-700 whitespace-pre-wrap bg-gray-50 rounded-lg p-4 font-mono">{{ genResult?.skill_md }}</pre>
          </div>
          <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
            <p class="text-xs text-gray-500">建议版本号: <span class="font-mono font-medium">{{ genResult?.suggested_version }}</span></p>
            <button
              class="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
              @click="useGenResult"
            >
              使用此草稿发布版本
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 发布版本 Modal -->
    <Teleport to="body">
      <div
        v-if="showPublish"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
        @click.self="showPublish = false"
      >
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col">
          <div class="px-6 py-4 border-b border-gray-100">
            <h3 class="text-base font-semibold text-gray-900">发布新版本</h3>
          </div>
          <div class="flex-1 overflow-auto p-6 space-y-4">
            <div class="flex gap-4">
              <div class="flex flex-col gap-1.5 w-40">
                <label class="text-xs font-medium text-gray-600">版本号 <span class="text-red-500">*</span></label>
                <input
                  v-model="publishForm.version"
                  placeholder="1.0.0"
                  class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white"
                />
              </div>
              <div class="flex flex-col gap-1.5 flex-1">
                <label class="text-xs font-medium text-gray-600">发布说明</label>
                <input
                  v-model="publishForm.release_notes"
                  placeholder="本次更新内容..."
                  class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white"
                />
              </div>
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-medium text-gray-600">SKILL.md 内容 <span class="text-red-500">*</span></label>
              <textarea
                v-model="publishForm.skill_md"
                rows="12"
                placeholder="---&#10;name: my-skill&#10;description: ...&#10;---&#10;# My Skill&#10;..."
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-mono resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white"
              />
            </div>
            <p v-if="publishError" class="text-xs text-red-500">{{ publishError }}</p>
          </div>
          <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
            <button class="px-4 py-2 text-sm text-gray-600 hover:text-gray-900" @click="showPublish = false">取消</button>
            <button
              class="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              :disabled="publishing"
              @click="handlePublish"
            >
              {{ publishing ? '发布中...' : '发布' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  getSkillDetail,
  generateSkillMd,
  createSkillVersion,
  downloadSkillZip,
} from '@/api/skills'
import type { SkillDetail, GenerateResult } from '@/api/skills'
import { getAIConfigs } from '@/api/ai-config'
import type { AIConfigItem } from '@/api/ai-config'

const route = useRoute()
const skillId = route.params.id as string

const skill = ref<SkillDetail | null>(null)
const loading = ref(true)
const generating = ref(false)
const showGenResult = ref(false)
const genResult = ref<GenerateResult | null>(null)
const showPublish = ref(false)
const publishing = ref(false)
const publishError = ref('')

// AI 配置选择器
const showConfigPicker = ref(false)
const aiConfigs = ref<AIConfigItem[]>([])
const selectedConfigId = ref<string | null>(null)

const publishForm = reactive({
  version: '',
  skill_md: '',
  release_notes: '',
})

onMounted(async () => {
  try {
    skill.value = await getSkillDetail(skillId)
  } finally {
    loading.value = false
  }
})

async function handleGenerate() {
  // 先加载 AI 配置列表，再显示选择器
  try {
    aiConfigs.value = await getAIConfigs()
  } catch {
    aiConfigs.value = []
  }
  // 预选默认配置
  const defaultCfg = aiConfigs.value.find(c => c.is_default)
  selectedConfigId.value = defaultCfg?.id ?? (aiConfigs.value[0]?.id ?? null)
  showConfigPicker.value = true
}

async function confirmGenerate() {
  showConfigPicker.value = false
  generating.value = true
  try {
    genResult.value = await generateSkillMd(skillId, selectedConfigId.value ?? undefined)
    showGenResult.value = true
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    alert(err.response?.data?.detail ?? 'AI 生成失败，请稍后重试')
  } finally {
    generating.value = false
  }
}

function useGenResult() {
  if (!genResult.value) return
  publishForm.skill_md = genResult.value.skill_md
  publishForm.version = genResult.value.suggested_version
  showGenResult.value = false
  showPublish.value = true
}

async function handlePublish() {
  publishError.value = ''
  if (!publishForm.version || !publishForm.skill_md) {
    publishError.value = '版本号和 SKILL.md 内容不能为空'
    return
  }
  publishing.value = true
  try {
    await createSkillVersion(skillId, {
      version: publishForm.version,
      skill_md: publishForm.skill_md,
      release_notes: publishForm.release_notes || undefined,
      is_default: true,
    })
    showPublish.value = false
    skill.value = await getSkillDetail(skillId)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    publishError.value = err.response?.data?.detail ?? '发布失败'
  } finally {
    publishing.value = false
  }
}

async function handleExport() {
  const blob = await downloadSkillZip(skillId)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${skill.value?.name ?? 'skill'}.zip`
  a.click()
  URL.revokeObjectURL(url)
}

async function downloadVersion(version: string) {
  const blob = await downloadSkillZip(skillId, version)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${skill.value?.name ?? 'skill'}-${version}.zip`
  a.click()
  URL.revokeObjectURL(url)
}
</script>
