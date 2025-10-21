/**
 * 🇨🇳 中文输入框组件
 * 
 * 专门为中文输入优化的输入框组件
 * 支持拼音输入、中文验证等功能
 */

import React, { useState, useCallback, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { ExclamationCircleIcon, CheckCircleIcon } from '@heroicons/react/24/outline'
import { cn } from '../../utils'
import { validateLength, validateRequired } from '../../utils/chinese-validators'

interface ChineseInputProps {
  /** 输入框值 */
  value?: string
  /** 值变化回调 */
  onChange?: (value: string) => void
  /** 占位符文本 */
  placeholder?: string
  /** 标签文本 */
  label?: string
  /** 错误信息 */
  error?: string
  /** 帮助文本 */
  helperText?: string
  /** 是否必填 */
  required?: boolean
  /** 是否禁用 */
  disabled?: boolean
  /** 是否只读 */
  readOnly?: boolean
  /** 最小长度 */
  minLength?: number
  /** 最大长度 */
  maxLength?: number
  /** 输入框类型 */
  type?: 'text' | 'password' | 'email' | 'tel'
  /** 自定义样式类名 */
  className?: string
  /** 是否显示字符计数 */
  showCount?: boolean
  /** 是否自动聚焦 */
  autoFocus?: boolean
  /** 是否支持中文输入法 */
  supportIME?: boolean
  /** 输入验证规则 */
  validation?: 'chinese' | 'mixed' | 'none'
  /** 失焦回调 */
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void
  /** 聚焦回调 */
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void
  /** 按键回调 */
  onKeyDown?: (event: React.KeyboardEvent<HTMLInputElement>) => void
}

const ChineseInput: React.FC<ChineseInputProps> = ({
  value = '',
  onChange,
  placeholder,
  label,
  error,
  helperText,
  required = false,
  disabled = false,
  readOnly = false,
  minLength,
  maxLength,
  type = 'text',
  className,
  showCount = false,
  autoFocus = false,
  supportIME = true,
  validation = 'mixed',
  onBlur,
  onFocus,
  onKeyDown,
}) => {
  const [isFocused, setIsFocused] = useState(false)
  const [isComposing, setIsComposing] = useState(false)
  const [internalError, setInternalError] = useState<string>('')
  const inputRef = useRef<HTMLInputElement>(null)

  // 🔍 验证输入内容
  const validateInput = useCallback((inputValue: string) => {
    let validationError = ''

    // 必填验证
    if (required) {
      const requiredResult = validateRequired(inputValue, label || '此字段')
      if (!requiredResult.isValid) {
        validationError = requiredResult.message
      }
    }

    // 长度验证
    if (!validationError && inputValue) {
      const lengthResult = validateLength(inputValue, minLength, maxLength, label || '此字段')
      if (!lengthResult.isValid) {
        validationError = lengthResult.message
      }
    }

    // 中文验证
    if (!validationError && validation === 'chinese' && inputValue) {
      const chineseRegex = /^[\u4e00-\u9fa5\s]*$/
      if (!chineseRegex.test(inputValue)) {
        validationError = '只能输入中文字符'
      }
    }

    setInternalError(validationError)
    return validationError === ''
  }, [required, minLength, maxLength, label, validation])

  // 🔄 处理输入变化
  const handleChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value

    // 如果正在使用输入法，延迟验证
    if (!isComposing) {
      validateInput(newValue)
    }

    onChange?.(newValue)
  }, [isComposing, validateInput, onChange])

  // 🎯 处理聚焦
  const handleFocus = useCallback((event: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(true)
    onFocus?.(event)
  }, [onFocus])

  // 🎯 处理失焦
  const handleBlur = useCallback((event: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(false)
    validateInput(value)
    onBlur?.(event)
  }, [value, validateInput, onBlur])

  // 🇨🇳 处理中文输入法开始
  const handleCompositionStart = useCallback(() => {
    if (supportIME) {
      setIsComposing(true)
    }
  }, [supportIME])

  // 🇨🇳 处理中文输入法结束
  const handleCompositionEnd = useCallback((event: React.CompositionEvent<HTMLInputElement>) => {
    if (supportIME) {
      setIsComposing(false)
      validateInput(event.currentTarget.value)
    }
  }, [supportIME, validateInput])

  // 🎨 计算样式类名
  const inputClasses = cn(
    // 基础样式
    'w-full px-4 py-3 rounded-xl border transition-all duration-200',
    'bg-white/10 backdrop-blur-md text-glass-text-primary placeholder-glass-text-secondary',
    'focus:outline-none focus:ring-2 focus:ring-white/20',
    
    // 状态样式
    {
      'border-white/20 hover:border-white/30': !error && !internalError,
      'border-red-400 bg-red-50/10': error || internalError,
      'border-green-400 bg-green-50/10': !error && !internalError && value && !isFocused,
      'opacity-50 cursor-not-allowed': disabled,
      'bg-gray-50/10': readOnly,
    },
    
    // 聚焦样式
    isFocused && !disabled && 'border-blue-400 bg-blue-50/10',
    
    className
  )

  // 🎨 标签样式
  const labelClasses = cn(
    'block text-sm font-medium text-glass-text-primary mb-2',
    required && "after:content-['*'] after:text-red-400 after:ml-1"
  )

  // 📊 字符计数
  const characterCount = value.length
  const isOverLimit = maxLength ? characterCount > maxLength : false

  // 🎨 计数器样式
  const countClasses = cn(
    'text-xs',
    {
      'text-glass-text-secondary': !isOverLimit,
      'text-red-400': isOverLimit,
    }
  )

  // 🔍 显示的错误信息
  const displayError = error || internalError

  // 🎯 自动聚焦
  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus()
    }
  }, [autoFocus])

  return (
    <div className="space-y-2">
      {/* 📝 标签 */}
      {label && (
        <label className={labelClasses}>
          {label}
        </label>
      )}

      {/* 📦 输入框容器 */}
      <div className="relative">
        <input
          ref={inputRef}
          type={type}
          value={value}
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onKeyDown={onKeyDown}
          onCompositionStart={handleCompositionStart}
          onCompositionEnd={handleCompositionEnd}
          placeholder={placeholder}
          disabled={disabled}
          readOnly={readOnly}
          maxLength={maxLength}
          className={inputClasses}
          autoComplete="off"
          spellCheck="false"
        />

        {/* ✅ 状态图标 */}
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center space-x-2">
          {/* 🔄 输入法状态指示器 */}
          {supportIME && isComposing && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="w-2 h-2 bg-blue-400 rounded-full"
              title="正在使用输入法"
            />
          )}

          {/* 📊 字符计数 */}
          {showCount && maxLength && (
            <span className={countClasses}>
              {characterCount}/{maxLength}
            </span>
          )}

          {/* ❌ 错误图标 */}
          {displayError && (
            <ExclamationCircleIcon className="w-5 h-5 text-red-400" />
          )}

          {/* ✅ 成功图标 */}
          {!displayError && value && !isFocused && (
            <CheckCircleIcon className="w-5 h-5 text-green-400" />
          )}
        </div>
      </div>

      {/* 💬 帮助文本和错误信息 */}
      <div className="min-h-[1.25rem]">
        {displayError ? (
          <motion.p
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-sm text-red-400 flex items-center space-x-1"
          >
            <ExclamationCircleIcon className="w-4 h-4 flex-shrink-0" />
            <span>{displayError}</span>
          </motion.p>
        ) : helperText ? (
          <p className="text-sm text-glass-text-secondary">
            {helperText}
          </p>
        ) : null}
      </div>
    </div>
  )
}

export default ChineseInput