/**
 * 🎨 玻璃态主题配置
 * 
 * 统一管理玻璃态设计系统的主题配置
 */

// 🎨 颜色配置
export const glassColors = {
  // 背景渐变
  gradients: {
    primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    secondary: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    tertiary: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    sunset: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%)',
    ocean: 'linear-gradient(135deg, #667db6 0%, #0082c8 25%, #0082c8 50%, #667db6 100%)',
  },
  
  // 玻璃态背景
  glass: {
    primary: 'rgba(255, 255, 255, 0.6)',
    secondary: 'rgba(255, 255, 255, 0.45)',
    tertiary: 'rgba(255, 255, 255, 0.3)',
    hover: 'rgba(255, 255, 255, 0.75)',
    active: 'rgba(255, 255, 255, 0.85)',
  },
  
  // 边框颜色
  borders: {
    primary: 'rgba(255, 255, 255, 0.35)',
    secondary: 'rgba(255, 255, 255, 0.3)',
    accent: 'rgba(102, 126, 234, 0.35)',
    error: 'rgba(239, 68, 68, 0.35)',
    success: 'rgba(34, 197, 94, 0.35)',
    warning: 'rgba(245, 158, 11, 0.35)',
  },
  
  // 文字颜色
  text: {
    primary: '#1f2937',
    secondary: '#475569',
    white: '#ffffff',
    accent: '#4f46e5',
    error: '#dc2626',
    success: '#16a34a',
    warning: '#d97706',
  },
} as const

// 🎨 尺寸配置
export const glassSizes = {
  // 圆角
  borderRadius: {
    sm: '8px',
    md: '15px',
    lg: '24px',
    xl: '32px',
    full: '9999px',
  },
  
  // 间距
  spacing: {
    xs: '0.5rem',   // 8px
    sm: '0.75rem',  // 12px
    md: '1rem',     // 16px
    lg: '1.5rem',   // 24px
    xl: '2rem',     // 32px
    '2xl': '3rem',  // 48px
  },
  
  // 字体大小
  fontSize: {
    xs: '0.75rem',   // 12px
    sm: '0.875rem',  // 14px
    md: '1rem',      // 16px
    lg: '1.125rem',  // 18px
    xl: '1.25rem',   // 20px
    '2xl': '1.5rem', // 24px
  },
  
  // 组件尺寸
  component: {
    xs: { padding: '0.5rem 0.75rem', fontSize: '0.75rem' },
    sm: { padding: '0.75rem 1rem', fontSize: '0.875rem' },
    md: { padding: '1rem 1.5rem', fontSize: '1rem' },
    lg: { padding: '1.25rem 2rem', fontSize: '1.125rem' },
    xl: { padding: '1.5rem 2.5rem', fontSize: '1.25rem' },
  },
} as const

// 🎨 阴影配置
export const glassShadows = {
  subtle: '0 4px 16px 0 rgba(31, 38, 135, 0.2)',
  normal: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
  hover: '0 15px 35px 0 rgba(31, 38, 135, 0.4)',
  strong: '0 20px 40px 0 rgba(31, 38, 135, 0.4)',
  focus: '0 0 0 3px rgba(102, 126, 234, 0.1)',
} as const

// 🎨 模糊效果配置
export const glassBlur = {
  light: '5px',
  normal: '10px',
  strong: '20px',
  ultra: '30px',
} as const

// 🎨 动画配置
export const glassAnimations = {
  // 持续时间
  duration: {
    fast: '150ms',
    normal: '300ms',
    slow: '400ms',
  },
  
  // 缓动函数
  easing: {
    ease: 'cubic-bezier(0.4, 0, 0.2, 1)',
    bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
    spring: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
  },
  
  // 预设动画
  presets: {
    fadeIn: {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      transition: { duration: 0.3 },
    },
    slideUp: {
      initial: { opacity: 0, y: 20 },
      animate: { opacity: 1, y: 0 },
      transition: { duration: 0.3, ease: 'easeOut' },
    },
    scaleIn: {
      initial: { opacity: 0, y: 10 },
      animate: { opacity: 1, y: 0 },
      transition: { duration: 0.2, ease: 'easeOut' },
    },
    // ⚠️ 避免使用 scale 以防止字体模糊
    // 使用 y 轴位移和透明度变化代替
    hover: {
      whileHover: { y: -2 },
      transition: { duration: 0.2, ease: 'easeOut' },
    },
    tap: {
      whileTap: { y: 0 },
      transition: { duration: 0.1 },
    },
  },
} as const

// 🎨 响应式断点
export const glassBreakpoints = {
  mobile: '768px',
  tablet: '1024px',
  desktop: '1280px',
  wide: '1536px',
} as const

// 🎨 Z-index 层级
export const glassZIndex = {
  dropdown: 10,
  sticky: 20,
  fixed: 30,
  modal: 40,
  popover: 50,
  tooltip: 60,
  toast: 70,
} as const

// 🎨 主题变体
export const glassVariants = {
  // 按钮变体
  button: {
    primary: {
      background: glassColors.glass.primary,
      border: glassColors.borders.primary,
      color: glassColors.text.primary,
      hover: {
        background: glassColors.glass.hover,
      },
    },
    secondary: {
      background: glassColors.glass.secondary,
      border: glassColors.borders.secondary,
      color: glassColors.text.secondary,
      hover: {
        background: glassColors.glass.primary,
      },
    },
    danger: {
      background: 'rgba(239, 68, 68, 0.2)',
      border: glassColors.borders.error,
      color: glassColors.text.error,
      hover: {
        background: 'rgba(239, 68, 68, 0.3)',
      },
    },
    success: {
      background: 'rgba(34, 197, 94, 0.2)',
      border: glassColors.borders.success,
      color: glassColors.text.success,
      hover: {
        background: 'rgba(34, 197, 94, 0.3)',
      },
    },
  },
  
  // 卡片变体
  card: {
    primary: {
      background: glassColors.glass.primary,
      border: glassColors.borders.primary,
      shadow: glassShadows.normal,
    },
    secondary: {
      background: glassColors.glass.secondary,
      border: glassColors.borders.secondary,
      shadow: glassShadows.subtle,
    },
    dark: {
      background: glassColors.glass.tertiary,
      border: glassColors.borders.secondary,
      shadow: glassShadows.normal,
    },
  },
} as const

// 🎨 工具函数
export const glassUtils = {
  // 获取响应式值
  responsive: (mobile: string, tablet?: string, desktop?: string) => ({
    [`@media (max-width: ${glassBreakpoints.mobile})`]: mobile,
    [`@media (min-width: ${glassBreakpoints.mobile}) and (max-width: ${glassBreakpoints.tablet})`]: tablet || mobile,
    [`@media (min-width: ${glassBreakpoints.tablet})`]: desktop || tablet || mobile,
  }),
  
  // 生成玻璃态样式
  glassStyle: (variant: keyof typeof glassVariants.card = 'primary') => ({
    background: glassVariants.card[variant].background,
    backdropFilter: `blur(${glassBlur.normal})`,
    border: `1px solid ${glassVariants.card[variant].border}`,
    borderRadius: glassSizes.borderRadius.md,
    boxShadow: glassVariants.card[variant].shadow,
    transition: `all ${glassAnimations.duration.normal} ${glassAnimations.easing.ease}`,
  }),
  
  // 生成悬浮效果
  hoverEffect: () => ({
    '&:hover': {
      transform: 'translateY(-5px)',
      boxShadow: glassShadows.hover,
      background: glassColors.glass.hover,
    },
  }),
} as const

// 🎨 默认主题配置
export const defaultGlassTheme = {
  colors: glassColors,
  sizes: glassSizes,
  shadows: glassShadows,
  blur: glassBlur,
  animations: glassAnimations,
  breakpoints: glassBreakpoints,
  zIndex: glassZIndex,
  variants: glassVariants,
  utils: glassUtils,
} as const

export type GlassTheme = typeof defaultGlassTheme