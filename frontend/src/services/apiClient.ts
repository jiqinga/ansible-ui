/**
 * 🌐 API客户端服务
 * 
 * 提供统一的HTTP请求接口，包含：
 * - 请求拦截器（添加认证token）
 * - 响应拦截器（处理错误和token刷新）
 * - 中文错误消息处理
 * - 请求缓存和性能优化
 */

import axios, { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { cachedRequest } from '../utils/requestOptimizer'

// 扩展axios配置类型以支持metadata
declare module 'axios' {
  interface InternalAxiosRequestConfig {
    metadata?: {
      startTime: Date
    }
  }
}

// 🔧 API配置
// 开发环境使用空字符串，让请求通过Vite代理
// 生产环境需要设置完整的API地址
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const REQUEST_TIMEOUT = 30000 // 30秒超时

/**
 * 创建axios实例
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
})

/**
 * 🔐 请求拦截器 - 添加认证token
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 从localStorage获取token
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // 添加请求时间戳
    config.metadata = { startTime: new Date() }
    
    return config
  },
  (error) => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

/**
 * 📥 响应拦截器 - 处理错误和token刷新
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // 计算请求耗时
    const endTime = new Date()
    const startTime = response.config.metadata?.startTime
    if (startTime) {
      const duration = endTime.getTime() - startTime.getTime()
      console.debug(`API请求耗时: ${duration}ms - ${response.config.method?.toUpperCase()} ${response.config.url}`)
    }
    
    return response
  },
  async (error) => {
    const originalRequest = error.config
    
    // 🔄 处理token过期，尝试刷新
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken
          })
          
          const { access_token, refresh_token: newRefreshToken } = response.data
          
          // 更新存储的token
          localStorage.setItem('access_token', access_token)
          if (newRefreshToken) {
            localStorage.setItem('refresh_token', newRefreshToken)
          }
          
          // 重新发送原始请求
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return apiClient(originalRequest)
        }
      } catch (refreshError) {
        console.error('Token刷新失败:', refreshError)
        // 清除无效token并跳转到登录页
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }
    
    // 🌐 处理网络错误
    if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
      error.message = '网络连接失败，请检查网络设置'
    }
    
    // ⏱️ 处理超时错误
    if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
      error.message = '请求超时，请稍后重试'
    }
    
    // 🔍 处理HTTP状态码错误
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 400:
          error.message = data?.detail || '请求参数错误'
          break
        case 401:
          error.message = '身份验证失败，请重新登录'
          break
        case 403:
          error.message = '权限不足，无法访问此资源'
          break
        case 404:
          error.message = '请求的资源不存在'
          break
        case 409:
          // 处理冲突错误（如文件名重复）
          error.message = data?.detail || '资源冲突'
          break
        case 422:
          // 处理验证错误
          if (data?.detail && Array.isArray(data.detail)) {
            const validationErrors = data.detail.map((err: any) => 
              `${err.loc?.join('.')} ${err.msg}`
            ).join(', ')
            error.message = `数据验证失败: ${validationErrors}`
          } else {
            error.message = data?.detail || '数据验证失败'
          }
          break
        case 429:
          error.message = '请求过于频繁，请稍后重试'
          break
        case 500:
          error.message = '服务器内部错误，请联系管理员'
          break
        case 502:
          error.message = '网关错误，服务暂时不可用'
          break
        case 503:
          error.message = '服务暂时不可用，请稍后重试'
          break
        default:
          error.message = data?.detail || `请求失败 (${status})`
      }
    }
    
    console.error('API请求错误:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      message: error.message,
      data: error.response?.data
    })
    
    return Promise.reject(error)
  }
)

/**
 * 🚀 带缓存的GET请求
 */
export async function cachedGet<T = any>(
  url: string,
  ttl: number = 60000 // 默认缓存60秒
): Promise<T> {
  const cacheKey = `GET:${url}`
  return cachedRequest(cacheKey, async () => {
    const response = await apiClient.get<T>(url)
    return response.data
  }, ttl)
}

/**
 * 🛠️ API工具函数
 */
export const apiUtils = {
  /**
   * 检查是否已认证
   */
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token')
  },
  
  /**
   * 获取当前用户token
   */
  getToken(): string | null {
    return localStorage.getItem('access_token')
  },
  
  /**
   * 设置认证token
   */
  setTokens(accessToken: string, refreshToken?: string): void {
    localStorage.setItem('access_token', accessToken)
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken)
    }
  },
  
  /**
   * 清除认证信息
   */
  clearAuth(): void {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
  },
  
  /**
   * 构建查询参数
   */
  buildQueryParams(params: Record<string, any>): string {
    const searchParams = new URLSearchParams()
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        if (Array.isArray(value)) {
          value.forEach(item => searchParams.append(key, String(item)))
        } else {
          searchParams.append(key, String(value))
        }
      }
    })
    
    return searchParams.toString()
  },
  
  /**
   * 处理文件上传
   */
  async uploadFile(
    url: string, 
    file: File, 
    onProgress?: (progress: number) => void
  ): Promise<AxiosResponse> {
    const formData = new FormData()
    formData.append('file', file)
    
    return apiClient.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })
  },
  
  /**
   * 下载文件
   */
  async downloadFile(url: string, filename?: string): Promise<void> {
    const response = await apiClient.get(url, {
      responseType: 'blob',
    })
    
    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  },
  
  /**
   * 批量GET请求（带缓存）
   */
  async batchGet<T = any>(
    urls: string[],
    ttl: number = 60000
  ): Promise<T[]> {
    const promises = urls.map(url => cachedGet<T>(url, ttl))
    return Promise.all(promises)
  }
}

export default apiClient