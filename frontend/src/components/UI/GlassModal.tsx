import React, { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { createPortal } from 'react-dom'
import { cn } from '@/utils'

interface GlassModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  closeOnOverlayClick?: boolean
  closeOnEscape?: boolean
  showCloseButton?: boolean
  className?: string
  overlayClassName?: string
}

/**
 * 🎨 玻璃态模态框组件
 * 
 * 功能：
 * - 多种尺寸选项
 * - 动画进入/退出效果
 * - 键盘和点击关闭支持
 * - Portal 渲染
 * - 焦点管理
 */
const GlassModal: React.FC<GlassModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  closeOnOverlayClick = true,
  closeOnEscape = true,
  showCloseButton = true,
  className,
  overlayClassName,
}) => {
  // 🎨 尺寸样式映射
  const sizeStyles = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-full mx-4',
  }

  // 🎨 模态框样式类
  const modalClasses = cn(
    // 基础玻璃态样式
    'bg-white/30 backdrop-blur-glass-strong border border-white/20',
    'rounded-glass-lg shadow-glass-strong',
    'relative w-full max-h-[90vh] overflow-hidden',
    
    // 尺寸
    sizeStyles[size],
    
    // 响应式优化
    'glass-mobile:mx-4 glass-mobile:max-h-[95vh]',
    
    // 自定义类名
    className
  )

  // 🎨 遮罩样式类
  const overlayClasses = cn(
    'fixed inset-0 bg-black/50 backdrop-blur-sm z-50',
    'flex items-center justify-center p-4',
    overlayClassName
  )

  // ⌨️ 键盘事件处理
  useEffect(() => {
    if (!isOpen || !closeOnEscape) return

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, closeOnEscape, onClose])

  // 🔒 滚动锁定
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  // 🎨 动画变体
  const overlayVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
    exit: { opacity: 0 }
  }

  const modalVariants = {
    hidden: { 
      opacity: 0, 
      y: 20
    },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: {
        type: 'spring',
        damping: 25,
        stiffness: 300
      }
    },
    exit: { 
      opacity: 0, 
      y: 20,
      transition: {
        duration: 0.2
      }
    }
  }

  // 🎨 关闭按钮图标
  const CloseIcon = () => (
    <svg
      className="w-6 h-6"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M6 18L18 6M6 6l12 12"
      />
    </svg>
  )

  // 🚪 遮罩点击处理
  const handleOverlayClick = (event: React.MouseEvent) => {
    if (closeOnOverlayClick && event.target === event.currentTarget) {
      onClose()
    }
  }

  // 🌐 Portal 渲染
  const modalContent = (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className={overlayClasses}
          data-testid="glass-modal-overlay"
          variants={overlayVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          onClick={handleOverlayClick}
        >
          <motion.div
            className={modalClasses}
            data-testid="glass-modal-content"
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            onClick={(e) => e.stopPropagation()}
          >
            {/* 📋 模态框头部 */}
            {(title || showCloseButton) && (
              <div className="flex items-center justify-between p-6 border-b border-white/10">
                {title && (
                  <h2 className="text-xl font-semibold text-glass-text-primary">
                    {title}
                  </h2>
                )}
                {showCloseButton && (
                  <motion.button
                    className="p-2 text-glass-text-secondary hover:text-glass-text-primary 
                             hover:bg-white/10 rounded-glass-sm transition-all duration-glass"
                    onClick={onClose}
                    aria-label="关闭模态框"
                    whileHover={{ opacity: 0.8 }}
                    whileTap={{ opacity: 0.6 }}
                  >
                    <CloseIcon />
                  </motion.button>
                )}
              </div>
            )}

            {/* 📄 模态框内容 */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
              {children}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )

  // 🌐 使用 Portal 渲染到 body
  return createPortal(modalContent, document.body)
}

export default GlassModal
