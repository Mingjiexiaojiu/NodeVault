<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-xl font-semibold text-gray-900">分类管理</h1>
        <p class="text-sm text-gray-400 mt-0.5">管理节点分类，支持拖拽排序</p>
      </div>
      <button
        class="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-xl hover:bg-indigo-700 active:scale-95 transition-all shadow-sm shadow-indigo-200"
        @click="showCreateDialog = true"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/>
        </svg>
        新建分类
      </button>
    </div>

    <!-- 分类列表 -->
    <div class="bg-white rounded-2xl border border-gray-100 overflow-hidden" style="box-shadow: 0 1px 3px rgba(0,0,0,0.04)">
      <div v-if="loading" class="p-6 space-y-3">
        <div v-for="i in 5" :key="i" class="h-12 bg-gray-100 rounded animate-pulse" />
      </div>

      <div v-else-if="categories.length === 0" class="p-12 text-center text-gray-400">
        暂无分类
      </div>

      <table v-else class="w-full text-sm">
        <thead class="bg-gray-50/80 border-b border-gray-100">
          <tr>
            <th class="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">排序</th>
            <th class="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">标识</th>
            <th class="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">显示名称</th>
            <th class="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">图标</th>
            <th class="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">类型</th>
            <th class="px-6 py-3.5 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="cat in categories" :key="cat.id" class="hover:bg-indigo-50/40 transition-colors">
            <td class="px-6 py-4 text-gray-500 font-mono text-xs">{{ cat.sort_order }}</td>
            <td class="px-6 py-4 font-mono text-gray-700">{{ cat.name }}</td>
            <td class="px-6 py-4 font-medium text-gray-900">{{ cat.display_name }}</td>
            <td class="px-6 py-4 text-lg">{{ cat.icon || '—' }}</td>
            <td class="px-6 py-4">
              <span
                class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                :class="cat.is_default ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'"
              >
                {{ cat.is_default ? '系统默认' : '自定义' }}
              </span>
            </td>
            <td class="px-6 py-4 text-right">
              <div class="flex items-center justify-end gap-2">
                <button
                  class="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
                  @click="startEdit(cat)"
                >编辑</button>
                <button
                  v-if="!cat.is_default"
                  class="text-xs text-red-500 hover:text-red-700 font-medium"
                  @click="handleDelete(cat)"
                >删除</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 创建/编辑弹窗 -->
    <div
      v-if="showCreateDialog || editingCat"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      @click.self="closeDialog"
    >
      <div class="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md mx-4">
        <h3 class="text-base font-semibold text-gray-900 mb-4">
          {{ editingCat ? '编辑分类' : '新建分类' }}
        </h3>
        <form class="space-y-4" @submit.prevent="handleSave">
          <div v-if="!editingCat" class="flex flex-col gap-1.5">
            <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">标识 (name)</label>
            <input
              v-model="dialogForm.name"
              placeholder="snake_case 格式"
              class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
            />
          </div>
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">显示名称</label>
            <input
              v-model="dialogForm.display_name"
              placeholder="中文名称"
              class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
            />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">图标 (emoji)</label>
              <input
                v-model="dialogForm.icon"
                placeholder="🔧"
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
              />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">排序</label>
              <input
                v-model.number="dialogForm.sort_order"
                type="number"
                class="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
              />
            </div>
          </div>
          <p v-if="dialogError" class="text-sm text-red-500">{{ dialogError }}</p>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" class="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors" @click="closeDialog">取消</button>
            <button type="submit" :disabled="dialogSaving" class="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors disabled:opacity-50">
              {{ dialogSaving ? '保存中...' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { listCategories, createCategory, updateCategory, deleteCategory } from '@/api/categories'
import type { Category } from '@/api/categories'

const categories = ref<Category[]>([])
const loading = ref(true)
const showCreateDialog = ref(false)
const editingCat = ref<Category | null>(null)
const dialogSaving = ref(false)
const dialogError = ref('')

const dialogForm = reactive({
  name: '',
  display_name: '',
  icon: '',
  sort_order: 0,
})

async function fetchCategories() {
  loading.value = true
  try {
    const res = await listCategories()
    categories.value = res.data
  } finally {
    loading.value = false
  }
}

function startEdit(cat: Category) {
  editingCat.value = cat
  dialogForm.name = cat.name
  dialogForm.display_name = cat.display_name
  dialogForm.icon = cat.icon || ''
  dialogForm.sort_order = cat.sort_order
}

function closeDialog() {
  showCreateDialog.value = false
  editingCat.value = null
  dialogError.value = ''
  dialogForm.name = ''
  dialogForm.display_name = ''
  dialogForm.icon = ''
  dialogForm.sort_order = 0
}

async function handleSave() {
  dialogError.value = ''
  dialogSaving.value = true
  try {
    if (editingCat.value) {
      await updateCategory(editingCat.value.id, {
        display_name: dialogForm.display_name || undefined,
        icon: dialogForm.icon || undefined,
        sort_order: dialogForm.sort_order,
      })
    } else {
      if (!dialogForm.name || !dialogForm.display_name) {
        dialogError.value = '标识和显示名称为必填项'
        return
      }
      await createCategory({
        name: dialogForm.name,
        display_name: dialogForm.display_name,
        icon: dialogForm.icon || undefined,
        sort_order: dialogForm.sort_order,
      })
    }
    closeDialog()
    await fetchCategories()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    dialogError.value = err.response?.data?.detail || '操作失败'
  } finally {
    dialogSaving.value = false
  }
}

async function handleDelete(cat: Category) {
  if (!confirm(`确定删除分类「${cat.display_name}」吗？`)) return
  try {
    await deleteCategory(cat.id)
    await fetchCategories()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    alert(err.response?.data?.detail || '删除失败')
  }
}

onMounted(fetchCategories)
</script>
