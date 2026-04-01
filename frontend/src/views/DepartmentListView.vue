<template>
  <div>
    <!-- 页头 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-xl font-semibold text-gray-900">部门总览</h1>
        <p class="text-sm text-gray-400 mt-0.5">查看公司所有部门，了解各部门能力节点与成员</p>
      </div>
      <button
        v-if="canCreate"
        @click="showCreate = true"
        class="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        创建部门
      </button>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-3 gap-4 mb-8">
      <div class="bg-white rounded-xl border border-gray-200 p-5">
        <div class="text-sm text-gray-500">部门总数</div>
        <div class="text-2xl font-bold text-gray-900 mt-1">{{ total }}</div>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-5">
        <div class="text-sm text-gray-500">我所在的部门</div>
        <div class="text-2xl font-bold text-indigo-600 mt-1">{{ authStore.user?.departments?.length ?? 0 }}</div>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-5">
        <div class="text-sm text-gray-500">节点总数</div>
        <div class="text-2xl font-bold text-gray-900 mt-1">{{ totalNodes }}</div>
      </div>
    </div>

    <!-- 部门卡片网格 -->
    <div v-if="loading" class="text-center py-20 text-gray-400">加载中...</div>
    <div v-else-if="departments.length === 0" class="text-center py-20 text-gray-400">暂无部门</div>
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <RouterLink
        v-for="dept in departments"
        :key="dept.id"
        :to="`/departments/${dept.id}`"
        class="group bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg hover:border-indigo-200 transition-all duration-200"
      >
        <!-- 标题行 -->
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-lg">
              {{ dept.team_name.charAt(0).toUpperCase() }}
            </div>
            <div>
              <h3 class="font-semibold text-gray-900 group-hover:text-indigo-600 transition-colors">
                {{ dept.team_name }}
              </h3>
              <span class="text-xs text-gray-400">{{ dept.organization_name }}</span>
            </div>
          </div>
          <span
            v-if="isMy(dept.id)"
            class="px-2 py-0.5 bg-green-50 text-green-600 text-xs rounded-full"
          >已加入</span>
        </div>

        <!-- 简介 -->
        <p class="text-sm text-gray-500 mb-4 line-clamp-2 min-h-[40px]">
          {{ dept.description || '暂无简介' }}
        </p>

        <!-- 底部统计 -->
        <div class="flex items-center gap-4 text-xs text-gray-400 pt-3 border-t border-gray-100">
          <span class="flex items-center gap-1">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
            {{ dept.member_count }} 成员
          </span>
          <span class="flex items-center gap-1">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
            {{ dept.node_count }} 节点
          </span>
          <span class="ml-auto text-gray-300">{{ formatDate(dept.created_at) }}</span>
        </div>
      </RouterLink>
    </div>

    <!-- 创建部门弹窗 -->
    <div v-if="showCreate" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showCreate = false">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">创建新部门</h2>
        <form @submit.prevent="handleCreate">
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">部门名称</label>
              <input v-model="form.org_name" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500" placeholder="如 数据中心" required />
              <p class="text-xs text-gray-400 mt-1">可选择已有部门或输入新部门名称</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">团队名称</label>
              <input v-model="form.team_name" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500" placeholder="如 数据分析组" required />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">团队简介</label>
              <textarea v-model="form.description" rows="3" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500" placeholder="描述团队职责与能力方向..."></textarea>
            </div>
          </div>
          <div v-if="createError" class="mt-3 text-sm text-red-600">{{ createError }}</div>
          <div class="flex justify-end gap-3 mt-6">
            <button type="button" @click="showCreate = false" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">取消</button>
            <button type="submit" :disabled="creating" class="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50">
              {{ creating ? '创建中...' : '创建' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { listDepartments, createDepartment, type DepartmentBrief } from '@/api/departments'

const authStore = useAuthStore()

const departments = ref<DepartmentBrief[]>([])
const total = ref(0)
const loading = ref(true)

const totalNodes = computed(() => departments.value.reduce((sum, d) => sum + d.node_count, 0))
const canCreate = computed(() => (authStore.user?.role ?? 2) <= 1)

function isMy(deptId: string) {
  return authStore.user?.departments?.some(ns => ns.id === deptId) ?? false
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN')
}

async function loadDepartments() {
  loading.value = true
  try {
    const res = await listDepartments({ page_size: 200 })
    departments.value = res.data.items
    total.value = res.data.total
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

// 创建部门
const showCreate = ref(false)
const creating = ref(false)
const createError = ref('')
const form = ref({ org_name: '', team_name: '', description: '' })

async function handleCreate() {
  creating.value = true
  createError.value = ''
  try {
    await createDepartment(form.value)
    showCreate.value = false
    form.value = { org_name: '', team_name: '', description: '' }
    // 刷新列表 + 用户信息
    await Promise.all([loadDepartments(), authStore.fetchMe()])
  } catch (e: any) {
    createError.value = e?.response?.data?.error?.message || e?.message || '创建失败'
  } finally {
    creating.value = false
  }
}

onMounted(loadDepartments)
</script>
