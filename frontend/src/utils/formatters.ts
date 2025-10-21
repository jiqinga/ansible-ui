/**
 * 🌐 格式化工具函数
 * 
 * 提供中文本地化的时间、数字、文件大小等格式化功能
 */

import { format, formatDistanceToNow, parseISO, isValid } from 'date-fns'
import { zhCN, enUS } from 'date-fns/locale'
import i18n from '../i18n'

/**
 * 🕒 获取当前语言的date-fns locale
 */
const getDateLocale = () => {
  const currentLang = i18n.language
  return currentLang.startsWith('zh') ? zhCN : enUS
}

/**
 * 🕒 格式化日期时间
 * @param date 日期对象、ISO字符串或时间戳
 * @param formatStr 格式字符串，默认为 'yyyy-MM-dd HH:mm:ss'
 * @returns 格式化后的日期字符串
 */
export const formatDateTime = (
  date: Date | string | number,
  formatStr: string = 'yyyy-MM-dd HH:mm:ss'
): string => {
  try {
    let dateObj: Date

    if (typeof date === 'string') {
      dateObj = parseISO(date)
    } else if (typeof date === 'number') {
      dateObj = new Date(date)
    } else {
      dateObj = date
    }

    if (!isValid(dateObj)) {
      return '无效日期'
    }

    return format(dateObj, formatStr, { locale: getDateLocale() })
  } catch (error) {
    console.error('日期格式化错误:', error)
    return '格式化失败'
  }
}

/**
 * 🕒 格式化相对时间（如：3分钟前）
 * @param date 日期对象、ISO字符串或时间戳
 * @returns 相对时间字符串
 */
export const formatRelativeTime = (date: Date | string | number): string => {
  try {
    let dateObj: Date

    if (typeof date === 'string') {
      dateObj = parseISO(date)
    } else if (typeof date === 'number') {
      dateObj = new Date(date)
    } else {
      dateObj = date
    }

    if (!isValid(dateObj)) {
      return '无效日期'
    }

    return formatDistanceToNow(dateObj, { 
      addSuffix: true, 
      locale: getDateLocale() 
    })
  } catch (error) {
    console.error('相对时间格式化错误:', error)
    return '格式化失败'
  }
}

/**
 * 📊 格式化文件大小
 * @param bytes 字节数
 * @param decimals 小数位数，默认为2
 * @returns 格式化后的文件大小字符串
 */
export const formatFileSize = (bytes: number, decimals: number = 2): string => {
  if (bytes === 0) return '0 字节'

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['字节', 'KB', 'MB', 'GB', 'TB', 'PB']

  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

/**
 * 📊 格式化百分比
 * @param value 数值（0-1之间）
 * @param decimals 小数位数，默认为1
 * @returns 格式化后的百分比字符串
 */
export const formatPercentage = (value: number, decimals: number = 1): string => {
  return (value * 100).toFixed(decimals) + '%'
}

/**
 * 🔢 格式化数字（添加千分位分隔符）
 * @param num 数字
 * @param decimals 小数位数
 * @returns 格式化后的数字字符串
 */
export const formatNumber = (num: number, decimals?: number): string => {
  const options: Intl.NumberFormatOptions = {
    style: 'decimal',
    useGrouping: true,
  }

  if (decimals !== undefined) {
    options.minimumFractionDigits = decimals
    options.maximumFractionDigits = decimals
  }

  // 根据当前语言选择格式
  const locale = i18n.language.startsWith('zh') ? 'zh-CN' : 'en-US'
  
  return new Intl.NumberFormat(locale, options).format(num)
}

/**
 * ⏱️ 格式化持续时间
 * @param seconds 秒数
 * @returns 格式化后的持续时间字符串
 */
export const formatDuration = (seconds: number): string => {
  if (seconds < 60) {
    return `${Math.round(seconds)} 秒`
  }

  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.round(seconds % 60)

  if (minutes < 60) {
    return remainingSeconds > 0 
      ? `${minutes} 分钟 ${remainingSeconds} 秒`
      : `${minutes} 分钟`
  }

  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60

  if (hours < 24) {
    return remainingMinutes > 0
      ? `${hours} 小时 ${remainingMinutes} 分钟`
      : `${hours} 小时`
  }

  const days = Math.floor(hours / 24)
  const remainingHours = hours % 24

  return remainingHours > 0
    ? `${days} 天 ${remainingHours} 小时`
    : `${days} 天`
}

/**
 * 📈 格式化状态文本
 * @param status 状态值
 * @returns 中文状态描述
 */
export const formatStatus = (status: string): string => {
  const statusMap: Record<string, string> = {
    // 任务执行状态
    'pending': '等待中',
    'running': '运行中',
    'success': '成功',
    'failed': '失败',
    'cancelled': '已取消',
    'timeout': '超时',
    
    // 连接状态
    'online': '在线',
    'offline': '离线',
    'unknown': '未知',
    
    // 系统状态
    'healthy': '健康',
    'warning': '警告',
    'critical': '严重',
    'error': '错误',
    
    // 通用状态
    'active': '活跃',
    'inactive': '非活跃',
    'enabled': '已启用',
    'disabled': '已禁用',
  }

  return statusMap[status.toLowerCase()] || status
}

/**
 * 🎨 获取状态对应的颜色类名
 * @param status 状态值
 * @returns Tailwind CSS颜色类名
 */
export const getStatusColor = (status: string): string => {
  const colorMap: Record<string, string> = {
    'success': 'text-green-600',
    'failed': 'text-red-600',
    'running': 'text-blue-600',
    'pending': 'text-yellow-600',
    'cancelled': 'text-gray-600',
    'timeout': 'text-orange-600',
    'online': 'text-green-600',
    'offline': 'text-red-600',
    'unknown': 'text-gray-600',
    'healthy': 'text-green-600',
    'warning': 'text-yellow-600',
    'critical': 'text-red-600',
    'error': 'text-red-600',
  }

  return colorMap[status.toLowerCase()] || 'text-gray-600'
}

/**
 * 🌐 格式化IP地址显示
 * @param ip IP地址
 * @returns 格式化后的IP地址
 */
export const formatIPAddress = (ip: string): string => {
  // 简单的IP地址验证和格式化
  const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/
  const ipv6Regex = /^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/

  if (ipv4Regex.test(ip) || ipv6Regex.test(ip)) {
    return ip
  }

  return ip || '未知IP'
}

/**
 * 📱 格式化端口号
 * @param port 端口号
 * @returns 格式化后的端口号
 */
export const formatPort = (port: number | string): string => {
  const portNum = typeof port === 'string' ? parseInt(port, 10) : port
  
  if (isNaN(portNum) || portNum < 1 || portNum > 65535) {
    return '无效端口'
  }

  return portNum.toString()
}

/**
 * 🏷️ 格式化标签列表
 * @param tags 标签数组
 * @param maxDisplay 最大显示数量，默认为3
 * @returns 格式化后的标签字符串
 */
export const formatTags = (tags: string[], maxDisplay: number = 3): string => {
  if (!tags || tags.length === 0) {
    return '无标签'
  }

  if (tags.length <= maxDisplay) {
    return tags.join(', ')
  }

  const displayTags = tags.slice(0, maxDisplay)
  const remainingCount = tags.length - maxDisplay

  return `${displayTags.join(', ')} 等 ${remainingCount} 个`
}