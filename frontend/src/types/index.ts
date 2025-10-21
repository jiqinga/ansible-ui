/**
 * 🎯 全局类型定义
 */

// 🌐 国际化相关类型
export interface Language {
  code: string
  name: string
  flag: string
}

// 🔐 认证相关类型
export interface User {
  id: string
  username: string
  email: string
  role: UserRole
  avatar?: string
  lastLogin?: string
  createdAt: string
}

export type UserRole = 'admin' | 'operator' | 'viewer'

export interface LoginCredentials {
  username: string
  password: string
  rememberMe?: boolean
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

// 📊 API响应类型
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
  timestamp: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// 🎨 UI组件通用类型
export interface BaseComponentProps {
  className?: string
  children?: React.ReactNode
}

export interface GlassComponentProps extends BaseComponentProps {
  variant?: 'primary' | 'secondary' | 'dark'
  hover?: boolean
  blur?: 'light' | 'normal' | 'strong'
}

// 🎨 按钮组件类型
export interface ButtonProps extends BaseComponentProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'success'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
  onClick?: () => void
  type?: 'button' | 'submit' | 'reset'
}

// 🎨 输入框组件类型
export interface InputProps extends BaseComponentProps {
  label?: string
  placeholder?: string
  type?: 'text' | 'password' | 'email' | 'number' | 'search'
  value: string
  onChange: (value: string) => void
  error?: string
  disabled?: boolean
  required?: boolean
}

// 📋 表单相关类型
export interface FormField {
  name: string
  label: string
  type: 'text' | 'password' | 'email' | 'number' | 'select' | 'textarea' | 'checkbox'
  value: any
  placeholder?: string
  required?: boolean
  options?: { label: string; value: any }[]
  validation?: {
    required?: boolean
    minLength?: number
    maxLength?: number
    pattern?: RegExp
    custom?: (value: any) => string | null
  }
}

export interface FormErrors {
  [fieldName: string]: string
}

// 🎨 模态框类型
export interface ModalProps extends BaseComponentProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
  closeOnOverlayClick?: boolean
  showCloseButton?: boolean
}

// 🎨 通知类型
export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
  actions?: NotificationAction[]
}

export interface NotificationAction {
  label: string
  onClick: () => void
  variant?: 'primary' | 'secondary'
}

// 📊 统计数据类型
export interface StatCard {
  title: string
  value: string | number
  icon: React.ComponentType<any>
  color: string
  bgColor: string
  trend?: {
    value: number
    isPositive: boolean
  }
}

// 🎨 主题相关类型
export interface Theme {
  name: string
  colors: {
    primary: string
    secondary: string
    accent: string
    background: string
    surface: string
    text: {
      primary: string
      secondary: string
      accent: string
    }
  }
  glassmorphism: {
    background: string
    border: string
    blur: string
    shadow: string
  }
}

// 🔧 设置相关类型
export interface AppSettings {
  language: string
  theme: string
  timezone: string
  dateFormat: string
  timeFormat: string
  pageSize: number
  autoSave: boolean
  confirmDelete: boolean
  showTooltips: boolean
  enableAnimations: boolean
  reducedMotion: boolean
  highContrast: boolean
  fontSize: 'sm' | 'md' | 'lg'
  compactMode: boolean
}

// 🎯 路由相关类型
export interface RouteConfig {
  path: string
  component: React.ComponentType
  exact?: boolean
  protected?: boolean
  roles?: UserRole[]
  title?: string
  icon?: React.ComponentType<any>
}

// 🎨 动画相关类型
export interface AnimationConfig {
  duration: number
  ease: string
  delay?: number
  stagger?: number
}

export interface PageTransition {
  initial: any
  animate: any
  exit: any
  transition: AnimationConfig
}

// 🔍 搜索相关类型
export interface SearchFilters {
  query?: string
  category?: string
  status?: string
  dateRange?: {
    start: string
    end: string
  }
  tags?: string[]
}

export interface SearchResult<T> {
  items: T[]
  total: number
  query: string
  filters: SearchFilters
  suggestions?: string[]
}

// 📱 响应式相关类型
export type Breakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'

export interface ResponsiveValue<T> {
  xs?: T
  sm?: T
  md?: T
  lg?: T
  xl?: T
  '2xl'?: T
}

// 🎨 图标相关类型
export interface IconProps {
  className?: string
  size?: number | string
  color?: string
}

// 🔄 加载状态类型
export interface LoadingState {
  isLoading: boolean
  error: string | null
  lastUpdated?: string
}

// 🎯 事件处理类型
export type EventHandler<T = any> = (event: T) => void
export type AsyncEventHandler<T = any> = (event: T) => Promise<void>

// 🎨 工具类型
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>
export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}