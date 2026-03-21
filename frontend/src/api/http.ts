import axios from 'axios'
import router from '@/router'
import { useAuthStore } from '@/stores/auth'

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => {
    // 自动解包 ApiResponse：成功响应 {success: true, data: ...} → response.data = data
    if (
      response.data &&
      typeof response.data === 'object' &&
      'success' in response.data &&
      response.data.success === true
    ) {
      response.data = response.data.data
    }
    return response
  },
  (error) => {
    // 统一提取错误消息：后端错误格式为 { error: { message } }，暂存为 error.uiMessage 供视图层直接使用
    if (error.response?.data) {
      const data = error.response.data
      const rawMsg: string | null =
        data?.error?.message ||
        data?.detail ||
        data?.message ||
        null
      // 将服务端通用英文错误消息本地化
      const i18n: Record<string, string> = {
        'Internal server error': '服务器内部错误，请稍后重试',
        'Not Found': '请求的资源不存在',
        'Unauthorized': '请先登录',
        'Forbidden': '无权限执行此操作',
        'Bad Request': '请求参数有误',
        'Method Not Allowed': '请求方式不支持',
      }
      error.uiMessage = (rawMsg && i18n[rawMsg]) || rawMsg
    }

    if (error.response?.status === 401) {
      // 避免在登录请求本身失败时触发 session expired 弹窗
      const isLoginRequest = error.config?.url?.includes('/auth/login')
      if (!isLoginRequest) {
        try {
          const authStore = useAuthStore()
          authStore.notifySessionExpired()
        } catch {
          localStorage.removeItem('token')
          router.push('/login')
        }
      }
    }
    return Promise.reject(error)
  },
)

export default http
