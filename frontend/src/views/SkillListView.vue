<template>
  <div class="space-y-6">
    <!-- 头部 -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-semibold text-gray-900">技能集</h1>
        <p class="text-sm text-gray-400 mt-0.5">将节点打包为 AI 可调用的 Agent Skills</p>
      </div>
      <button
        class="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-xl hover:bg-indigo-700 active:scale-95 transition-all shadow-sm shadow-indigo-200"
        @click="showCreate = true"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4" />
        </svg>
        新建技能集
      </button>
    </div>

    <!-- 列表 -->
    <div v-if="loading" class="space-y-3">
      <div v-for="i in 4" :key="i" class="h-20 bg-gray-100 rounded-xl animate-pulse" />
    </div>

    <div v-else-if="skills.length === 0" class="text-center py-16 text-gray-400">
      <svg class="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
      <p class="text-sm">暂无技能集</p>
      <p class="text-xs mt-1">点击「新建技能集」开始将节点组织成可导出的 Agent Skill</p>
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <RouterLink
        v-for="skill in skills"
        :key="skill.id"
        :to="`/skills/${skill.id}`"
        class="group bg-white rounded-2xl border border-gray-100 overflow-hidden hover:border-indigo-200 hover:shadow-md hover:shadow-indigo-100/40 transition-all duration-200"
      >
        <!-- 彩色顶部条 -->
        <div class="h-1" :class="skill.status === 'active' ? 'bg-gradient-to-r from-indigo-500 to-violet-500' : 'bg-gray-200'"></div>
        <div class="p-5">
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <h3 class="text-sm font-semibold text-gray-900 truncate">{{ skill.display_name || skill.name }}</h3>
                <span v-if="skill.is_system" class="shrink-0 text-xs px-1.5 py-0.5 rounded-full bg-blue-50 text-blue-600 border border-blue-200">系统</span>
                <span v-else class="shrink-0 text-xs px-1.5 py-0.5 rounded-full bg-gray-50 text-gray-500 border border-gray-200">自定义</span>
                <span v-if="skill.is_stale" class="shrink-0 text-xs px-1.5 py-0.5 rounded-full bg-amber-50 text-amber-600 border border-amber-200">需更新</span>
              </div>
              <p class="text-xs text-gray-400 font-mono mt-0.5">{{ skill.name }}</p>
            </div>
            <span class="shrink-0 text-xs px-2 py-0.5 rounded-full" :class="skill.status === 'active' ? 'bg-emerald-50 text-emerald-600 border border-emerald-200' : 'bg-gray-100 text-gray-500'">
              {{ skill.status === 'active' ? '活跃' : skill.status }}
            </span>
          </div>
          <p v-if="skill.description" class="text-xs text-gray-500 mt-3 line-clamp-2 leading-relaxed">{{ skill.description }}</p>
        </div>
        <!-- 卡片底栏 -->
        <div class="px-5 py-3 bg-gray-50/60 border-t border-gray-100 flex items-center gap-3 text-xs text-gray-400">
          <span class="flex items-center gap-1">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
            {{ skill.node_count }} 个节点
          </span>
          <span v-if="skill.latest_version" class="font-mono text-indigo-500 font-medium">v{{ skill.latest_version }}</span>
          <span v-else class="text-gray-300">未发版</span>
          <span class="ml-auto text-gray-200 group-hover:text-indigo-400 transition-colors">→</span>
        </div>
      </RouterLink>
    </div>

    <!-- 新建 Modal -->
    <Teleport to="body">
      <div
        v-if="showCreate"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
        @click.self="showCreate = false"
      >
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
          <h2 class="text-base font-semibold text-gray-900 mb-4">新建技能集</h2>
          <div class="space-y-4">
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-medium text-gray-600">名称 (kebab-case) <span class="text-red-500">*</span></label>
              <input
                v-model="createForm.name"
                placeholder="my-skill"
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
              />
              <p v-if="createError" class="text-xs text-red-500">{{ createError }}</p>
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-medium text-gray-600">显示名称</label>
              <input
                v-model="createForm.display_name"
                placeholder="我的技能集"
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
              />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-medium text-gray-600">描述</label>
              <textarea
                v-model="createForm.description"
                rows="2"
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
              />
            </div>
          </div>
          <div class="flex justify-end gap-3 mt-6">
            <button
              class="px-4 py-2 text-sm text-gray-600 hover:text-gray-900"
              @click="showCreate = false"
            >
              取消
            </button>
            <button
              class="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              :disabled="creating"
              @click="handleCreate"
            >
              {{ creating ? '创建中...' : '创建' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getSkills, createSkill } from '@/api/skills'
import type { SkillItem } from '@/api/skills'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const skills = ref<SkillItem[]>([])
const loading = ref(true)
const showCreate = ref(false)
const creating = ref(false)
const createError = ref('')

const createForm = reactive({
  name: '',
  display_name: '',
  description: '',
})

onMounted(async () => {
  try {
    skills.value = await getSkills()
  } finally {
    loading.value = false
  }
})

async function handleCreate() {
  createError.value = ''
  if (!createForm.name) {
    createError.value = '名称不能为空'
    return
  }

  // 从用户已加入的部门中取第一个
  const departmentId = authStore.user?.departments?.[0]?.id

  if (!departmentId) {
    createError.value = '获取部门 ID 失败，请先加入一个部门后再试'
    return
  }

  creating.value = true
  try {
    const skill = await createSkill({
      name: createForm.name,
      display_name: createForm.display_name || undefined,
      description: createForm.description || undefined,
      department_id: departmentId,
    })
    showCreate.value = false
    router.push(`/skills/${skill.id}`)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    createError.value = err.response?.data?.detail ?? '创建失败，请检查名称格式'
  } finally {
    creating.value = false
  }
}
</script>
