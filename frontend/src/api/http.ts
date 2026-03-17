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
