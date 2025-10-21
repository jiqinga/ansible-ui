import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

// 🌐 导入语言资源
import zhCN from './locales/zh-CN.json'
import enUS from './locales/en-US.json'

/**
 * 🌐 国际化配置
 * 
 * 功能：
 * - 支持中文和英文
 * - 自动检测浏览器语言
 * - 本地存储语言偏好
 * - 中文优先原则
 */
i18n
  // 🔍 检测用户语言偏好
  .use(LanguageDetector)
  // ⚛️ 集成React
  .use(initReactI18next)
  // ⚙️ 初始化配置
  .init({
    // 🌐 语言资源
    resources: {
      'zh-CN': {
        translation: zhCN,
      },
      'en-US': {
        translation: enUS,
      },
    },
    
    // 🎯 默认语言（中文优先）
    lng: 'zh-CN',
    fallbackLng: 'zh-CN',
    
    // 🔍 语言检测配置
    detection: {
      // 🔍 检测顺序：本地存储 > 浏览器语言 > 默认语言
      order: ['localStorage', 'navigator', 'htmlTag'],
      // 💾 缓存用户选择
      caches: ['localStorage'],
      // 🔑 本地存储键名
      lookupLocalStorage: 'ansible-ui-language',
    },
    
    // 🔧 插值配置
    interpolation: {
      // ⚛️ React已经处理了XSS防护
      escapeValue: false,
    },
    
    // 🐛 调试模式（开发环境）
    debug: process.env.NODE_ENV === 'development',
    
    // 🎯 命名空间配置
    defaultNS: 'translation',
    ns: ['translation'],
    
    // ⚡ 性能优化
    load: 'languageOnly', // 只加载语言，不加载地区变体
    preload: ['zh-CN'], // 预加载中文
    
    // 🔄 更新配置
    updateMissing: process.env.NODE_ENV === 'development', // 开发环境下自动添加缺失的翻译
    
    // 🎨 格式化配置
    returnObjects: true, // 允许返回对象
    joinArrays: '\n', // 数组连接符
    
    // 🔧 React特定配置
    react: {
      // 🔄 绑定事件
      bindI18n: 'languageChanged',
      bindI18nStore: '',
      // 🎯 事务模式
      transEmptyNodeValue: '',
      transSupportBasicHtmlNodes: true,
      transKeepBasicHtmlNodesFor: ['br', 'strong', 'i', 'em'],
      // 🎨 使用Suspense
      useSuspense: false,
    },
  })

export default i18n

/**
 * 🛠️ 语言切换工具函数
 */
export const changeLanguage = (language: string) => {
  i18n.changeLanguage(language)
}

/**
 * 🔍 获取当前语言
 */
export const getCurrentLanguage = () => {
  return i18n.language
}

/**
 * 🌐 支持的语言列表
 */
export const supportedLanguages = [
  { code: 'zh-CN', name: '中文', flag: '🇨🇳' },
  { code: 'en-US', name: 'English', flag: '🇺🇸' },
] as const

/**
 * 🎯 语言类型定义
 */
export type SupportedLanguage = typeof supportedLanguages[number]['code']