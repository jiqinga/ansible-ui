/**
 * 🇨🇳 中文格式化Hook
 * 
 * 提供React组件中使用的中文格式化功能
 */

import { useCallback, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import {
  formatChineseDate,
  formatChineseTime,
  formatChineseRelativeTime,
  formatChineseCurrency,
  formatChineseFileSize,
  formatChineseDuration,
  getChineseStatusText,
  getChinesePriorityText,
  getChineseRoleText,
  toChineseNumber
} from '../utils/chinese-formatters'

/**
 * 🇨🇳 中文格式化Hook
 */
export const useChineseFormat = () => {
  const { t, i18n } = useTranslation()
  
  // 🌐 检查当前是否为中文环境
  const isChinese = useMemo(() => {
    return i18n.language.startsWith('zh')
  }, [i18n.language])

  // 📅 日期格式化
  const formatDate = useCallback((
    date: Date | string | number,
    options?: {
      includeWeekday?: boolean
      includeTime?: boolean
      use24Hour?: boolean
      relative?: boolean
    }
  ) => {
    const {
      includeWeekday = false,
      includeTime = false,
      use24Hour = true,
      relative = false
    } = options || {}

    if (relative) {
      return formatChineseRelativeTime(date)
    }

    let result = formatChineseDate(date, includeWeekday)
    
    if (includeTime) {
      const timeStr = formatChineseTime(date, use24Hour)
      result += ` ${timeStr}`
    }

    return result
  }, [])

  // 💰 货币格式化
  const formatCurrency = useCallback((
    amount: number,
    currency: 'CNY' | 'USD' | 'EUR' = 'CNY'
  ) => {
    if (isChinese) {
      return formatChineseCurrency(amount, currency)
    }
    
    // 非中文环境使用标准格式
    return new Intl.NumberFormat(i18n.language, {
      style: 'currency',
      currency,
    }).format(amount)
  }, [isChinese, i18n.language])

  // 📊 文件大小格式化
  const formatFileSize = useCallback((bytes: number, decimals: number = 2) => {
    return formatChineseFileSize(bytes, decimals)
  }, [])

  // ⏱️ 持续时间格式化
  const formatDuration = useCallback((
    seconds: number,
    detailed: boolean = false
  ) => {
    return formatChineseDuration(seconds, detailed)
  }, [])

  // 🔢 数字格式化
  const formatNumber = useCallback((
    num: number,
    options?: {
      useGrouping?: boolean
      minimumFractionDigits?: number
      maximumFractionDigits?: number
      chinese?: boolean
    }
  ) => {
    const {
      useGrouping = true,
      minimumFractionDigits,
      maximumFractionDigits,
      chinese = false
    } = options || {}

    if (chinese && isChinese && Number.isInteger(num) && num >= 0 && num <= 99) {
      return toChineseNumber(num)
    }

    return new Intl.NumberFormat(i18n.language, {
      useGrouping,
      minimumFractionDigits,
      maximumFractionDigits,
    }).format(num)
  }, [isChinese, i18n.language])

  // 📊 百分比格式化
  const formatPercentage = useCallback((
    value: number,
    decimals: number = 1
  ) => {
    return new Intl.NumberFormat(i18n.language, {
      style: 'percent',
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value)
  }, [i18n.language])

  // 🏷️ 状态文本格式化
  const formatStatus = useCallback((status: string) => {
    if (isChinese) {
      return getChineseStatusText(status)
    }
    
    // 非中文环境使用翻译
    return t(`status.${status}`, status)
  }, [isChinese, t])

  // 🎯 优先级文本格式化
  const formatPriority = useCallback((priority: string | number) => {
    if (isChinese) {
      return getChinesePriorityText(priority)
    }
    
    // 非中文环境使用翻译
    return t(`priority.${priority}`, priority.toString())
  }, [isChinese, t])

  // 👥 角色文本格式化
  const formatRole = useCallback((role: string) => {
    if (isChinese) {
      return getChineseRoleText(role)
    }
    
    // 非中文环境使用翻译
    return t(`role.${role}`, role)
  }, [isChinese, t])

  // 📏 单位格式化
  const formatWithUnit = useCallback((
    value: number,
    unit: string,
    options?: {
      decimals?: number
      space?: boolean
    }
  ) => {
    const { decimals = 2, space = true } = options || {}
    const formattedValue = decimals > 0 ? value.toFixed(decimals) : value.toString()
    const separator = space ? ' ' : ''
    
    return `${formattedValue}${separator}${unit}`
  }, [])

  // 🔗 列表格式化（用逗号连接）
  const formatList = useCallback((
    items: string[],
    options?: {
      maxItems?: number
      moreText?: string
    }
  ) => {
    const { maxItems = 3, moreText = '等' } = options || {}
    
    if (items.length === 0) {
      return isChinese ? '无' : 'None'
    }
    
    if (items.length <= maxItems) {
      return items.join(isChinese ? '、' : ', ')
    }
    
    const displayItems = items.slice(0, maxItems)
    const remainingCount = items.length - maxItems
    
    if (isChinese) {
      return `${displayItems.join('、')}${moreText}${remainingCount}个`
    } else {
      return `${displayItems.join(', ')} and ${remainingCount} more`
    }
  }, [isChinese])

  // 📊 进度格式化
  const formatProgress = useCallback((
    current: number,
    total: number,
    options?: {
      showPercentage?: boolean
      showFraction?: boolean
    }
  ) => {
    const { showPercentage = true, showFraction = true } = options || {}
    
    const percentage = total > 0 ? (current / total) * 100 : 0
    const parts: string[] = []
    
    if (showFraction) {
      parts.push(`${current}/${total}`)
    }
    
    if (showPercentage) {
      parts.push(`${percentage.toFixed(1)}%`)
    }
    
    return parts.join(' ')
  }, [])

  return {
    // 基础格式化
    formatDate,
    formatCurrency,
    formatFileSize,
    formatDuration,
    formatNumber,
    formatPercentage,
    
    // 业务格式化
    formatStatus,
    formatPriority,
    formatRole,
    formatWithUnit,
    formatList,
    formatProgress,
    
    // 工具属性
    isChinese,
    language: i18n.language,
  }
}

export default useChineseFormat