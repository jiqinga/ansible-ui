/**
 * 🇨🇳 中文日期选择器组件
 * 
 * 支持中文日期格式显示和选择的日期选择器
 */

import React, { useState, useCallback, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CalendarIcon, ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline'
import { cn } from '../../utils'
import { formatChineseDate } from '../../utils/chinese-formatters'
import { CHINESE_DATE } from '../../constants/chinese-constants'

interface ChineseDatePickerProps {
  /** 选中的日期 */
  value?: Date
  /** 日期变化回调 */
  onChange?: (date: Date | null) => void
  /** 占位符文本 */
  placeholder?: string
  /** 标签文本 */
  label?: string
  /** 错误信息 */
  error?: string
  /** 是否必填 */
  required?: boolean
  /** 是否禁用 */
  disabled?: boolean
  /** 最小日期 */
  minDate?: Date
  /** 最大日期 */
  maxDate?: Date
  /** 自定义样式类名 */
  className?: string
  /** 日期格式 */
  format?: 'full' | 'short' | 'numeric'
  /** 是否显示今天按钮 */
  showToday?: boolean
  /** 是否显示清除按钮 */
  showClear?: boolean
}

const ChineseDatePicker: React.FC<ChineseDatePickerProps> = ({
  value,
  onChange,
  placeholder = '请选择日期',
  label,
  error,
  required = false,
  disabled = false,
  minDate,
  maxDate,
  className,
  format = 'full',
  showToday = true,
  showClear = true,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [currentMonth, setCurrentMonth] = useState(value || new Date())
  const containerRef = useRef<HTMLDivElement>(null)

  // 🗓️ 生成日历数据
  const generateCalendar = useCallback((date: Date) => {
    const year = date.getFullYear()
    const month = date.getMonth()
    
    // 获取当月第一天和最后一天
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    
    // 获取当月第一天是星期几（0=周日，1=周一...）
    const firstDayOfWeek = firstDay.getDay()
    
    // 生成日历数组
    const calendar: (Date | null)[] = []
    
    // 添加上个月的日期（填充）
    for (let i = 0; i < firstDayOfWeek; i++) {
      const prevDate = new Date(year, month, -firstDayOfWeek + i + 1)
      calendar.push(prevDate)
    }
    
    // 添加当月的日期
    for (let day = 1; day <= lastDay.getDate(); day++) {
      calendar.push(new Date(year, month, day))
    }
    
    // 添加下个月的日期（填充到42个格子）
    const remainingCells = 42 - calendar.length
    for (let day = 1; day <= remainingCells; day++) {
      calendar.push(new Date(year, month + 1, day))
    }
    
    return calendar
  }, [])

  // 📅 格式化显示日期
  const formatDisplayDate = useCallback((date: Date) => {
    switch (format) {
      case 'short':
        return formatChineseDate(date, false)
      case 'numeric':
        return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`
      default:
        return formatChineseDate(date, true)
    }
  }, [format])

  // 🎯 处理日期选择
  const handleDateSelect = useCallback((date: Date) => {
    // 检查日期是否在允许范围内
    if (minDate && date < minDate) return
    if (maxDate && date > maxDate) return
    
    onChange?.(date)
    setIsOpen(false)
  }, [onChange, minDate, maxDate])

  // 🗓️ 处理月份切换
  const handleMonthChange = useCallback((direction: 'prev' | 'next') => {
    setCurrentMonth(prev => {
      const newDate = new Date(prev)
      if (direction === 'prev') {
        newDate.setMonth(prev.getMonth() - 1)
      } else {
        newDate.setMonth(prev.getMonth() + 1)
      }
      return newDate
    })
  }, [])

  // 📅 处理今天按钮
  const handleToday = useCallback(() => {
    const today = new Date()
    handleDateSelect(today)
    setCurrentMonth(today)
  }, [handleDateSelect])

  // 🗑️ 处理清除按钮
  const handleClear = useCallback(() => {
    onChange?.(null)
    setIsOpen(false)
  }, [onChange])

  // 🖱️ 处理点击外部关闭
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  // 🎨 样式类名
  const inputClasses = cn(
    'w-full px-4 py-3 rounded-xl border transition-all duration-200',
    'bg-white/10 backdrop-blur-md text-glass-text-primary placeholder-glass-text-secondary',
    'focus:outline-none focus:ring-2 focus:ring-white/20 cursor-pointer',
    {
      'border-white/20 hover:border-white/30': !error,
      'border-red-400 bg-red-50/10': error,
      'opacity-50 cursor-not-allowed': disabled,
    },
    className
  )

  const labelClasses = cn(
    'block text-sm font-medium text-glass-text-primary mb-2',
    required && "after:content-['*'] after:text-red-400 after:ml-1"
  )

  // 🗓️ 生成当前月份的日历
  const calendarDays = generateCalendar(currentMonth)
  const currentYear = currentMonth.getFullYear()
  const currentMonthIndex = currentMonth.getMonth()

  return (
    <div ref={containerRef} className="relative space-y-2">
      {/* 📝 标签 */}
      {label && (
        <label className={labelClasses}>
          {label}
        </label>
      )}

      {/* 📦 输入框 */}
      <div
        className={inputClasses}
        onClick={() => !disabled && setIsOpen(!isOpen)}
      >
        <div className="flex items-center justify-between">
          <span className={value ? 'text-glass-text-primary' : 'text-glass-text-secondary'}>
            {value ? formatDisplayDate(value) : placeholder}
          </span>
          <CalendarIcon className="w-5 h-5 text-glass-text-secondary" />
        </div>
      </div>

      {/* 📅 日期选择器弹窗 */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full left-0 z-50 mt-2 w-80 glass-container p-4 shadow-lg"
          >
            {/* 🗓️ 月份导航 */}
            <div className="flex items-center justify-between mb-4">
              <button
                onClick={() => handleMonthChange('prev')}
                className="p-2 rounded-lg hover:bg-white/10 transition-colors"
              >
                <ChevronLeftIcon className="w-5 h-5 text-glass-text-primary" />
              </button>
              
              <h3 className="text-lg font-semibold text-glass-text-primary">
                {currentYear}年{CHINESE_DATE.MONTHS_SHORT[currentMonthIndex]}
              </h3>
              
              <button
                onClick={() => handleMonthChange('next')}
                className="p-2 rounded-lg hover:bg-white/10 transition-colors"
              >
                <ChevronRightIcon className="w-5 h-5 text-glass-text-primary" />
              </button>
            </div>

            {/* 📅 星期标题 */}
            <div className="grid grid-cols-7 gap-1 mb-2">
              {CHINESE_DATE.WEEKDAYS_SHORT.map((day) => (
                <div
                  key={day}
                  className="h-8 flex items-center justify-center text-sm font-medium text-glass-text-secondary"
                >
                  {day}
                </div>
              ))}
            </div>

            {/* 📅 日期网格 */}
            <div className="grid grid-cols-7 gap-1 mb-4">
              {calendarDays.map((date, index) => {
                if (!date) return <div key={index} />
                
                const isCurrentMonth = date.getMonth() === currentMonthIndex
                const isSelected = value && date.toDateString() === value.toDateString()
                const isToday = date.toDateString() === new Date().toDateString()
                const isDisabled = 
                  (minDate && date < minDate) || 
                  (maxDate && date > maxDate)

                return (
                  <motion.button
                    key={date.toISOString()}
                    onClick={() => !isDisabled && handleDateSelect(date)}
                    whileHover={!isDisabled ? { y: -1 } : {}}
                    whileTap={!isDisabled ? { y: 0 } : {}}
                    className={cn(
                      'h-8 w-8 rounded-lg text-sm font-medium transition-all duration-150',
                      {
                        'text-glass-text-primary hover:bg-white/10': isCurrentMonth && !isSelected && !isDisabled,
                        'text-glass-text-secondary': !isCurrentMonth,
                        'bg-blue-500 text-white': isSelected,
                        'bg-blue-500/20 text-blue-600': isToday && !isSelected,
                        'opacity-50 cursor-not-allowed': isDisabled,
                      }
                    )}
                    disabled={isDisabled}
                  >
                    {date.getDate()}
                  </motion.button>
                )
              })}
            </div>

            {/* 🔘 操作按钮 */}
            <div className="flex items-center justify-between pt-2 border-t border-white/10">
              <div className="flex space-x-2">
                {showToday && (
                  <button
                    onClick={handleToday}
                    className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-500/10 rounded-lg transition-colors"
                  >
                    今天
                  </button>
                )}
                {showClear && value && (
                  <button
                    onClick={handleClear}
                    className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-500/10 rounded-lg transition-colors"
                  >
                    清除
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 💬 错误信息 */}
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-sm text-red-400"
        >
          {error}
        </motion.p>
      )}
    </div>
  )
}

export default ChineseDatePicker