import { useEffect, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'
// import { storageUtils } from '../utils'

/**
 * 🔄 Token自动刷新Hook
 * 
 * 功能：
 * - 监听Token过期时间
 * - 自动刷新Token
 * - 处理刷新失败情况
 * - 提供手动刷新功能
 */
export const useTokenRefresh = () => {
  const { state, refreshToken, logout } = useAuth()

  /**
   * 🔍 检查Token是否即将过期
   */
  const isTokenExpiringSoon = useCallback((token: string): boolean => {
    try {
      // 解析JWT Token的payload部分
      const payload = JSON.parse(atob(token.split('.')[1]))
      const currentTime = Math.floor(Date.now() / 1000)
      const expirationTime = payload.exp
      
      // 如果Token在5分钟内过期，则认为即将过期
      const bufferTime = 5 * 60 // 5分钟
      return expirationTime - currentTime <= bufferTime
    } catch (error) {
      console.error('解析Token失败:', error)
      return true // 解析失败时认为Token无效
    }
  }, [])

  /**
   * 🔄 自动刷新Token
   */
  const autoRefreshToken = useCallback(async () => {
    if (!state.token || !state.isAuthenticated) {
      return
    }

    try {
      if (isTokenExpiringSoon(state.token)) {
        console.log('🔄 Token即将过期，开始自动刷新...')
        const success = await refreshToken()
        
        if (success) {
          console.log('✅ Token刷新成功')
        } else {
          console.warn('⚠️ Token刷新失败，将执行登出')
          logout()
        }
      }
    } catch (error) {
      console.error('Token自动刷新错误:', error)
      logout()
    }
  }, [state.token, state.isAuthenticated, isTokenExpiringSoon, refreshToken, logout])

  /**
   * 🕒 设置定时检查
   */
  useEffect(() => {
    if (!state.isAuthenticated || !state.token) {
      return
    }

    // 立即检查一次
    autoRefreshToken()

    // 每分钟检查一次Token状态
    const interval = setInterval(autoRefreshToken, 60 * 1000)

    return () => {
      clearInterval(interval)
    }
  }, [state.isAuthenticated, state.token, autoRefreshToken])

  /**
   * 🔄 手动刷新Token
   */
  const manualRefresh = useCallback(async (): Promise<boolean> => {
    if (!state.isAuthenticated) {
      return false
    }

    try {
      const success = await refreshToken()
      if (!success) {
        logout()
      }
      return success
    } catch (error) {
      console.error('手动刷新Token失败:', error)
      logout()
      return false
    }
  }, [state.isAuthenticated, refreshToken, logout])

  /**
   * 🔍 获取Token剩余时间
   */
  const getTokenTimeRemaining = useCallback((): number | null => {
    if (!state.token) {
      return null
    }

    try {
      const payload = JSON.parse(atob(state.token.split('.')[1]))
      const currentTime = Math.floor(Date.now() / 1000)
      const expirationTime = payload.exp
      
      return Math.max(0, expirationTime - currentTime)
    } catch (error) {
      console.error('获取Token剩余时间失败:', error)
      return null
    }
  }, [state.token])

  /**
   * 🔍 检查Token是否有效
   */
  const isTokenValid = useCallback((): boolean => {
    if (!state.token) {
      return false
    }

    try {
      const payload = JSON.parse(atob(state.token.split('.')[1]))
      const currentTime = Math.floor(Date.now() / 1000)
      const expirationTime = payload.exp
      
      return expirationTime > currentTime
    } catch (error) {
      console.error('验证Token有效性失败:', error)
      return false
    }
  }, [state.token])

  return {
    manualRefresh,
    getTokenTimeRemaining,
    isTokenValid,
    isTokenExpiringSoon: state.token ? isTokenExpiringSoon(state.token) : false,
  }
}

/**
 * 🔄 页面可见性变化时刷新Token的Hook
 */
export const useVisibilityRefresh = () => {
  const { manualRefresh } = useTokenRefresh()
  const { state } = useAuth()

  useEffect(() => {
    const handleVisibilityChange = () => {
      // 当页面从隐藏状态变为可见状态时，检查并刷新Token
      if (!document.hidden && state.isAuthenticated) {
        console.log('🔄 页面重新可见，检查Token状态...')
        manualRefresh()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [manualRefresh, state.isAuthenticated])
}

/**
 * 🌐 网络重连时刷新Token的Hook
 */
export const useNetworkRefresh = () => {
  const { manualRefresh } = useTokenRefresh()
  const { state } = useAuth()

  useEffect(() => {
    const handleOnline = () => {
      // 当网络重新连接时，检查并刷新Token
      if (state.isAuthenticated) {
        console.log('🌐 网络重新连接，检查Token状态...')
        setTimeout(() => {
          manualRefresh()
        }, 1000) // 延迟1秒确保网络稳定
      }
    }

    window.addEventListener('online', handleOnline)

    return () => {
      window.removeEventListener('online', handleOnline)
    }
  }, [manualRefresh, state.isAuthenticated])
}

export default useTokenRefresh