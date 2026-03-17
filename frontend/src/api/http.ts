import axios from 'axios'
import router from '@/router'

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
      localStorage.removeItem('token')
      router.push('/login')
    }
    return Promise.reject(error)
  },
)

export default http
