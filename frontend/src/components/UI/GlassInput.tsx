import React, { forwardRef } from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/utils'

interface GlassInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string
  error?: string
  helperText?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  variant?: 'primary' | 'secondary' | 'search'
  size?: 'sm' | 'md' | 'lg'
  fullWidth?: boolean
  loading?: boolean
  className?: string
  containerClassName?: string
}

/**
 * 🎨 玻璃态输入框组件
 * 
 * 功能：
 * - 多种输入框变体和尺寸
 * - 标签和错误提示支持
 * - 图标支持
 * - 加载状态
 * - 动画效果
 */
const GlassInput = forwardRef<HTMLInputElement, GlassInputProps>(({
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  variant = 'primary',
  size = 'md',
  fullWidth = true,
  loading = false,
  className,
  containerClassName,
  ...inputProps
}, ref) => {
  // 🎨 变体样式映射
  const variantStyles = {
    primary: 'bg-white/15 border-white/20 text-glass-text-primary placeholder:text-glass-text-secondary/60',
    secondary: 'bg-white/10 border-white/15 text-glass-text-secondary placeholder:text-glass-text-secondary/50',
    search: 'bg-white/15 border-white/20 text-glass-text-primary placeholder:text-glass-text-secondary/60 pl-10',
  }

  // 🎨 尺寸样式映射
  const sizeStyles = {
    sm: 'px-3 py-2 text-sm rounded-glass-sm',
    md: 'px-4 py-3 text-base rounded-glass-sm',
    lg: 'px-5 py-4 text-lg rounded-glass',
  }

  // 🎨 输入框样式类
  const inputClasses = cn(
    // 基础玻璃态样式
    'backdrop-blur-glass border transition-all duration-glass ease-glass',
    'focus:outline-none focus:ring-2 focus:ring-glass-text-accent/50 focus:border-glass-text-accent/60',
    'disabled:opacity-50 disabled:cursor-not-allowed',
    
    // 变体和尺寸
    variantStyles[variant],
    sizeStyles[size],
    
    // 全宽
    fullWidth && 'w-full',
    
    // 错误状态
    error && 'border-red-500/50 focus:border-red-500/60 focus:ring-red-500/30',
    
    // 图标间距调整
    leftIcon && variant !== 'search' && 'pl-10',
    rightIcon && 'pr-10',
    
    // 响应式优化
    'glass-mobile:px-3 glass-mobile:py-2 glass-mobile:text-sm',
    
    // 自定义类名
    className
  )

  // 🎨 容器样式类
  const containerClasses = cn(
    'relative',
    fullWidth && 'w-full',
    containerClassName
  )

  // 🎨 标签样式类
  const labelClasses = cn(
    'block text-sm font-medium mb-2',
    error ? 'text-red-600' : 'text-glass-text-primary'
  )

  // 🎨 错误提示样式类
  const errorClasses = cn(
    'mt-1 text-sm text-red-600'
  )

  // 🎨 帮助文本样式类
  const helperClasses = cn(
    'mt-1 text-sm text-glass-text-secondary'
  )

  // 🎨 加载动画组件
  const LoadingSpinner = () => (
    <motion.div
      className="w-4 h-4 border-2 border-glass-text-secondary border-t-transparent rounded-full"
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
    />
  )

  return (
    <motion.div
      className={containerClasses}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
    >
      {/* 🏷️ 标签 */}
      {label && (
        <label className={labelClasses}>
          {label}
        </label>
      )}

      {/* 📝 输入框容器 */}
      <div className="relative">
        {/* 🎨 左侧图标 */}
        {leftIcon && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-glass-text-secondary">
            {leftIcon}
          </div>
        )}

        {/* 📝 输入框 */}
        <input
          ref={ref}
          className={inputClasses}
          {...inputProps}
        />

        {/* 🎨 右侧图标或加载状态 */}
        {(rightIcon || loading) && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-glass-text-secondary">
            {loading ? <LoadingSpinner /> : rightIcon}
          </div>
        )}
      </div>

      {/* ⚠️ 错误提示 */}
      {error && (
        <motion.div
          className={errorClasses}
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          transition={{ duration: 0.2 }}
        >
          {error}
        </motion.div>
      )}

      {/* 💡 帮助文本 */}
      {helperText && !error && (
        <div className={helperClasses}>
          {helperText}
        </div>
      )}
    </motion.div>
  )
})

GlassInput.displayName = 'GlassInput'

export default GlassInput