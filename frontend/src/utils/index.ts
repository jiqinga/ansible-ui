import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { format, formatDistanceToNow, parseISO } from 'date-fns'
import { zhCN } from 'date-fns/locale'

/**
 * 🎨 CSS类名合并工具
 * 结合clsx和tailwind-merge，智能合并CSS类名
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * 🕒 时间格式化工具
 */
export const timeUtils = {
  /**
   * 格式化日期时间
   */
  formatDateTime: (date: string | Date, formatStr = 'yyyy-MM-dd HH:mm:ss') => {
    const dateObj = typeof date === 'string' ? parseISO(date) : date
    return format(dateObj, formatStr, { locale: zhCN })
  },

  /**
   * 格式化相对时间（如：2分钟前）
   */
  formatRelativeTime: (date: string | Date) => {
    const dateObj = typeof date === 'string' ? parseISO(date) : date
    return formatDistanceToNow(dateObj, { 
      addSuffix: true, 
      locale: zhCN 
    })
  },

  /**
   * 格式化持续时间
   */
  formatDuration: (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) {
      return `${hours}小时${minutes}分钟${secs}秒`
    } else if (minutes > 0) {
      return `${minutes}分钟${secs}秒`
    } else {
      return `${secs}秒`
    }
  },
}

/**
 * 📊 文件大小格式化工具
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 字节'

  const k = 1024
  const sizes = ['字节', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

/**
 * 🔢 数字格式化工具
 */
export const numberUtils = {
  /**
   * 格式化数字（添加千分位分隔符）
   */
  formatNumber: (num: number) => {
    return new Intl.NumberFormat('zh-CN').format(num)
  },

  /**
   * 格式化百分比
   */
  formatPercentage: (num: number, decimals = 1) => {
    return `${(num * 100).toFixed(decimals)}%`
  },

  /**
   * 格式化货币
   */
  formatCurrency: (num: number, currency = 'CNY') => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency,
    }).format(num)
  },
}

/**
 * 🎨 颜色工具
 */
export const colorUtils = {
  /**
   * 根据状态获取颜色
   */
  getStatusColor: (status: string) => {
    const colors = {
      success: 'text-green-600 bg-green-500/20',
      error: 'text-red-600 bg-red-500/20',
      warning: 'text-yellow-600 bg-yellow-500/20',
      info: 'text-blue-600 bg-blue-500/20',
      pending: 'text-gray-600 bg-gray-500/20',
      running: 'text-blue-600 bg-blue-500/20',
      failed: 'text-red-600 bg-red-500/20',
      cancelled: 'text-gray-600 bg-gray-500/20',
    }
    return colors[status as keyof typeof colors] || colors.info
  },

  /**
   * 生成随机颜色
   */
  generateRandomColor: () => {
    const colors = [
      'bg-red-500/20 text-red-600',
      'bg-blue-500/20 text-blue-600',
      'bg-green-500/20 text-green-600',
      'bg-yellow-500/20 text-yellow-600',
      'bg-purple-500/20 text-purple-600',
      'bg-pink-500/20 text-pink-600',
      'bg-indigo-500/20 text-indigo-600',
      'bg-cyan-500/20 text-cyan-600',
    ]
    return colors[Math.floor(Math.random() * colors.length)]
  },
}

/**
 * 🔍 搜索和筛选工具
 */
export const searchUtils = {
  /**
   * 高亮搜索关键词
   */
  highlightText: (text: string, query: string) => {
    if (!query) return text
    
    const regex = new RegExp(`(${query})`, 'gi')
    return text.replace(regex, '<mark class="bg-yellow-200 text-yellow-800">$1</mark>')
  },

  /**
   * 模糊搜索
   */
  fuzzySearch: <T>(items: T[], query: string, keys: (keyof T)[]) => {
    if (!query) return items

    const lowerQuery = query.toLowerCase()
    return items.filter(item =>
      keys.some(key => {
        const value = String(item[key]).toLowerCase()
        return value.includes(lowerQuery)
      })
    )
  },
}

/**
 * 🔧 验证工具
 */
export const validationUtils = {
  /**
   * 验证邮箱
   */
  isValidEmail: (email: string) => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return regex.test(email)
  },

  /**
   * 验证密码强度
   */
  validatePassword: (password: string) => {
    const minLength = password.length >= 8
    const hasUpper = /[A-Z]/.test(password)
    const hasLower = /[a-z]/.test(password)
    const hasNumber = /\d/.test(password)
    const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password)

    return {
      isValid: minLength && hasUpper && hasLower && hasNumber,
      strength: [minLength, hasUpper, hasLower, hasNumber, hasSpecial].filter(Boolean).length,
      requirements: {
        minLength,
        hasUpper,
        hasLower,
        hasNumber,
        hasSpecial,
      },
    }
  },

  /**
   * 验证URL
   */
  isValidUrl: (url: string) => {
    try {
      new URL(url)
      return true
    } catch {
      return false
    }
  },
}

/**
 * 💾 本地存储工具
 */
export const storageUtils = {
  /**
   * 设置本地存储
   */
  setItem: <T>(key: string, value: T) => {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.error('设置本地存储失败:', error)
    }
  },

  /**
   * 获取本地存储
   */
  getItem: <T>(key: string, defaultValue?: T): T | null => {
    try {
      const item = localStorage.getItem(key)
      if (!item) return defaultValue || null
      
      // 🔧 尝试解析JSON，如果失败则返回原始字符串
      try {
        return JSON.parse(item)
      } catch {
        // 如果不是有效的JSON（如JWT token），返回原始字符串
        return item as T
      }
    } catch (error) {
      console.error('获取本地存储失败:', error)
      return defaultValue || null
    }
  },

  /**
   * 移除本地存储
   */
  removeItem: (key: string) => {
    try {
      localStorage.removeItem(key)
    } catch (error) {
      console.error('移除本地存储失败:', error)
    }
  },

  /**
   * 清空本地存储
   */
  clear: () => {
    try {
      localStorage.clear()
    } catch (error) {
      console.error('清空本地存储失败:', error)
    }
  },
}

/**
 * 🎯 防抖和节流工具
 */
export const performanceUtils = {
  /**
   * 防抖函数
   */
  debounce: <T extends (...args: any[]) => any>(
    func: T,
    wait: number
  ): ((...args: Parameters<T>) => void) => {
    let timeout: NodeJS.Timeout
    return (...args: Parameters<T>) => {
      clearTimeout(timeout)
      timeout = setTimeout(() => func(...args), wait)
    }
  },

  /**
   * 节流函数
   */
  throttle: <T extends (...args: any[]) => any>(
    func: T,
    limit: number
  ): ((...args: Parameters<T>) => void) => {
    let inThrottle: boolean
    return (...args: Parameters<T>) => {
      if (!inThrottle) {
        func(...args)
        inThrottle = true
        setTimeout(() => (inThrottle = false), limit)
      }
    }
  },
}

/**
 * 🎲 随机工具
 */
export const randomUtils = {
  /**
   * 生成随机ID
   */
  generateId: (length = 8) => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    let result = ''
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    return result
  },

  /**
   * 生成随机数
   */
  randomBetween: (min: number, max: number) => {
    return Math.floor(Math.random() * (max - min + 1)) + min
  },

  /**
   * 随机选择数组元素
   */
  randomChoice: <T>(array: T[]): T => {
    return array[Math.floor(Math.random() * array.length)]
  },
}

/**
 * 🔄 异步工具
 */
export const asyncUtils = {
  /**
   * 延迟执行
   */
  delay: (ms: number) => new Promise(resolve => setTimeout(resolve, ms)),

  /**
   * 重试机制
   */
  retry: async <T>(
    fn: () => Promise<T>,
    maxAttempts = 3,
    delayMs = 1000
  ): Promise<T> => {
    let lastError: Error
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        return await fn()
      } catch (error) {
        lastError = error as Error
        if (attempt < maxAttempts) {
          await asyncUtils.delay(delayMs * attempt)
        }
      }
    }
    
    throw lastError!
  },
}

/**
 * 🎨 DOM工具
 */
export const domUtils = {
  /**
   * 复制文本到剪贴板
   */
  copyToClipboard: async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch (error) {
      console.error('复制失败:', error)
      return false
    }
  },

  /**
   * 滚动到元素
   */
  scrollToElement: (element: HTMLElement, behavior: ScrollBehavior = 'smooth') => {
    element.scrollIntoView({ behavior, block: 'center' })
  },

  /**
   * 获取元素尺寸
   */
  getElementSize: (element: HTMLElement) => {
    const rect = element.getBoundingClientRect()
    return {
      width: rect.width,
      height: rect.height,
      top: rect.top,
      left: rect.left,
    }
  },
}

// 🛠️ 导出新的中文工具函数
export * from './chinese-formatters'
export * from './chinese-validators'