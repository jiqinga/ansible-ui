import React from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { storageUtils } from '../../utils'

/**
 * 🔍 认证调试组件
 * 用于调试认证状态和本地存储
 */
const AuthDebug: React.FC = () => {
  const { state } = useAuth()

  const storedToken = storageUtils.getItem<string>('access_token') || localStorage.getItem('access_token')
  const storedUser = storageUtils.getItem<any>('auth_user')
  const storedRefreshToken = storageUtils.getItem<string>('refresh_token') || localStorage.getItem('refresh_token')

  return (
    <div className="fixed bottom-4 right-4 glass-container p-4 max-w-md text-xs">
      <h3 className="font-bold mb-2">🔍 认证调试信息</h3>
      
      <div className="space-y-2">
        <div>
          <strong>认证状态:</strong>
          <div className="ml-2">
            <div>isAuthenticated: {state.isAuthenticated ? '✅' : '❌'}</div>
            <div>isLoading: {state.isLoading ? '🔄' : '✅'}</div>
            <div>hasUser: {state.user ? '✅' : '❌'}</div>
            <div>hasToken: {state.token ? '✅' : '❌'}</div>
          </div>
        </div>

        <div>
          <strong>本地存储:</strong>
          <div className="ml-2">
            <div>access_token: {storedToken ? '✅' : '❌'}</div>
            <div>refresh_token: {storedRefreshToken ? '✅' : '❌'}</div>
            <div>auth_user: {storedUser ? '✅' : '❌'}</div>
          </div>
        </div>

        {state.user && (
          <div>
            <strong>用户信息:</strong>
            <div className="ml-2">
              <div>用户名: {state.user.username}</div>
              <div>角色: {state.user.role}</div>
              <div>邮箱: {state.user.email}</div>
            </div>
          </div>
        )}

        {state.token && (
          <div>
            <strong>Token信息:</strong>
            <div className="ml-2 break-all">
              {state.token.substring(0, 20)}...
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default AuthDebug