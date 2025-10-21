import React from 'react'
import { motion, HTMLMotionProps } from 'framer-motion'
import { cn } from '@/utils'

interface GlassCardProps extends Omit<HTMLMotionProps<'div'>, 'children'> {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'dark'
  hover?: boolean
  blur?: 'light' | 'normal' | 'strong'
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl'
  rounded?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  shadow?: 'none' | 'sm' | 'md' | 'lg'
  border?: boolean
  className?: string
}

/**
 * 🎨 玻璃态卡片组件
 * 
 * 功能：
 * - 多种玻璃态变体
 * - 可配置的模糊效果
 * - 响应式设计
 * - 动画支持
 */
const GlassCard: React.FC<GlassCardProps> = ({
  children,
  variant = 'primary',
  hover = true,
  blur = 'normal',
  padding = 'md',
  rounded = 'md',
  shadow = 'md',
  border = true,
  className,
  ...motionProps
}) => {
  // 🎨 变体样式映射
  const variantStyles = {
    primary: 'bg-white/70',
    secondary: 'bg-white/50',
    dark: 'bg-white/35',
  }

  // 🎨 模糊效果映射
  const blurStyles = {
    light: 'backdrop-blur-glass-light',
    normal: 'backdrop-blur-glass',
    strong: 'backdrop-blur-glass-strong',
  }

  // 🎨 内边距映射
  const paddingStyles = {
    none: '',
    sm: 'p-3',
    md: 'p-6',
    lg: 'p-8',
    xl: 'p-12',
  }

  // 🎨 圆角映射
  const roundedStyles = {
    sm: 'rounded-glass-sm',
    md: 'rounded-glass',
    lg: 'rounded-glass-lg',
    xl: 'rounded-3xl',
    full: 'rounded-full',
  }

  // 🎨 阴影映射
  const shadowStyles = {
    none: '',
    sm: 'shadow-glass-subtle',
    md: 'shadow-glass',
    lg: 'shadow-glass-hover',
  }

  // 🎨 组合样式类
  const cardClasses = cn(
    // 基础玻璃态样式
    variantStyles[variant],
    blurStyles[blur],
    paddingStyles[padding],
    roundedStyles[rounded],
    shadowStyles[shadow],
    
    // 边框
    border && 'border border-white/18',
    
    // 过渡动画
    'transition-all duration-glass ease-glass',
    
    // 悬浮效果
    hover && 'glass-hover',
    
    // 响应式优化
    'glass-mobile:backdrop-blur-glass-light glass-mobile:p-4',
    
    // 自定义类名
    className
  )

  // 🎨 悬浮动画配置
  const hoverAnimation = hover ? {
    whileHover: { 
      y: -5,
      transition: { duration: 0.2, ease: 'easeOut' }
    },
    whileTap: { 
      y: 0,
      transition: { duration: 0.1 }
    }
  } : {}

  return (
    <motion.div
      className={cardClasses}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      {...hoverAnimation}
      {...motionProps}
    >
      {children}
    </motion.div>
  )
}

export default GlassCard