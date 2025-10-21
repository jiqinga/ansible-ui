import React, { createContext, useContext, useReducer, ReactNode } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  InformationCircleIcon, 
  XCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'
import { Notification } from '../types'
import { randomUtils } from '../utils'

/**
 * 🔔 通知上下文类型定义
 */
interface NotificationContextType {
  notifications: Notification[]
  addNotification: (notification: Omit<Notification, 'id'>) => string
  removeNotification: (id: string) => void
  clearAllNotifications: () => void
  success: (title: string, message?: string, duration?: number) => string
  error: (title: string, message?: string, duration?: number) => string
  warning: (title: string, message?: string, duration?: number) => string
  info: (title: string, message?: string, duration?: number) => string
}

/**
 * 🔄 通知状态动作类型
 */
type NotificationActionType = 
  | { type: 'ADD_NOTIFICATION'; payload: Notification }
  | { type: 'REMOVE_NOTIFICATION'; payload: string }
  | { type: 'CLEAR_ALL' }

/**
 * 🏪 初始通知状态
 */
const initialState: Notification[] = []

/**
 * 🔄 通知状态reducer
 */
const notificationReducer = (state: Notification[], action: NotificationActionType): Notification[] => {
  switch (action.type) {
    case 'ADD_NOTIFICATION':
      return [...state, action.payload]
    
    case 'REMOVE_NOTIFICATION':
      return state.filter(notification => notification.id !== action.payload)
    
    case 'CLEAR_ALL':
      return []
    
    default:
      return state
  }
}

/**
 * 🔔 通知上下文
 */
const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

/**
 * 🔔 通知提供者组件
 */
interface NotificationProviderProps {
  children: ReactNode
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [notifications, dispatch] = useReducer(notificationReducer, initialState)

  /**
   * ➕ 添加通知
   */
  const addNotification = (notification: Omit<Notification, 'id'>): string => {
    const id = randomUtils.generateId()
    const newNotification: Notification = {
      ...notification,
      id,
      duration: notification.duration || 5000,
    }

    dispatch({ type: 'ADD_NOTIFICATION', payload: newNotification })

    // 🕒 自动移除通知
    if (newNotification.duration && newNotification.duration > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, newNotification.duration)
    }

    return id
  }

  /**
   * ➖ 移除通知
   */
  const removeNotification = (id: string) => {
    dispatch({ type: 'REMOVE_NOTIFICATION', payload: id })
  }

  /**
   * 🧹 清空所有通知
   */
  const clearAllNotifications = () => {
    dispatch({ type: 'CLEAR_ALL' })
  }

  /**
   * ✅ 成功通知
   */
  const success = (title: string, message?: string, duration = 5000): string => {
    return addNotification({
      type: 'success',
      title,
      message,
      duration,
    })
  }

  /**
   * ❌ 错误通知
   */
  const error = (title: string, message?: string, duration = 8000): string => {
    return addNotification({
      type: 'error',
      title,
      message,
      duration,
    })
  }

  /**
   * ⚠️ 警告通知
   */
  const warning = (title: string, message?: string, duration = 6000): string => {
    return addNotification({
      type: 'warning',
      title,
      message,
      duration,
    })
  }

  /**
   * ℹ️ 信息通知
   */
  const info = (title: string, message?: string, duration = 5000): string => {
    return addNotification({
      type: 'info',
      title,
      message,
      duration,
    })
  }

  const contextValue: NotificationContextType = {
    notifications,
    addNotification,
    removeNotification,
    clearAllNotifications,
    success,
    error,
    warning,
    info,
  }

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}
      <NotificationContainer />
    </NotificationContext.Provider>
  )
}

/**
 * 🔔 通知容器组件
 */
const NotificationContainer: React.FC = () => {
  const { notifications, removeNotification } = useNotification()

  return (
    <div className="fixed top-4 right-4 z-[9999] space-y-2 max-w-sm">
      <AnimatePresence>
        {notifications.map((notification) => (
          <NotificationItem
            key={notification.id}
            notification={notification}
            onRemove={() => removeNotification(notification.id)}
          />
        ))}
      </AnimatePresence>
    </div>
  )
}

/**
 * 🔔 通知项组件
 */
interface NotificationItemProps {
  notification: Notification
  onRemove: () => void
}

const NotificationItem: React.FC<NotificationItemProps> = ({ notification, onRemove }) => {
  const getIcon = () => {
    switch (notification.type) {
      case 'success':
        return <CheckCircleIcon className="w-5 h-5 text-green-600" />
      case 'error':
        return <XCircleIcon className="w-5 h-5 text-red-600" />
      case 'warning':
        return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600" />
      case 'info':
        return <InformationCircleIcon className="w-5 h-5 text-blue-600" />
      default:
        return <InformationCircleIcon className="w-5 h-5 text-blue-600" />
    }
  }

  const getColorClasses = () => {
    switch (notification.type) {
      case 'success':
        return 'border-green-500/30 bg-green-500/10'
      case 'error':
        return 'border-red-500/30 bg-red-500/10'
      case 'warning':
        return 'border-yellow-500/30 bg-yellow-500/10'
      case 'info':
        return 'border-blue-500/30 bg-blue-500/10'
      default:
        return 'border-blue-500/30 bg-blue-500/10'
    }
  }

  return (
    <motion.div
      className={`glass-container p-4 border ${getColorClasses()} min-w-80 max-w-sm`}
      initial={{ opacity: 0, x: 300 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 300 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      layout
    >
      <div className="flex items-start space-x-3">
        {/* 🎨 图标 */}
        <div className="flex-shrink-0 mt-0.5">
          {getIcon()}
        </div>

        {/* 📝 内容 */}
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-glass-text-primary mb-1">
            {notification.title}
          </h4>
          {notification.message && (
            <p className="text-sm text-glass-text-secondary">
              {notification.message}
            </p>
          )}
          
          {/* 🎯 操作按钮 */}
          {notification.actions && notification.actions.length > 0 && (
            <div className="mt-3 flex space-x-2">
              {notification.actions.map((action, index) => (
                <button
                  key={index}
                  onClick={action.onClick}
                  className={`text-xs px-3 py-1 rounded-glass-sm transition-colors ${
                    action.variant === 'primary'
                      ? 'bg-glass-text-accent/20 text-glass-text-accent hover:bg-glass-text-accent/30'
                      : 'bg-white/10 text-glass-text-secondary hover:bg-white/20'
                  }`}
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* ❌ 关闭按钮 */}
        <button
          onClick={onRemove}
          className="flex-shrink-0 text-glass-text-secondary hover:text-glass-text-primary transition-colors"
        >
          <XMarkIcon className="w-4 h-4" />
        </button>
      </div>
    </motion.div>
  )
}

/**
 * 🪝 使用通知上下文的Hook
 */
export const useNotification = (): NotificationContextType => {
  const context = useContext(NotificationContext)
  if (context === undefined) {
    throw new Error('useNotification必须在NotificationProvider内部使用')
  }
  return context
}

export default NotificationContext