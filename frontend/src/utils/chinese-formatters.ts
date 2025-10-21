/**
 * 🇨🇳 中文本地化格式化工具
 * 
 * 提供专门针对中文环境的格式化功能
 */

import { parseISO, isValid } from 'date-fns'
// import { format, formatDistanceToNow } from 'date-fns'
// import { zhCN } from 'date-fns/locale'

/**
 * 🔢 中文数字转换
 * @param num 阿拉伯数字
 * @returns 中文数字字符串
 */
export const toChineseNumber = (num: number): string => {
  const chineseNums = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九']
  const chineseUnits = ['', '十', '百', '千', '万', '十万', '百万', '千万', '亿']
  
  if (num === 0) return '零'
  if (num < 0) return '负' + toChineseNumber(-num)
  
  let result = ''
  let unitIndex = 0
  
  while (num > 0) {
    const digit = num % 10
    if (digit !== 0) {
      result = chineseNums[digit] + chineseUnits[unitIndex] + result
    } else if (result && !result.startsWith('零')) {
      result = '零' + result
    }
    num = Math.floor(num / 10)
    unitIndex++
  }
  
  // 处理特殊情况：十一 -> 十一，而不是一十一
  if (result.startsWith('一十')) {
    result = result.substring(1)
  }
  
  return result
}

/**
 * 📅 中文日期格式化
 * @param date 日期
 * @param includeWeekday 是否包含星期
 * @returns 中文日期字符串
 */
export const formatChineseDate = (
  date: Date | string | number,
  includeWeekday: boolean = true
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

    const year = dateObj.getFullYear()
    const month = dateObj.getMonth() + 1
    const day = dateObj.getDate()
    
    let result = `${year}年${month}月${day}日`
    
    if (includeWeekday) {
      const weekdays = ['日', '一', '二', '三', '四', '五', '六']
      const weekday = weekdays[dateObj.getDay()]
      result += ` 星期${weekday}`
    }
    
    return result
  } catch (error) {
    console.error('中文日期格式化错误:', error)
    return '格式化失败'
  }
}

/**
 * 🕐 中文时间格式化
 * @param date 日期时间
 * @param use24Hour 是否使用24小时制
 * @returns 中文时间字符串
 */
export const formatChineseTime = (
  date: Date | string | number,
  use24Hour: boolean = true
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
      return '无效时间'
    }

    const hours = dateObj.getHours()
    const minutes = dateObj.getMinutes()
    const seconds = dateObj.getSeconds()
    
    if (use24Hour) {
      return `${hours.toString().padStart(2, '0')}时${minutes.toString().padStart(2, '0')}分${seconds.toString().padStart(2, '0')}秒`
    } else {
      const period = hours < 12 ? '上午' : '下午'
      const displayHours = hours % 12 || 12
      return `${period}${displayHours}时${minutes.toString().padStart(2, '0')}分`
    }
  } catch (error) {
    console.error('中文时间格式化错误:', error)
    return '格式化失败'
  }
}

/**
 * 📊 中文相对时间格式化
 * @param date 日期
 * @returns 中文相对时间字符串
 */
export const formatChineseRelativeTime = (date: Date | string | number): string => {
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

    const now = new Date()
    const diffInSeconds = Math.floor((now.getTime() - dateObj.getTime()) / 1000)
    
    if (diffInSeconds < 60) {
      return '刚刚'
    }
    
    const diffInMinutes = Math.floor(diffInSeconds / 60)
    if (diffInMinutes < 60) {
      return `${diffInMinutes}分钟前`
    }
    
    const diffInHours = Math.floor(diffInMinutes / 60)
    if (diffInHours < 24) {
      return `${diffInHours}小时前`
    }
    
    const diffInDays = Math.floor(diffInHours / 24)
    if (diffInDays < 30) {
      return `${diffInDays}天前`
    }
    
    const diffInMonths = Math.floor(diffInDays / 30)
    if (diffInMonths < 12) {
      return `${diffInMonths}个月前`
    }
    
    const diffInYears = Math.floor(diffInMonths / 12)
    return `${diffInYears}年前`
  } catch (error) {
    console.error('中文相对时间格式化错误:', error)
    return '格式化失败'
  }
}

/**
 * 💰 中文货币格式化
 * @param amount 金额
 * @param currency 货币类型
 * @returns 中文货币字符串
 */
export const formatChineseCurrency = (
  amount: number,
  currency: 'CNY' | 'USD' | 'EUR' = 'CNY'
): string => {
  const currencySymbols = {
    CNY: '¥',
    USD: '$',
    EUR: '€'
  }
  
  const currencyNames = {
    CNY: '人民币',
    USD: '美元',
    EUR: '欧元'
  }
  
  const formattedAmount = new Intl.NumberFormat('zh-CN', {
    style: 'decimal',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
  
  return `${currencySymbols[currency]}${formattedAmount} ${currencyNames[currency]}`
}

/**
 * 📏 中文单位格式化
 * @param value 数值
 * @param unit 单位类型
 * @returns 中文单位字符串
 */
export const formatChineseUnit = (
  value: number,
  unit: 'length' | 'weight' | 'area' | 'volume' | 'temperature'
): string => {
  const units = {
    length: {
      mm: '毫米',
      cm: '厘米',
      m: '米',
      km: '千米'
    },
    weight: {
      g: '克',
      kg: '千克',
      t: '吨'
    },
    area: {
      'm²': '平方米',
      'km²': '平方千米',
      'ha': '公顷'
    },
    volume: {
      ml: '毫升',
      l: '升',
      'm³': '立方米'
    },
    temperature: {
      '°C': '摄氏度',
      '°F': '华氏度',
      'K': '开尔文'
    }
  }
  
  // 简单的单位选择逻辑，实际应用中可能需要更复杂的逻辑
  const unitMap = units[unit]
  const unitKey = Object.keys(unitMap)[0] // 默认使用第一个单位
  
  return `${value} ${unitMap[unitKey as keyof typeof unitMap]}`
}

/**
 * 📈 中文百分比格式化
 * @param value 数值（0-1之间）
 * @param decimals 小数位数
 * @returns 中文百分比字符串
 */
export const formatChinesePercentage = (value: number, decimals: number = 1): string => {
  const percentage = (value * 100).toFixed(decimals)
  return `${percentage}%`
}

/**
 * 📊 中文文件大小格式化
 * @param bytes 字节数
 * @param decimals 小数位数
 * @returns 中文文件大小字符串
 */
export const formatChineseFileSize = (bytes: number, decimals: number = 2): string => {
  if (bytes === 0) return '0 字节'

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['字节', 'KB', 'MB', 'GB', 'TB', 'PB']

  const i = Math.floor(Math.log(bytes) / Math.log(k))
  const size = parseFloat((bytes / Math.pow(k, i)).toFixed(dm))

  return `${size} ${sizes[i]}`
}

/**
 * ⏱️ 中文持续时间格式化
 * @param seconds 秒数
 * @param detailed 是否显示详细信息
 * @returns 中文持续时间字符串
 */
export const formatChineseDuration = (seconds: number, detailed: boolean = false): string => {
  if (seconds < 60) {
    return `${Math.round(seconds)} 秒`
  }

  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.round(seconds % 60)

  if (minutes < 60) {
    if (detailed && remainingSeconds > 0) {
      return `${minutes} 分钟 ${remainingSeconds} 秒`
    }
    return `${minutes} 分钟`
  }

  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60

  if (hours < 24) {
    if (detailed && remainingMinutes > 0) {
      return `${hours} 小时 ${remainingMinutes} 分钟`
    }
    return `${hours} 小时`
  }

  const days = Math.floor(hours / 24)
  const remainingHours = hours % 24

  if (detailed && remainingHours > 0) {
    return `${days} 天 ${remainingHours} 小时`
  }
  return `${days} 天`
}

/**
 * 🏷️ 中文状态描述
 * @param status 状态值
 * @returns 中文状态描述
 */
export const getChineseStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    // 任务执行状态
    'pending': '等待执行',
    'running': '正在运行',
    'success': '执行成功',
    'failed': '执行失败',
    'cancelled': '已取消',
    'timeout': '执行超时',
    'paused': '已暂停',
    'resumed': '已恢复',
    
    // 连接状态
    'online': '在线',
    'offline': '离线',
    'connecting': '连接中',
    'disconnected': '已断开',
    'unknown': '状态未知',
    
    // 系统状态
    'healthy': '运行正常',
    'warning': '需要注意',
    'critical': '严重问题',
    'error': '发生错误',
    'maintenance': '维护中',
    
    // 通用状态
    'active': '活跃状态',
    'inactive': '非活跃',
    'enabled': '已启用',
    'disabled': '已禁用',
    'loading': '加载中',
    'completed': '已完成',
    'processing': '处理中',
    'waiting': '等待中',
  }

  return statusMap[status.toLowerCase()] || status
}

/**
 * 🎯 中文优先级描述
 * @param priority 优先级值
 * @returns 中文优先级描述
 */
export const getChinesePriorityText = (priority: string | number): string => {
  const priorityMap: Record<string, string> = {
    'low': '低优先级',
    'normal': '普通优先级',
    'medium': '中等优先级',
    'high': '高优先级',
    'urgent': '紧急',
    'critical': '极其重要',
    '1': '最低',
    '2': '较低',
    '3': '普通',
    '4': '较高',
    '5': '最高',
  }

  return priorityMap[priority.toString().toLowerCase()] || priority.toString()
}

/**
 * 🔐 中文权限级别描述
 * @param role 角色或权限级别
 * @returns 中文权限描述
 */
export const getChineseRoleText = (role: string): string => {
  const roleMap: Record<string, string> = {
    'admin': '系统管理员',
    'operator': '操作员',
    'viewer': '查看者',
    'guest': '访客',
    'user': '普通用户',
    'moderator': '协调员',
    'editor': '编辑者',
    'owner': '所有者',
    'member': '成员',
  }

  return roleMap[role.toLowerCase()] || role
}