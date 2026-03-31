<template>
  <div class="space-y-5">
    <!-- 统计卡片 -->
    <div class="grid grid-cols-3 gap-4">
      <div v-for="card in statCards" :key="card.label"
        class="bg-white rounded-2xl p-5 flex items-center gap-4"
        style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
        <div class="w-10 h-10 rounded-xl flex items-center justify-center" :style="`background:${card.bg}`">
          <svg class="w-5 h-5" :style="`color:${card.color}`" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" v-html="card.icon"></svg>
        </div>
        <div>
          <div class="text-2xl font-bold text-gray-900">{{ card.value }}</div>
          <div class="text-xs text-gray-500">{{ card.label }}</div>
        </div>
      </div>
    </div>

    <!-- 筛选 Tab -->
    <div class="bg-white rounded-2xl px-5 py-3 flex items-center gap-1" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
      <button
        v-for="tab in tabs" :key="tab.value"
        @click="currentStatus = tab.value; page = 1; load()"
        class="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
        :class="currentStatus === tab.value
          ? 'bg-indigo-600 text-white'
          : 'text-gray-500 hover:bg-gray-100'">
        {{ tab.label }}
      </button>
    </div>

    <!-- 申请列表 -->
    <div class="bg-white rounded-2xl overflow-hidden" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
      <div v-if="loading" class="flex items-center justify-center h-48">
        <div class="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
      <table v-else class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-100">
            <th class="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">申请人</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">申请角色</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">申请理由</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">申请时间</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">状态</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="app in applications" :key="app.id" class="hover:bg-gray-50/60 transition-colors">
            <td class="px-5 py-3.5">
              <div class="font-medium text-gray-900">{{ app.display_name || app.username || '—' }}</div>
              <div class="text-xs text-gray-400">{{ app.email }}</div>
            </td>
            <td class="px-4 py-3.5">
              <span class="px-2 py-0.5 text-xs font-medium rounded-full bg-violet-50 text-violet-700">
                {{ app.requested_role_label }}
              </span>
            </td>
            <td class="px-4 py-3.5 text-gray-500 max-w-xs truncate">{{ app.reason || '—' }}</td>
            <td class="px-4 py-3.5 text-xs text-gray-400">{{ app.created_at?.slice(0, 10) }}</td>
            <td class="px-4 py-3.5">
              <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
                :class="{
                  'bg-amber-50 text-amber-700': app.status === 'pending',
                  'bg-green-50 text-green-700': app.status === 'approved',
                  'bg-red-50 text-red-600': app.status === 'rejected',
                }">
                <span class="w-1.5 h-1.5 rounded-full"
                  :class="{
                    'bg-amber-500': app.status === 'pending',
                    'bg-green-500': app.status === 'approved',
                    'bg-red-500': app.status === 'rejected',
                  }"></span>
                {{ statusLabel(app.status) }}
              </span>
            </td>
            <td class="px-4 py-3.5">
              <div v-if="app.status === 'pending'" class="flex items-center gap-2">
                <button @click="openApproveModal(app)"
                  :disabled="processing === app.id"
                  class="px-3 py-1 text-xs font-medium rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition-colors">
                  通过
                </button>
                <button @click="openRejectModal(app)"
                  :disabled="processing === app.id"
                  class="px-3 py-1 text-xs font-medium rounded-lg bg-red-50 text-red-600 hover:bg-red-100 disabled:opacity-50 transition-colors">
                  拒绝
                </button>
              </div>
              <span v-else-if="app.review_note" class="text-xs text-gray-400 italic">{{ app.review_note }}</span>
            </td>
          </tr>
          <tr v-if="!loading && applications.length === 0">
            <td colspan="6" class="text-center py-16 text-gray-400">暂无申请记录</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="flex items-center justify-center gap-2">
      <button v-for="p in totalPages" :key="p" @click="page = p; load()"
        class="w-8 h-8 rounded-lg text-sm font-medium transition-colors"
        :class="p === page ? 'bg-indigo-600 text-white' : 'text-gray-500 hover:bg-gray-100'">
        {{ p }}
      </button>
    </div>

    <!-- 拒绝备注弹窗 -->
    <Teleport to="body">
      <div v-if="rejectModal.open" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
        <div class="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-sm mx-4">
          <h3 class="text-base font-semibold text-gray-900 mb-4">拒绝申请</h3>
          <p class="text-sm text-gray-500 mb-3">申请人：<span class="font-medium text-gray-800">{{ rejectModal.app?.username }}</span></p>
          <textarea v-model="rejectModal.note" rows="3" placeholder="填写拒绝理由（可选）"
            class="w-full px-3 py-2 rounded-xl border border-gray-200 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-red-300"></textarea>
          <div class="flex justify-end gap-2 mt-4">
            <button @click="rejectModal.open = false" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-900">取消</button>
            <button @click="handleReject" :disabled="processing === rejectModal.app?.id"
              class="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors">
              {{ processing === rejectModal.app?.id ? '处理中...' : '确认拒绝' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 审批 + 分配部门弹窗 -->
    <Teleport to="body">
      <div v-if="approveModal.open" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
        <div class="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-sm mx-4">
          <h3 class="text-base font-semibold text-gray-900 mb-4">批准主管申请</h3>
          <div class="space-y-1 mb-4 text-sm text-gray-500">
            <p>申请人：<span class="font-medium text-gray-800">{{ approveModal.app?.display_name || approveModal.app?.username }}</span></p>
            <p class="text-xs text-gray-400">{{ approveModal.app?.email }}</p>
          </div>

          <!-- 部门选择 -->
          <div class="mb-4">
            <label class="block text-xs font-medium text-gray-600 mb-1.5">分配到部门 <span class="text-red-400">*</span></label>
            <div v-if="approveModal.loadingDepts" class="flex items-center gap-2 text-xs text-gray-400 py-2">
              <div class="w-3.5 h-3.5 border border-indigo-400 border-t-transparent rounded-full animate-spin"></div>
              加载部门中…
            </div>
            <p v-else-if="approveModal.loadError" class="text-xs text-red-500 py-1">{{ approveModal.loadError }}</p>
            <select v-else v-model="approveModal.departmentId"
              class="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-300 transition"
              :disabled="availableDepartments.length === 0">
              <option value="" disabled>
                {{ availableDepartments.length === 0 ? '当前无可分配的空余部门' : '— 请选择部门 —' }}
              </option>
              <option v-for="dept in availableDepartments" :key="dept.id" :value="dept.id">
                {{ dept.organization_name + ' / ' + dept.team_name }}
              </option>
            </select>
            <p v-if="!approveModal.loadingDepts && availableDepartments.length === 0"
              class="text-xs text-amber-600 mt-1">所有部门均已有主管，请先创建新部门</p>
          </div>

          <!-- 审批备注 -->
          <div class="mb-5">
            <label class="block text-xs font-medium text-gray-600 mb-1.5">审批备注（可选）</label>
            <textarea v-model="approveModal.note" rows="2" placeholder="填写审批备注"
              class="w-full px-3 py-2 rounded-xl border border-gray-200 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-300"></textarea>
          </div>

          <div class="flex justify-end gap-2">
            <button @click="approveModal.open = false" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-900">取消</button>
            <button
              @click="handleApprove"
              :disabled="processing === approveModal.app?.id || !approveModal.departmentId || availableDepartments.length === 0"
              class="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors">
              {{ processing === approveModal.app?.id ? '处理中...' : '确认批准' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { listRoleApplications, approveApplication, rejectApplication, type RoleApplicationItem } from '@/api/roleApplications'
import { listAllDepartments, type AdminDepartmentListItem } from '@/api/admin'

const applications = ref<RoleApplicationItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const processing = ref<string | null>(null)
const currentStatus = ref<string>('')

const rejectModal = reactive<{ open: boolean; app: RoleApplicationItem | null; note: string }>({
  open: false,
  app: null,
  note: '',
})

const approveModal = reactive<{
  open: boolean
  app: RoleApplicationItem | null
  departmentId: string
  note: string
  departments: AdminDepartmentListItem[]
  loadingDepts: boolean
  loadError: string
}>({
  open: false,
  app: null,
  departmentId: '',
  note: '',
  departments: [],
  loadingDepts: false,
  loadError: '',
})

const availableDepartments = computed(() =>
  approveModal.departments.filter(d => !d.supervisor_username)
)

const totalPages = computed(() => Math.ceil(total.value / pageSize))

const tabs = [
  { label: '全部', value: '' },
  { label: '待审批', value: 'pending' },
  { label: '已批准', value: 'approved' },
  { label: '已拒绝', value: 'rejected' },
]

const statCards = computed(() => [
  {
    label: '待审批',
    value: applications.value.filter(a => a.status === 'pending').length || (currentStatus.value === 'pending' ? total.value : '—'),
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>',
    bg: '#fef3c7', color: '#d97706',
  },
  {
    label: '已批准',
    value: currentStatus.value === 'approved' ? total.value : '—',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>',
    bg: '#f0fdf4', color: '#16a34a',
  },
  {
    label: '已拒绝',
    value: currentStatus.value === 'rejected' ? total.value : '—',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/>',
    bg: '#fef2f2', color: '#dc2626',
  },
])

function statusLabel(s: string) {
  return { pending: '待审批', approved: '已批准', rejected: '已拒绝' }[s] ?? s
}

async function load() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: page.value, page_size: pageSize }
    if (currentStatus.value) params.status = currentStatus.value
    const res = await listRoleApplications(params)
    applications.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

async function openApproveModal(app: RoleApplicationItem) {
  approveModal.app = app
  approveModal.departmentId = ''
  approveModal.note = ''
  approveModal.departments = []
  approveModal.loadError = ''
  approveModal.loadingDepts = true
  approveModal.open = true
  try {
    const res = await listAllDepartments({ page: 1, page_size: 200 })
    approveModal.departments = res.data.items ?? []
  } catch {
    approveModal.loadError = '部门列表加载失败，请关闭后重试'
  } finally {
    approveModal.loadingDepts = false
  }
}

async function handleApprove() {
  if (!approveModal.app || !approveModal.departmentId) return
  processing.value = approveModal.app.id
  try {
    await approveApplication(approveModal.app.id, {
      department_id: approveModal.departmentId,
      review_note: approveModal.note || undefined,
    })
    approveModal.open = false
    await load()
  } finally {
    processing.value = null
  }
}

function openRejectModal(app: RoleApplicationItem) {
  rejectModal.app = app
  rejectModal.note = ''
  rejectModal.open = true
}

async function handleReject() {
  if (!rejectModal.app) return
  processing.value = rejectModal.app.id
  try {
    await rejectApplication(rejectModal.app.id, rejectModal.note || undefined)
    rejectModal.open = false
    await load()
  } finally {
    processing.value = null
  }
}

onMounted(() => load())
</script>
