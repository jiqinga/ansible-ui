import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { ShieldExclamationIcon, UserIcon } from '@heroicons/react/24/outline'
import { useAuth } from '../../contexts/AuthContext'
import { UserRole } from '../../types'

/**
 * 🔒 受保护路由组件属性
 */
interface ProtectedRouteProps {
  children: React.ReactNode
  requiredRole?: UserRole
  fallback?: React.ReactNode
}

/**
 * 🔒 受保护路由组件
 * 
 * 功能：
 * - 检查用户认证状态
 * - 验证用户权限
 * - 提供玻璃态加载和错误界面
 * - 自动重定向到登录页面
 */
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole,
  fallback,
}) => {
  const { state, checkPermission } = useAuth()
  const { t } = useTranslation()
  const location = useLocation()

  // 🔄 加载状态
  if (state.isLoading) {
    return (
      <div className="min-h-screen gradient-bg-primary flex items-center justify-center">
        <motion.div
          className="glass-container p-8 text-center max-w-md"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="w-12 h-12 border-3 border-white/30 border-t-white rounded-full animate-spin mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-glass-text-primary mb-2">
            🔍 验证身份中...
          </h2>
          <p className="text-glass-text-secondary">
            {t('auth.verifyingCredentials')}
          </p>
        </motion.div>
      </div>
    )
  }

  // 🚫 未认证用户重定向到登录页
  if (!state.isAuthenticated) {
    return (
      <Navigate 
        to="/login" 
        state={{ from: location.pathname }} 
        replace 
      />
    )
  }

  // 🔒 权限检查失败
  if (requiredRole && !checkPermission(requiredRole)) {
    if (fallback) {
      return <>{fallback}</>
    }

    return (
      <div className="min-h-screen gradient-bg-primary flex items-center justify-center p-4">
        <motion.div
          className="glass-container p-8 text-center max-w-md"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <div className="w-16 h-16 mx-auto mb-6 glass-container rounded-full flex items-center justify-center">
            <ShieldExclamationIcon className="w-8 h-8 text-red-500" />
          </div>
          
          <h2 className="text-2xl font-bold text-glass-text-primary mb-4">
            🚫 访问被拒绝
          </h2>
          
          <p className="text-glass-text-secondary mb-6">
            {t('auth.insufficientPermissions')}
          </p>
          
          <div className="space-y-3 text-sm text-glass-text-secondary">
            <div className="flex items-center justify-between p-3 glass-container rounded-glass-sm">
              <span>当前角色:</span>
              <span className="font-medium text-glass-text-primary">
                {state.user?.role === 'admin' ? '🔧 管理员' : 
                 state.user?.role === 'operator' ? '⚙️ 操作员' : '👁️ 查看者'}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 glass-container rounded-glass-sm">
              <span>需要角色:</span>
              <span className="font-medium text-glass-text-accent">
                {requiredRole === 'admin' ? '🔧 管理员' : 
                 requiredRole === 'operator' ? '⚙️ 操作员' : '👁️ 查看者'}
              </span>
            </div>
          </div>

          <motion.button
            onClick={() => window.history.back()}
            className="mt-6 glass-btn-secondary px-6 py-2 text-sm"
            whileHover={{ x: -2 }}
            whileTap={{ x: 0 }}
          >
            ← 返回上一页
          </motion.button>
        </motion.div>
      </div>
    )
  }

  // ✅ 认证和权限检查通过，渲染子组件
  return <>{children}</>
}

/**
 * 🔒 角色守卫组件
 * 用于在组件内部进行权限检查
 */
interface RoleGuardProps {
  children: React.ReactNode
  requiredRole: UserRole
  fallback?: React.ReactNode
  showMessage?: boolean
}

export const RoleGuard: React.FC<RoleGuardProps> = ({
  children,
  requiredRole,
  fallback,
  showMessage = true,
}) => {
  const { checkPermission } = useAuth()
  // const { t } = useTranslation()

  if (!checkPermission(requiredRole)) {
    if (fallback) {
      return <>{fallback}</>
    }

    if (!showMessage) {
      return null
    }

    return (
      <motion.div
        className="glass-container p-4 text-center"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <ShieldExclamationIcon className="w-8 h-8 text-yellow-500 mx-auto mb-2" />
        <p className="text-glass-text-secondary text-sm">
          ⚠️ 权限不足，无法访问此功能
        </p>
      </motion.div>
    )
  }

  return <>{children}</>
}

/**
 * 🔐 认证状态指示器组件
 */
export const AuthStatusIndicator: React.FC = () => {
  const { state } = useAuth()
  // const { t } = useTranslation() // 暂时不使用

  if (!state.isAuthenticated) {
    return null
  }

  return (
    <motion.div
      className="flex items-center space-x-2 text-sm text-glass-text-secondary"
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
    >
      <UserIcon className="w-4 h-4" />
      <span>{state.user?.username}</span>
      <span className="text-xs px-2 py-1 glass-container rounded-full">
        {state.user?.role === 'admin' ? '🔧' : 
         state.user?.role === 'operator' ? '⚙️' : '👁️'}
      </span>
    </motion.div>
  )
}

export default ProtectedRoute