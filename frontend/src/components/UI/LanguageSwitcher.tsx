import React, { useState } from 'react'
// import { useTranslation } from 'react-i18next' // 暂时不使用
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDownIcon, LanguageIcon } from '@heroicons/react/24/outline'
import { supportedLanguages, changeLanguage, getCurrentLanguage } from '../../i18n'
import { cn } from '../../utils'

/**
 * 🌐 语言切换器组件
 * 
 * 功能：
 * - 显示当前语言
 * - 提供语言切换下拉菜单
 * - 玻璃态设计风格
 * - 本地存储语言偏好
 */

interface LanguageSwitcherProps {
  /** 组件大小 */
  size?: 'sm' | 'md' | 'lg'
  /** 是否显示文字标签 */
  showLabel?: boolean
  /** 自定义样式类名 */
  className?: string
  /** 下拉菜单位置 */
  placement?: 'bottom-left' | 'bottom-right' | 'top-left' | 'top-right'
}

const LanguageSwitcher: React.FC<LanguageSwitcherProps> = ({
  size = 'md',
  showLabel = true,
  className,
  placement = 'bottom-right'
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const currentLang = getCurrentLanguage()

  // 🎯 获取当前语言信息
  const currentLanguage = supportedLanguages.find(lang => lang.code === currentLang) || supportedLanguages[0]

  // 🎨 尺寸样式映射
  const sizeStyles = {
    sm: {
      button: 'px-2 py-1 text-sm',
      icon: 'w-4 h-4',
      dropdown: 'min-w-[120px]'
    },
    md: {
      button: 'px-3 py-2 text-sm',
      icon: 'w-5 h-5',
      dropdown: 'min-w-[140px]'
    },
    lg: {
      button: 'px-4 py-3 text-base',
      icon: 'w-6 h-6',
      dropdown: 'min-w-[160px]'
    }
  }

  // 🎨 下拉菜单位置样式
  const placementStyles = {
    'bottom-left': 'top-full left-0 mt-2',
    'bottom-right': 'top-full right-0 mt-2',
    'top-left': 'bottom-full left-0 mb-2',
    'top-right': 'bottom-full right-0 mb-2'
  }

  const styles = sizeStyles[size]

  // 🔄 处理语言切换
  const handleLanguageChange = (langCode: string) => {
    changeLanguage(langCode)
    setIsOpen(false)
  }

  // 🖱️ 处理点击外部关闭
  const handleClickOutside = () => {
    setIsOpen(false)
  }

  return (
    <div className={cn('relative', className)}>
      {/* 🔘 语言切换按钮 */}
      <motion.button
        className={cn(
          'glass-button flex items-center gap-2 transition-all duration-200',
          'hover:bg-white/30 focus:outline-none focus:ring-2 focus:ring-white/20',
          styles.button
        )}
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ y: -1 }}
        whileTap={{ y: 0 }}
      >
        {/* 🌐 语言图标 */}
        <LanguageIcon className={styles.icon} />
        
        {/* 🏷️ 当前语言标识 */}
        <span className="text-lg">{currentLanguage.flag}</span>
        
        {/* 📝 语言名称（可选） */}
        {showLabel && (
          <span className="font-medium text-glass-text-primary">
            {currentLanguage.name}
          </span>
        )}
        
        {/* 🔽 下拉箭头 */}
        <ChevronDownIcon 
          className={cn(
            styles.icon, 
            'transition-transform duration-200',
            isOpen && 'rotate-180'
          )} 
        />
      </motion.button>

      {/* 📋 语言选择下拉菜单 */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* 🖱️ 点击遮罩层关闭菜单 */}
            <div 
              className="fixed inset-0 z-10" 
              onClick={handleClickOutside}
            />
            
            {/* 📋 下拉菜单 */}
            <motion.div
              className={cn(
                'absolute z-20 glass-container py-2 shadow-lg',
                styles.dropdown,
                placementStyles[placement]
              )}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.15 }}
            >
              {supportedLanguages.map((language) => (
                <motion.button
                  key={language.code}
                  className={cn(
                    'w-full px-4 py-2 text-left flex items-center gap-3',
                    'hover:bg-white/20 transition-colors duration-150',
                    'text-glass-text-primary',
                    currentLang === language.code && 'bg-white/10'
                  )}
                  onClick={() => handleLanguageChange(language.code)}
                  whileHover={{ x: 4 }}
                  whileTap={{ x: 2 }}
                >
                  {/* 🏷️ 国旗图标 */}
                  <span className="text-lg">{language.flag}</span>
                  
                  {/* 📝 语言名称 */}
                  <span className="font-medium">{language.name}</span>
                  
                  {/* ✅ 当前选中标识 */}
                  {currentLang === language.code && (
                    <motion.div
                      className="ml-auto w-2 h-2 bg-blue-500 rounded-full"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.1 }}
                    />
                  )}
                </motion.button>
              ))}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}

export default LanguageSwitcher