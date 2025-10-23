import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ExclamationTriangleIcon, XMarkIcon } from '@heroicons/react/24/outline'
import GlassButton from './GlassButton'

/**
 * 🎨 玻璃态确认对话框组件
 * 
 * 功能：
 * - 符合项目玻璃态设计风格
 * - 支持自定义标题、消息和按钮文本
 * - 流畅的动画效果
 * - 键盘快捷键支持（ESC取消，Enter确认）
 */

interface GlassConfirmDialogProps {
  /** 是否显示对话框 */
  isOpen: boolean
  /** 对话框标题 */
  title: string
  /** 对话框消息内容 */
  message: string
  /** 确认按钮文本 */
  confirmText?: string
  /** 取消按钮文本 */
  cancelText?: string
  /** 确认按钮样式变体 */
  confirmVariant?: 'primary' | 'danger'
  /** 确认回调 */
  onConfirm: () => void
  /** 取消回调 */
  onCancel: () => void
  /** 图标类型 */
  icon?: 'warning' | 'danger' | 'info'
}

const GlassConfirmDialog: React.FC<GlassConfirmDialogProps> = ({
  isOpen,
  title,
  message,
  confirmText = '确认',
  cancelText = '取消',
  confirmVariant = 'danger',
  onConfirm,
  onCancel,
  icon = 'warning'
}) => {
  // ⌨️ 键盘事件处理
  React.useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCancel()
      } else if (e.key === 'Enter') {
        onConfirm()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onConfirm, onCancel])

  // 🎨 图标渲染
  const renderIcon = () => {
    const iconClasses = "w-12 h-12"
    
    switch (icon) {
      case 'danger':
        return <ExclamationTriangleIcon className={`${iconClasses} text-red-400`} />
      case 'warning':
        return <ExclamationTriangleIcon className={`${iconClasses} text-yellow-400`} />
      case 'info':
        return <ExclamationTriangleIcon className={`${iconClasses} text-blue-400`} />
      default:
        return <ExclamationTriangleIcon className={`${iconClasses} text-yellow-400`} />
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* 🌫️ 背景遮罩 */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onCancel}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          >
            {/* 🎨 对话框容器 */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              onClick={(e) => e.stopPropagation()}
              className="relative w-full max-w-md"
            >
              {/* 玻璃态卡片 */}
              <div className="bg-white/25 backdrop-blur-xl rounded-2xl border border-white/20 shadow-2xl overflow-hidden">
                {/* 关闭按钮 */}
                <button
                  onClick={onCancel}
                  className="absolute top-4 right-4 p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-all duration-200 group"
                  aria-label="关闭"
                >
                  <XMarkIcon className="w-5 h-5 text-white/70 group-hover:text-white" />
                </button>

                {/* 内容区域 */}
                <div className="p-6">
                  {/* 图标 */}
                  <div className="flex justify-center mb-4">
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: 0.1, type: 'spring', stiffness: 200 }}
                    >
                      {renderIcon()}
                    </motion.div>
                  </div>

                  {/* 标题 */}
                  <h3 className="text-xl font-bold text-white text-center mb-3">
                    {title}
                  </h3>

                  {/* 消息内容 */}
                  <p className="text-white/80 text-center mb-6 whitespace-pre-line">
                    {message}
                  </p>

                  {/* 按钮组 */}
                  <div className="flex gap-3">
                    <GlassButton
                      variant="ghost"
                      onClick={onCancel}
                      className="flex-1"
                    >
                      {cancelText}
                    </GlassButton>
                    <GlassButton
                      onClick={onConfirm}
                      className={`flex-1 ${
                        confirmVariant === 'danger'
                          ? 'bg-red-500/30 hover:bg-red-500/40 border-red-500/50'
                          : ''
                      }`}
                    >
                      {confirmText}
                    </GlassButton>
                  </div>

                  {/* 快捷键提示 */}
                  <div className="mt-4 text-center text-xs text-white/50">
                    <kbd className="px-2 py-1 bg-white/10 rounded">ESC</kbd> 取消 · 
                    <kbd className="px-2 py-1 bg-white/10 rounded ml-2">Enter</kbd> 确认
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export default GlassConfirmDialog
