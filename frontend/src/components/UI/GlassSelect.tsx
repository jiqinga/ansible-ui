import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/utils'

interface SelectOption {
  value: string | number
  label: string
  disabled?: boolean
  icon?: React.ReactNode
}

interface GlassSelectProps {
  options: SelectOption[]
  value?: string | number
  defaultValue?: string | number
  placeholder?: string
  label?: string
  error?: string
  helperText?: string
  size?: 'sm' | 'md' | 'lg'
  fullWidth?: boolean
  disabled?: boolean
  loading?: boolean
  searchable?: boolean
  multiple?: boolean
  clearable?: boolean
  className?: string
  containerClassName?: string
  onChange?: (value: string | number | (string | number)[]) => void
  onSearch?: (query: string) => void
}

/**
 * 🎨 玻璃态选择器组件
 * 
 * 功能：
 * - 单选和多选支持
 * - 搜索功能
 * - 图标支持
 * - 加载状态
 * - 动画效果
 */
const GlassSelect: React.FC<GlassSelectProps> = ({
  options,
  value,
  defaultValue,
  placeholder = '请选择...',
  label,
  error,
  helperText,
  size = 'md',
  fullWidth = true,
  disabled = false,
  loading = false,
  searchable = false,
  multiple = false,
  clearable = false,
  className,
  containerClassName,
  onChange,
  onSearch,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedValues, setSelectedValues] = useState<(string | number)[]>(() => {
    if (multiple) {
      return Array.isArray(value) ? value : []
    }
    return value !== undefined ? [value] : defaultValue !== undefined ? [defaultValue] : []
  })

  const selectRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)

  // 🎨 尺寸样式映射
  const sizeStyles = {
    sm: 'px-3 py-2 text-sm rounded-glass-sm',
    md: 'px-4 py-3 text-base rounded-glass-sm',
    lg: 'px-5 py-4 text-lg rounded-glass',
  }

  // 🎨 选择器样式类
  const selectClasses = cn(
    // 基础玻璃态样式
    'bg-white/15 backdrop-blur-glass border border-white/20',
    'transition-all duration-glass ease-glass cursor-pointer',
    'focus:outline-none focus:ring-2 focus:ring-glass-text-accent/50 focus:border-glass-text-accent/60',
    
    // 尺寸
    sizeStyles[size],
    
    // 全宽
    fullWidth && 'w-full',
    
    // 禁用状态
    disabled && 'opacity-50 cursor-not-allowed',
    
    // 错误状态
    error && 'border-red-500/50 focus:border-red-500/60 focus:ring-red-500/30',
    
    // 响应式优化
    'glass-mobile:px-3 glass-mobile:py-2 glass-mobile:text-sm',
    
    // 自定义类名
    className
  )

  // 🎨 下拉菜单样式类
  const dropdownClasses = cn(
    'absolute top-full left-0 right-0 mt-1 z-50',
    'bg-white/30 backdrop-blur-glass-strong border border-white/20',
    'rounded-glass-sm shadow-glass-strong',
    'max-h-60 overflow-y-auto'
  )

  // 🔍 过滤选项
  const filteredOptions = options.filter(option =>
    option.label.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // 🎯 获取显示文本
  const getDisplayText = () => {
    if (selectedValues.length === 0) {
      return placeholder
    }

    if (multiple) {
      if (selectedValues.length === 1) {
        const option = options.find(opt => opt.value === selectedValues[0])
        return option?.label || ''
      }
      return `已选择 ${selectedValues.length} 项`
    }

    const option = options.find(opt => opt.value === selectedValues[0])
    return option?.label || ''
  }

  // 🎯 处理选项点击
  const handleOptionClick = (optionValue: string | number) => {
    let newValues: (string | number)[]

    if (multiple) {
      if (selectedValues.includes(optionValue)) {
        newValues = selectedValues.filter(v => v !== optionValue)
      } else {
        newValues = [...selectedValues, optionValue]
      }
    } else {
      newValues = [optionValue]
      setIsOpen(false)
    }

    setSelectedValues(newValues)
    
    if (onChange) {
      onChange(multiple ? newValues : newValues[0])
    }
  }

  // 🧹 清空选择
  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    setSelectedValues([])
    if (onChange) {
      onChange(multiple ? [] : '')
    }
  }

  // 🔍 处理搜索
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value
    setSearchQuery(query)
    if (onSearch) {
      onSearch(query)
    }
  }

  // 🎯 点击外部关闭
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setSearchQuery('')
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // 🎯 搜索框自动聚焦
  useEffect(() => {
    if (isOpen && searchable && searchInputRef.current) {
      searchInputRef.current.focus()
    }
  }, [isOpen, searchable])

  // 🎨 箭头图标
  const ChevronIcon = ({ isOpen }: { isOpen: boolean }) => (
    <motion.svg
      className="w-5 h-5 text-glass-text-secondary"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      animate={{ rotate: isOpen ? 180 : 0 }}
      transition={{ duration: 0.2 }}
    >
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </motion.svg>
  )

  // 🎨 清空图标
  const ClearIcon = () => (
    <svg
      className="w-4 h-4 text-glass-text-secondary hover:text-glass-text-primary"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  )

  // 🎨 加载动画
  const LoadingSpinner = () => (
    <motion.div
      className="w-4 h-4 border-2 border-glass-text-secondary border-t-transparent rounded-full"
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
    />
  )

  return (
    <div className={cn('relative', fullWidth && 'w-full', containerClassName)}>
      {/* 🏷️ 标签 */}
      {label && (
        <label className={cn(
          'block text-sm font-medium mb-2',
          error ? 'text-red-600' : 'text-glass-text-primary'
        )}>
          {label}
        </label>
      )}

      {/* 📝 选择器 */}
      <div ref={selectRef} className="relative">
        <div
          className={selectClasses}
          onClick={() => !disabled && setIsOpen(!isOpen)}
        >
          <div className="flex items-center justify-between">
            <span className={cn(
              'flex-1 truncate',
              selectedValues.length === 0 && 'text-glass-text-secondary/60'
            )}>
              {getDisplayText()}
            </span>
            
            <div className="flex items-center gap-2 ml-2">
              {/* 🧹 清空按钮 */}
              {clearable && selectedValues.length > 0 && !loading && (
                <motion.button
                  className="p-1 hover:bg-white/10 rounded-full transition-colors"
                  onClick={handleClear}
                  aria-label="清空选择"
                  whileHover={{ opacity: 0.8 }}
                  whileTap={{ opacity: 0.6 }}
                >
                  <ClearIcon />
                </motion.button>
              )}
              
              {/* 🔄 加载状态 */}
              {loading ? <LoadingSpinner /> : <ChevronIcon isOpen={isOpen} />}
            </div>
          </div>
        </div>

        {/* 📋 下拉菜单 */}
        <AnimatePresence>
          {isOpen && (
            <motion.div
              className={dropdownClasses}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
            >
              {/* 🔍 搜索框 */}
              {searchable && (
                <div className="p-2 border-b border-white/10">
                  <input
                    ref={searchInputRef}
                    type="text"
                    placeholder="搜索选项..."
                    value={searchQuery}
                    onChange={handleSearch}
                    className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-glass-sm
                             text-glass-text-primary placeholder:text-glass-text-secondary/60
                             focus:outline-none focus:ring-1 focus:ring-glass-text-accent/50"
                  />
                </div>
              )}

              {/* 📋 选项列表 */}
              <div className="py-1">
                {filteredOptions.length === 0 ? (
                  <div className="px-4 py-3 text-glass-text-secondary text-center">
                    {searchQuery ? '未找到匹配选项' : '暂无选项'}
                  </div>
                ) : (
                  filteredOptions.map((option) => (
                    <motion.div
                      key={option.value}
                      className={cn(
                        'flex items-center px-4 py-3 cursor-pointer transition-colors',
                        'hover:bg-white/10',
                        selectedValues.includes(option.value) && 'bg-white/15',
                        option.disabled && 'opacity-50 cursor-not-allowed'
                      )}
                      onClick={() => !option.disabled && handleOptionClick(option.value)}
                      whileHover={!option.disabled ? { x: 2 } : {}}
                    >
                      {/* 🎨 图标 */}
                      {option.icon && (
                        <span className="mr-3 flex-shrink-0">
                          {option.icon}
                        </span>
                      )}
                      
                      {/* 📝 标签 */}
                      <span className="flex-1 text-glass-text-primary">
                        {option.label}
                      </span>
                      
                      {/* ✅ 选中标记 */}
                      {selectedValues.includes(option.value) && (
                        <motion.svg
                          className="w-5 h-5 text-glass-text-accent ml-2"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ duration: 0.2 }}
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </motion.svg>
                      )}
                    </motion.div>
                  ))
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ⚠️ 错误提示 */}
      {error && (
        <motion.div
          className="mt-1 text-sm text-red-600"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          transition={{ duration: 0.2 }}
        >
          {error}
        </motion.div>
      )}

      {/* 💡 帮助文本 */}
      {helperText && !error && (
        <div className="mt-1 text-sm text-glass-text-secondary">
          {helperText}
        </div>
      )}
    </div>
  )
}

export default GlassSelect
