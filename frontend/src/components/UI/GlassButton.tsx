import React from 'react'
import { motion, HTMLMotionProps } from 'framer-motion'
import { cn } from '@/utils'

interface GlassButtonProps extends Omit<HTMLMotionProps<'button'>, 'children'> {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'warning' | 'ghost'
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  loading?: boolean
  disabled?: boolean
  fullWidth?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  className?: string
}

/**
 * 🎨 玻璃态按钮组件
 * 
 * 功能：
 * - 多种按钮变体和尺寸
 * - 加载状态支持
 * - 图标支持
 * - 动画效果
 */
const GlassButton: React.FC<GlassButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  fullWidth = false,
  leftIcon,
  rightIcon,
  className,
  ...motionProps
}) => {
  // 🎨 变体样式映射
  const variantStyles = {
    primary: 'bg-white/20 hover:bg-white/30 text-glass-text-primary border-white/30',
    secondary: 'bg-white/10 hover:bg-white/20 text-glass-text-secondary border-white/20',
    danger: 'bg-red-500/20 hover:bg-red-500/30 text-red-700 border-red-500/30',
    success: 'bg-green-500/20 hover:bg-green-500/30 text-green-700 border-green-500/30',
    warning: 'bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-700 border-yellow-500/30',
    ghost: 'bg-transparent hover:bg-white/10 text-glass-text-primary border-transparent',
  }

  // 🎨 尺寸样式映射
  const sizeStyles = {
    xs: 'px-2 py-1 text-xs rounded-glass-sm',
    sm: 'px-3 py-2 text-sm rounded-glass-sm',
    md: 'px-6 py-3 text-base rounded-glass',
    lg: 'px-8 py-4 text-lg rounded-glass',
    xl: 'px-10 py-5 text-xl rounded-glass-lg',
  }

  // 🎨 组合样式类
  const buttonClasses = cn(
    // 基础玻璃态样式
    'backdrop-blur-glass border transition-all duration-glass ease-glass',
    'font-medium cursor-pointer select-none',
    'focus:outline-none focus:ring-2 focus:ring-glass-text-accent/50 focus:ring-offset-2',
    
    // 变体和尺寸
    variantStyles[variant],
    sizeStyles[size],
    
    // 全宽
    fullWidth && 'w-full',
    
    // 禁用状态
    disabled && 'opacity-50 cursor-not-allowed pointer-events-none',
    
    // 加载状态
    loading && 'cursor-wait',
    
    // 响应式优化
    'glass-mobile:px-4 glass-mobile:py-2 glass-mobile:text-sm',
    
    // 自定义类名
    className
  )

  // 🎨 按钮动画配置
  const buttonAnimation = {
    whileHover: disabled || loading ? {} : { 
      y: -2,
      transition: { duration: 0.2, ease: 'easeOut' }
    },
    whileTap: disabled || loading ? {} : { 
      y: 0,
      transition: { duration: 0.1 }
    }
  }

  // 🎨 加载动画组件
  const LoadingSpinner = () => (
    <motion.div
      className="w-4 h-4 border-2 border-current border-t-transparent rounded-full"
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
    />
  )

  return (
    <motion.button
      className={buttonClasses}
      disabled={disabled || loading}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
      {...buttonAnimation}
      {...motionProps}
    >
      <div className="flex items-center justify-center gap-2">
        {loading ? (
          <LoadingSpinner />
        ) : (
          <>
            {leftIcon && <span className="flex-shrink-0">{leftIcon}</span>}
            <span className="flex-1">{children}</span>
            {rightIcon && <span className="flex-shrink-0">{rightIcon}</span>}
          </>
        )}
      </div>
    </motion.button>
  )
}

export default GlassButton