import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { createPortal } from 'react-dom'
import { cn } from '@/utils'

interface GlassTooltipProps {
  content: React.ReactNode
  children: React.ReactNode
  placement?: 'top' | 'bottom' | 'left' | 'right'
  trigger?: 'hover' | 'click' | 'focus'
  delay?: number
  offset?: number
  className?: string
  contentClassName?: string
  disabled?: boolean
}

/**
 * 🎨 玻璃态工具提示组件
 * 
 * 功能：
 * - 多种位置选项
 * - 多种触发方式
 * - 延迟显示支持
 * - 动画效果
 * - Portal 渲染
 */
const GlassTooltip: React.FC<GlassTooltipProps> = ({
  content,
  children,
  placement = 'top',
  trigger = 'hover',
  delay = 500,
  offset = 8,
  className,
  contentClassName,
  disabled = false,
}) => {
  const [isVisible, setIsVisible] = useState(false)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const triggerRef = useRef<HTMLDivElement>(null)
  const timeoutRef = useRef<NodeJS.Timeout>()

  // 🎨 工具提示样式类
  const tooltipClasses = cn(
    // 基础玻璃态样式
    'bg-white/90 backdrop-blur-glass border border-white/20',
    'rounded-glass-sm shadow-glass-subtle',
    'px-3 py-2 text-sm text-glass-text-primary',
    'pointer-events-none select-none',
    'max-w-xs break-words',
    'z-50 fixed',
    
    // 响应式优化
    'glass-mobile:text-xs glass-mobile:px-2 glass-mobile:py-1',
    
    // 自定义类名
    contentClassName
  )

  // 🎨 箭头样式映射
  const arrowStyles = {
    top: 'top-full left-1/2 transform -translate-x-1/2 border-t-white/90 border-t-4 border-x-transparent border-x-4 border-b-0',
    bottom: 'bottom-full left-1/2 transform -translate-x-1/2 border-b-white/90 border-b-4 border-x-transparent border-x-4 border-t-0',
    left: 'left-full top-1/2 transform -translate-y-1/2 border-l-white/90 border-l-4 border-y-transparent border-y-4 border-r-0',
    right: 'right-full top-1/2 transform -translate-y-1/2 border-r-white/90 border-r-4 border-y-transparent border-y-4 border-l-0',
  }

  // 📍 计算位置
  const calculatePosition = () => {
    if (!triggerRef.current) return

    const triggerRect = triggerRef.current.getBoundingClientRect()
    const scrollX = window.pageXOffset
    const scrollY = window.pageYOffset

    let x = 0
    let y = 0

    switch (placement) {
      case 'top':
        x = triggerRect.left + triggerRect.width / 2 + scrollX
        y = triggerRect.top - offset + scrollY
        break
      case 'bottom':
        x = triggerRect.left + triggerRect.width / 2 + scrollX
        y = triggerRect.bottom + offset + scrollY
        break
      case 'left':
        x = triggerRect.left - offset + scrollX
        y = triggerRect.top + triggerRect.height / 2 + scrollY
        break
      case 'right':
        x = triggerRect.right + offset + scrollX
        y = triggerRect.top + triggerRect.height / 2 + scrollY
        break
    }

    setPosition({ x, y })
  }

  // 🎯 显示工具提示
  const showTooltip = () => {
    if (disabled) return

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    timeoutRef.current = setTimeout(() => {
      calculatePosition()
      setIsVisible(true)
    }, trigger === 'hover' ? delay : 0)
  }

  // 🚫 隐藏工具提示
  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setIsVisible(false)
  }

  // 🎯 切换工具提示
  const toggleTooltip = () => {
    if (isVisible) {
      hideTooltip()
    } else {
      showTooltip()
    }
  }

  // 📱 事件处理器
  const eventHandlers = {
    hover: {
      onMouseEnter: showTooltip,
      onMouseLeave: hideTooltip,
    },
    click: {
      onClick: toggleTooltip,
    },
    focus: {
      onFocus: showTooltip,
      onBlur: hideTooltip,
    },
  }

  // 🔄 窗口大小变化时重新计算位置
  useEffect(() => {
    if (isVisible) {
      const handleResize = () => calculatePosition()
      window.addEventListener('resize', handleResize)
      window.addEventListener('scroll', handleResize)
      
      return () => {
        window.removeEventListener('resize', handleResize)
        window.removeEventListener('scroll', handleResize)
      }
    }
  }, [isVisible, placement])

  // 🧹 清理定时器
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  // 🎨 动画变体
  const tooltipVariants = {
    hidden: { 
      opacity: 0, 
      y: placement === 'top' ? 10 : placement === 'bottom' ? -10 : 0,
      x: placement === 'left' ? 10 : placement === 'right' ? -10 : 0,
    },
    visible: { 
      opacity: 1, 
      y: 0,
      x: 0,
      transition: {
        type: 'spring',
        damping: 20,
        stiffness: 300,
        duration: 0.2
      }
    },
    exit: { 
      opacity: 0, 
      transition: {
        duration: 0.15
      }
    }
  }

  // 🎨 工具提示内容
  const tooltipContent = (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          className={tooltipClasses}
          style={{
            left: placement === 'left' || placement === 'right' 
              ? placement === 'left' ? position.x - 8 : position.x + 8
              : position.x,
            top: placement === 'top' || placement === 'bottom'
              ? placement === 'top' ? position.y - 8 : position.y + 8  
              : position.y,
            transform: placement === 'left' || placement === 'right'
              ? 'translateX(-100%) translateY(-50%)'
              : 'translateX(-50%)',
          }}
          variants={tooltipVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
        >
          {content}
          
          {/* 🎯 箭头 */}
          <div 
            className={cn('absolute w-0 h-0', arrowStyles[placement])}
          />
        </motion.div>
      )}
    </AnimatePresence>
  )

  return (
    <>
      <div
        ref={triggerRef}
        className={cn('inline-block', className)}
        {...eventHandlers[trigger]}
      >
        {children}
      </div>
      
      {/* 🌐 Portal 渲染工具提示 */}
      {createPortal(tooltipContent, document.body)}
    </>
  )
}

export default GlassTooltip