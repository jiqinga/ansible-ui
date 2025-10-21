import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { AuthState, User, LoginCredentials, ApiResponse } from '../types'
import { storageUtils } from '../utils'

/**
 * 🔐 认证上下文类型定义
 */
interface AuthContextType {
  state: AuthState
  login: (credentials: LoginCredentials) => Promise<{ success: boolean; message?: string }>
  logout: () => void
  refreshToken: () => Promise<boolean>
  updateUser: (user: Partial<User>) => void
  checkPermission: (requiredRole?: string) => boolean
}

/**
 * 🔄 认证状态动作类型
 */
type AuthAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'LOGIN_SUCCESS'; payload: { user: User; token: string } }
  | { type: 'LOGIN_FAILURE' }
  | { type: 'LOGOUT' }
  | { type: 'UPDATE_USER'; payload: Partial<User> }
  | { type: 'REFRESH_TOKEN'; payload: string }

/**
 * 🏪 初始认证状态
 */
const initialState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,
}

/**
 * 🔄 认证状态reducer
 */
const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      }
    
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        isAuthenticated: true,
        isLoading: false,
      }
    
    case 'LOGIN_FAILURE':
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      }
    
    case 'LOGOUT':
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      }
    
    case 'UPDATE_USER':
      return {
        ...state,
        user: state.user ? { ...state.user, ...action.payload } : null,
      }
    
    case 'REFRESH_TOKEN':
      return {
        ...state,
        token: action.payload,
      }
    
    default:
      return state
  }
}

/**
 * 🔐 认证上下文
 */
const AuthContext = createContext<AuthContextType | undefined>(undefined)

/**
 * 🔐 认证提供者组件
 */
interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState)
  const { t } = useTranslation()

  /**
   * 🚀 API基础URL配置
   * 注意：如果环境变量未设置，默认值已包含 /api/v1 路径
   */
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL 
    ? `${import.meta.env.VITE_API_BASE_URL}/api/v1`
    : 'http://localhost:8000/api/v1'

  /**
   * 🌐 API请求工具函数
   */
  const apiRequest = async <T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> => {
    const url = `${API_BASE_URL}${endpoint}`
    const token = state.token || storageUtils.getItem<string>('access_token') || localStorage.getItem('access_token')

    const defaultHeaders: HeadersInit = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    }

    if (token) {
      defaultHeaders.Authorization = `Bearer ${token}`
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...defaultHeaders,
          ...options.headers,
        },
      })

      // 检查响应是否为JSON格式
      const contentType = response.headers.get('content-type')
      let data: any = {}
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json()
      } else {
        data = { message: await response.text() }
      }

      if (!response.ok) {
        // 🚨 根据HTTP状态码提供友好的错误消息
        let errorMessage = data.detail || data.message || ''
        
        switch (response.status) {
          case 400:
            errorMessage = errorMessage || '请求参数错误，请检查输入信息'
            break
          case 401:
            // 🔐 针对认证失败提供更友好的提示
            if (endpoint.includes('/auth/login')) {
              errorMessage = '用户名或密码错误，请重新输入'
            } else {
              errorMessage = errorMessage || '登录已过期，请重新登录'
            }
            break
          case 403:
            errorMessage = errorMessage || '权限不足，无法访问此功能'
            break
          case 404:
            errorMessage = errorMessage || '请求的资源不存在'
            break
          case 422:
            errorMessage = errorMessage || '输入数据格式错误，请检查后重试'
            break
          case 429:
            errorMessage = errorMessage || '请求过于频繁，请稍后再试'
            break
          case 500:
            errorMessage = errorMessage || '服务器内部错误，请稍后重试'
            break
          case 502:
            errorMessage = errorMessage || '服务器网关错误，请稍后重试'
            break
          case 503:
            errorMessage = errorMessage || '服务暂时不可用，请稍后重试'
            break
          case 504:
            errorMessage = errorMessage || '请求超时，请检查网络连接'
            break
          default:
            errorMessage = errorMessage || `服务器错误 (${response.status})，请稍后重试`
        }
        
        throw new Error(errorMessage)
      }

      return {
        success: true,
        data: data.data || data,
        message: data.message,
        timestamp: new Date().toISOString(),
      }
    } catch (error) {
      console.error('API请求失败:', error)
      
      // 🌐 网络错误的友好提示
      let errorMessage = '网络连接失败，请检查网络设置'
      
      if (error instanceof Error) {
        // 如果是我们自定义的错误消息，直接使用
        if (error.message.includes('用户名或密码错误') || 
            error.message.includes('权限不足') ||
            error.message.includes('服务器错误') ||
            error.message.includes('请求')) {
          errorMessage = error.message
        } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
          errorMessage = '无法连接到服务器，请检查网络连接'
        } else if (error.message.includes('timeout')) {
          errorMessage = '请求超时，请检查网络连接后重试'
        }
      }
      
      return {
        success: false,
        error: errorMessage,
        timestamp: new Date().toISOString(),
      }
    }
  }

  /**
   * 🔐 用户登录
   */
  const login = async (credentials: LoginCredentials) => {
    dispatch({ type: 'SET_LOADING', payload: true })

    try {
      // 先进行登录获取Token
      const loginResponse = await apiRequest<{ access_token: string; refresh_token: string }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          username: credentials.username,
          password: credentials.password,
        }),
      })

      if (loginResponse.success && loginResponse.data) {
        const { access_token, refresh_token } = loginResponse.data
        
        // 使用Token获取用户信息
        const userResponse = await apiRequest<User>('/auth/me', {
          headers: {
            'Authorization': `Bearer ${access_token}`
          }
        })

        if (userResponse.success && userResponse.data) {
          const user = userResponse.data
          
          // 💾 保存认证信息到本地存储（使用与apiClient一致的键名）
          storageUtils.setItem('access_token', access_token)
          storageUtils.setItem('refresh_token', refresh_token)
          storageUtils.setItem('auth_user', user)
          
          // 同时保存到localStorage以确保apiClient可以访问
          localStorage.setItem('access_token', access_token)
          localStorage.setItem('refresh_token', refresh_token)
          
          if (credentials.rememberMe) {
            storageUtils.setItem('remember_me', true)
          }

          dispatch({
            type: 'LOGIN_SUCCESS',
            payload: { user, token: access_token },
          })

          return {
            success: true,
            message: t('auth.loginSuccess'),
          }
        } else {
          dispatch({ type: 'LOGIN_FAILURE' })
          return {
            success: false,
            message: '获取用户信息失败',
          }
        }
      } else {
        dispatch({ type: 'LOGIN_FAILURE' })
        return {
          success: false,
          message: loginResponse.error || t('auth.loginFailed'),
        }
      }
    } catch (error) {
      dispatch({ type: 'LOGIN_FAILURE' })
      return {
        success: false,
        message: error instanceof Error ? error.message : t('auth.networkError'),
      }
    }
  }

  /**
   * 🚪 用户登出
   */
  const logout = async () => {
    try {
      // 🌐 调用后端登出接口
      await apiRequest('/auth/logout', {
        method: 'POST',
      })
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      // 🧹 清理本地存储
      storageUtils.removeItem('access_token')
      storageUtils.removeItem('refresh_token')
      storageUtils.removeItem('auth_user')
      // 同时清理localStorage
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_info')
      storageUtils.removeItem('remember_me')
      
      dispatch({ type: 'LOGOUT' })
    }
  }

  /**
   * 🔄 刷新Token
   */
  const refreshToken = async (): Promise<boolean> => {
    try {
      const refreshTokenValue = storageUtils.getItem<string>('refresh_token')
      if (!refreshTokenValue) {
        console.warn('没有刷新Token，无法刷新')
        return false
      }

      const response = await apiRequest<{ access_token: string }>('/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({
          refresh_token: refreshTokenValue
        }),
      })

      if (response.success && response.data) {
        const { access_token } = response.data
        storageUtils.setItem('access_token', access_token)
        localStorage.setItem('access_token', access_token)
        dispatch({ type: 'REFRESH_TOKEN', payload: access_token })
        return true
      }
    } catch (error) {
      console.error('Token刷新失败:', error)
      logout()
    }
    
    return false
  }

  /**
   * 👤 更新用户信息
   */
  const updateUser = (userData: Partial<User>) => {
    dispatch({ type: 'UPDATE_USER', payload: userData })
    
    // 🔄 更新本地存储中的用户信息
    const currentUser = storageUtils.getItem<User>('auth_user')
    if (currentUser) {
      storageUtils.setItem('auth_user', { ...currentUser, ...userData })
    }
  }

  /**
   * 🔒 权限检查
   */
  const checkPermission = (requiredRole?: string): boolean => {
    if (!state.isAuthenticated || !state.user) {
      return false
    }

    if (!requiredRole) {
      return true
    }

    const roleHierarchy = {
      viewer: 1,
      operator: 2,
      admin: 3,
    }

    const userLevel = roleHierarchy[state.user.role as keyof typeof roleHierarchy] || 0
    const requiredLevel = roleHierarchy[requiredRole as keyof typeof roleHierarchy] || 0

    return userLevel >= requiredLevel
  }

  /**
   * 🔄 自动Token刷新
   */
  useEffect(() => {
    let refreshInterval: NodeJS.Timeout

    if (state.isAuthenticated && state.token) {
      // 🕒 每25分钟刷新一次Token（假设Token有效期30分钟）
      refreshInterval = setInterval(() => {
        refreshToken()
      }, 25 * 60 * 1000)
    }

    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
      }
    }
  }, [state.isAuthenticated, state.token])

  /**
   * 🔄 初始化认证状态
   */
  useEffect(() => {
    const initializeAuth = async () => {
      dispatch({ type: 'SET_LOADING', payload: true })

      try {
        const token = storageUtils.getItem<string>('access_token') || localStorage.getItem('access_token')
        const user = storageUtils.getItem<User>('auth_user')

        if (token && user) {
          // 🔍 验证Token是否仍然有效
          const response = await apiRequest<User>('/auth/me')
          
          if (response.success && response.data) {
            // 使用服务器返回的最新用户信息
            dispatch({
              type: 'LOGIN_SUCCESS',
              payload: { user: response.data, token },
            })
          } else {
            // Token无效，清理本地存储
            console.warn('Token验证失败，清理本地存储')
            storageUtils.removeItem('access_token')
            storageUtils.removeItem('auth_user')
            storageUtils.removeItem('remember_me')
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            dispatch({ type: 'LOGIN_FAILURE' })
          }
        } else {
          // 没有存储的认证信息
          dispatch({ type: 'LOGIN_FAILURE' })
        }
      } catch (error) {
        console.error('认证初始化失败:', error)
        // 清理可能损坏的本地存储
        storageUtils.removeItem('access_token')
        storageUtils.removeItem('auth_user')
        storageUtils.removeItem('remember_me')
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        dispatch({ type: 'LOGIN_FAILURE' })
      }
    }

    initializeAuth()
  }, [])

  const contextValue: AuthContextType = {
    state,
    login,
    logout,
    refreshToken,
    updateUser,
    checkPermission,
  }

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  )
}

/**
 * 🪝 使用认证上下文的Hook
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth必须在AuthProvider内部使用')
  }
  return context
}

export default AuthContext