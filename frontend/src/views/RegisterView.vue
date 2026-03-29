<template>
  <div class="min-h-screen relative flex flex-col items-center py-10 px-4"
    style="background: linear-gradient(135deg, #eef2ff 0%, #f0f9ff 50%, #faf5ff 100%)">

    <!-- 背景装饰圆（fixed 定位，不影响文档高度） -->
    <div class="fixed -top-32 -right-32 w-96 h-96 rounded-full opacity-30 pointer-events-none"
      style="background: radial-gradient(circle, #8b5cf6, transparent 70%)" />
    <div class="fixed -bottom-40 -left-40 w-[30rem] h-[30rem] rounded-full opacity-20 pointer-events-none"
      style="background: radial-gradient(circle, #6366f1, transparent 70%)" />

    <div class="relative w-full max-w-md my-auto">
      <!-- Logo 区 -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-4"
          style="background: linear-gradient(135deg, #6366f1, #8b5cf6)">
          <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 10V11" />
          </svg>
        </div>
        <h1 class="text-3xl font-extrabold tracking-tight"
          style="background: linear-gradient(135deg, #6366f1, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent">
          NodeVault
        </h1>
        <p class="text-gray-500 mt-1.5 text-sm">创建账号，开始管理算法节点</p>
      </div>

      <div class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl shadow-indigo-100/50 border border-white/60 px-8 py-8">
        <h2 class="text-lg font-semibold text-gray-800 mb-6">创建账号</h2>

        <!-- 主管申请成功提示 -->
        <div v-if="supervisorApplied"
          class="flex items-start gap-3 text-sm text-indigo-700 bg-indigo-50 border border-indigo-100 px-4 py-3 rounded-xl mb-5">
          <svg class="w-4 h-4 mt-0.5 shrink-0 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>主管申请已提交，管理员审批通过后权限将自动升级</span>
        </div>

        <form class="space-y-4" @submit.prevent="handleRegister">
          <!-- 昵称 -->
          <div class="space-y-1">
            <label class="text-sm font-medium text-gray-700">昵称 <span class="text-red-400">*</span></label>
            <div class="relative">
              <div class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <input v-model="form.display_name" type="text" autocomplete="nickname" placeholder="你的昵称，展示给其他人"
                :class="['w-full pl-10 pr-4 py-2.5 rounded-xl border text-sm transition focus:outline-none focus:ring-2',
                  errors.display_name ? 'border-red-300 focus:ring-red-400' : 'border-gray-200 focus:ring-indigo-400 focus:border-indigo-400']" />
            </div>
            <p v-if="errors.display_name" class="text-xs text-red-500">{{ errors.display_name }}</p>
          </div>

          <!-- 邮箱 -->
          <div class="space-y-1">
            <label class="text-sm font-medium text-gray-700">邮箱 <span class="text-red-400">*</span></label>
            <div class="relative">
              <div class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                </svg>
              </div>
              <input v-model="form.email" type="email" autocomplete="email" placeholder="your@email.com"
                :class="['w-full pl-10 pr-4 py-2.5 rounded-xl border text-sm transition focus:outline-none focus:ring-2',
                  errors.email ? 'border-red-300 focus:ring-red-400' : 'border-gray-200 focus:ring-indigo-400 focus:border-indigo-400']" />
            </div>
            <p v-if="errors.email" class="text-xs text-red-500">{{ errors.email }}</p>
          </div>

          <!-- 用户名 -->
          <div class="space-y-1">
            <label class="text-sm font-medium text-gray-700">用户名 <span class="text-red-400">*</span></label>
            <div class="relative">
              <div class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <input v-model="form.username" type="text" autocomplete="username" placeholder="仅限英文字母、数字、下划线，至少 8 位"
                :class="['w-full pl-10 pr-4 py-2.5 rounded-xl border text-sm transition focus:outline-none focus:ring-2',
                  errors.username ? 'border-red-300 focus:ring-red-400' : 'border-gray-200 focus:ring-indigo-400 focus:border-indigo-400']" />
            </div>
            <p class="text-xs text-gray-400">不能包含中文，至少 8 位，可用字母、数字、下划线、连字符</p>
            <p v-if="errors.username" class="text-xs text-red-500">{{ errors.username }}</p>
          </div>

          <!-- 密码 -->
          <div class="space-y-1">
            <label class="text-sm font-medium text-gray-700">密码 <span class="text-red-400">*</span></label>
            <div class="relative">
              <div class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <input v-model="form.password" :type="showPwd ? 'text' : 'password'"
                autocomplete="new-password" placeholder="至少 8 位，含大小写字母和数字"
                :class="['w-full pl-10 pr-10 py-2.5 rounded-xl border text-sm transition focus:outline-none focus:ring-2',
                  errors.password ? 'border-red-300 focus:ring-red-400' : 'border-gray-200 focus:ring-indigo-400 focus:border-indigo-400']" />
              <button type="button" class="absolute inset-y-0 right-3 flex items-center text-gray-400 hover:text-gray-600"
                @click="showPwd = !showPwd">
                <svg v-if="!showPwd" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                </svg>
              </button>
            </div>
            <p v-if="errors.password" class="text-xs text-red-500">{{ errors.password }}</p>
          </div>

          <!-- 身份选择 -->
          <div class="space-y-2">
            <label class="text-sm font-medium text-gray-700">加入身份</label>
            <div class="grid grid-cols-2 gap-2">
              <label
                class="flex items-center gap-2.5 px-3 py-2.5 rounded-xl border cursor-pointer transition-all"
                :class="form.requested_role === 2
                  ? 'border-indigo-400 bg-indigo-50 text-indigo-700'
                  : 'border-gray-200 hover:border-gray-300 text-gray-600'">
                <input type="radio" :value="2" v-model="form.requested_role" class="accent-indigo-600" />
                <div>
                  <div class="text-sm font-medium">普通用户</div>
                  <div class="text-xs text-gray-400">加入已有部门</div>
                </div>
              </label>
              <label
                class="flex items-center gap-2.5 px-3 py-2.5 rounded-xl border cursor-pointer transition-all"
                :class="form.requested_role === 1
                  ? 'border-violet-400 bg-violet-50 text-violet-700'
                  : 'border-gray-200 hover:border-gray-300 text-gray-600'">
                <input type="radio" :value="1" v-model="form.requested_role" class="accent-violet-600" />
                <div>
                  <div class="text-sm font-medium">申请主管</div>
                  <div class="text-xs text-gray-400">需等待审批</div>
                </div>
              </label>
            </div>
          </div>

          <!-- 部门选择（仅普通用户） -->
          <div v-if="form.requested_role === 2" class="space-y-1">
            <label class="text-sm font-medium text-gray-700">选择部门 <span class="text-red-400">*</span></label>
            <div class="relative">
              <div class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-2 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <select v-model="form.department_id"
                :class="['w-full pl-10 pr-4 py-2.5 rounded-xl border text-sm bg-white appearance-none focus:outline-none focus:ring-2 transition',
                  errors.department ? 'border-red-300 focus:ring-red-400 text-gray-700' : 'border-gray-200 focus:ring-indigo-400 focus:border-indigo-400 text-gray-700']">
                <option value="" disabled>— 请选择所属部门 —</option>
                <option v-for="dept in departments" :key="dept.id" :value="dept.id">
                  {{ dept.display_name || dept.slug }}
                </option>
              </select>
              <div class="absolute inset-y-0 right-3 flex items-center pointer-events-none">
                <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
            <p v-if="errors.department" class="text-xs text-red-500">{{ errors.department }}</p>
            <p v-if="deptLoadFailed" class="text-xs text-gray-400">部门列表加载失败，请刷新重试</p>
          </div>

          <!-- 主管申请提示 -->
          <div v-if="form.requested_role === 1"
            class="flex items-start gap-2 text-xs text-violet-600 bg-violet-50 border border-violet-100 px-3 py-2.5 rounded-xl">
            <svg class="w-3.5 h-3.5 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>提交后需等待管理员审批，审批期间账号可正常使用</span>
          </div>

          <div v-if="errorMsg"
            class="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100 px-4 py-3 rounded-xl">
            <svg class="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
            {{ errorMsg }}
          </div>

          <button type="submit" :disabled="loading"
            class="w-full py-2.5 rounded-xl text-white text-sm font-semibold transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            style="background: linear-gradient(135deg, #6366f1, #8b5cf6); box-shadow: 0 4px 15px rgba(99,102,241,0.4)">
            <svg v-if="loading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {{ loading ? '注册中...' : '创建账号' }}
          </button>
        </form>

        <p class="mt-6 text-center text-sm text-gray-500">
          已有账号？
          <RouterLink to="/login" class="font-medium text-indigo-600 hover:text-indigo-700">
            立即登录 →
          </RouterLink>
        </p>
      </div>

      <p class="mt-6 text-center text-xs text-gray-400">NodeVault · Enterprise AI Capability Registry</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import http from '@/api/http'

const router = useRouter()
const auth = useAuthStore()

interface DeptOption { id: string; slug: string; display_name: string | null }

const form = reactive({
  email: '',
  username: '',
  display_name: '',
  password: '',
  requested_role: 2,
  department_id: '',
})
const errors = reactive({ email: '', username: '', display_name: '', password: '', department: '' })
const errorMsg = ref('')
const loading = ref(false)
const showPwd = ref(false)
const supervisorApplied = ref(false)
const departments = ref<DeptOption[]>([])
const deptLoadFailed = ref(false)

async function loadDepartments() {
  try {
    const res = await http.get<{ items: DeptOption[] }>('/departments/public')
    departments.value = res.data?.items ?? (Array.isArray(res.data) ? res.data : [])
  } catch {
    deptLoadFailed.value = true
  }
}

onMounted(loadDepartments)

function validatePassword(pwd: string): string {
  if (pwd.length < 8) return '密码至少 8 位'
  if (!/[a-z]/.test(pwd)) return '密码需包含小写字母'
  if (!/[A-Z]/.test(pwd)) return '密码需包含大写字母'
  if (!/[0-9]/.test(pwd)) return '密码需包含数字'
  return ''
}

function validateUsername(name: string): string {
  if (name.length < 8) return '用户名至少 8 位'
  if (/[\u4e00-\u9fa5]/.test(name)) return '用户名不能包含中文'
  if (!/^[a-zA-Z0-9_][a-zA-Z0-9_-]{7,63}$/.test(name)) return '用户名只能包含字母、数字、下划线、连字符'
  return ''
}

async function handleRegister() {
  errors.email = ''
  errors.username = ''
  errors.display_name = ''
  errors.password = ''
  errors.department = ''
  errorMsg.value = ''
  supervisorApplied.value = false

  if (!form.display_name.trim()) { errors.display_name = '请输入昵称'; return }
  if (!form.email) { errors.email = '请输入邮箱'; return }
  if (!form.username) { errors.username = '请输入用户名'; return }
  const unameErr = validateUsername(form.username)
  if (unameErr) { errors.username = unameErr; return }
  const pwdErr = validatePassword(form.password)
  if (pwdErr) { errors.password = pwdErr; return }
  if (form.requested_role === 2 && !form.department_id) { errors.department = '请选择所属部门'; return }

  loading.value = true
  try {
    const payload: Parameters<typeof register>[0] = {
      email: form.email,
      username: form.username,
      display_name: form.display_name.trim(),
      password: form.password,
      requested_role: form.requested_role,
    }
    if (form.requested_role === 2) {
      payload.department_id = form.department_id
    }
    await register(payload)

    if (form.requested_role === 1) {
      // 主管申请账号未激活，不能自动登录，跳转到登录页展示等待审批提示
      router.push({ path: '/login', query: { pending_approval: '1' } })
      return
    }

    try {
      await auth.login({ identifier: form.email, password: form.password })
      router.push('/')
    } catch {
      router.push({ path: '/login', query: { registered: '1' } })
    }
    return
  } catch (e: unknown) {
    const err = e as { response?: { status?: number; data?: { error?: { message?: string; details?: { fields?: Record<string, string> } } } } }
    const apiError = err.response?.data?.error
    if (err.response?.status === 409) {
      errorMsg.value = '该邮箱已注册'
    } else if (err.response?.status === 422 && apiError?.details?.fields) {
      const fields = apiError.details.fields
      let handled = false
      for (const field of ['email', 'username', 'display_name', 'password'] as (keyof typeof errors)[]) {
        if (fields[field]) {
          errors[field] = fields[field]
          handled = true
        }
      }
      if (!handled) errorMsg.value = apiError.message || '注册失败，请检查填写内容'
    } else if (apiError?.message) {
      errorMsg.value = apiError.message
    } else {
      errorMsg.value = '注册失败，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}
</script>
