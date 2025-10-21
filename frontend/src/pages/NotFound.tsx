import React from 'react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { 
  HomeIcon, 
  ArrowLeftIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'

/**
 * 🔍 404页面组件
 * 
 * 功能：
 * - 玻璃态错误页面
 * - 导航返回功能
 * - 动画效果
 */
const NotFound: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()

  // 🎨 页面动画配置
  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
        ease: 'easeOut',
      },
    },
  }

  const floatingVariants = {
    animate: {
      y: [-10, 10, -10],
      transition: {
        duration: 3,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
  }

  return (
    <div className="min-h-screen gradient-bg-primary flex items-center justify-center p-4">
      <motion.div
        className="text-center max-w-md w-full"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* 🎨 错误卡片 */}
        <div className="glass-container p-8">
          {/* 🎨 404图标 */}
          <motion.div
            className="mb-6"
            variants={floatingVariants}
            animate="animate"
          >
            <div className="w-24 h-24 mx-auto glass-container rounded-full flex items-center justify-center mb-4">
              <ExclamationTriangleIcon className="w-12 h-12 text-orange-500" />
            </div>
            <div className="text-6xl font-bold text-gradient-primary mb-2">
              404
            </div>
          </motion.div>

          {/* 🎨 错误信息 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <h1 className="text-2xl font-bold text-glass-text-primary mb-3">
              {t('errors.notFound')} 🔍
            </h1>
            <p className="text-glass-text-secondary mb-6 leading-relaxed">
              抱歉，您访问的页面不存在。可能是链接错误或页面已被移动。
            </p>
          </motion.div>

          {/* 🎨 操作按钮 */}
          <motion.div
            className="space-y-3"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <button
              onClick={() => navigate('/')}
              className="w-full glass-btn-primary py-3 flex items-center justify-center space-x-2"
            >
              <HomeIcon className="w-5 h-5" />
              <span>{t('errors.goHome')}</span>
            </button>
            
            <button
              onClick={() => navigate(-1)}
              className="w-full glass-button bg-white/10 hover:bg-white/20 py-3 flex items-center justify-center space-x-2"
            >
              <ArrowLeftIcon className="w-5 h-5" />
              <span>{t('common.back')}</span>
            </button>
          </motion.div>

          {/* 🎨 帮助信息 */}
          <motion.div
            className="mt-6 pt-6 border-t border-white/20"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7 }}
          >
            <p className="text-glass-text-secondary text-sm">
              如果问题持续存在，请联系系统管理员
            </p>
          </motion.div>
        </div>

        {/* 🎨 背景装饰元素 */}
        <div className="absolute inset-0 -z-10 overflow-hidden">
          {/* 浮动装饰球 */}
          {[...Array(6)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-4 h-4 bg-white/10 rounded-full"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
              }}
              animate={{
                y: [-20, 20, -20],
                opacity: [0.3, 0.8, 0.3],
              }}
              transition={{
                duration: 3 + Math.random() * 2,
                repeat: Infinity,
                delay: Math.random() * 2,
                ease: 'easeInOut',
              }}
            />
          ))}
          
          {/* 大型装饰元素 */}
          <motion.div
            className="absolute top-1/4 left-1/4 w-32 h-32 bg-gradient-to-r from-purple-500/20 to-blue-500/20 rounded-full blur-xl"
            animate={{
              scale: [1, 1.3, 1],
              rotate: [0, 180, 360],
            }}
            transition={{
              duration: 8,
              repeat: Infinity,
              ease: 'linear',
            }}
          />
          
          <motion.div
            className="absolute bottom-1/4 right-1/4 w-24 h-24 bg-gradient-to-r from-pink-500/20 to-orange-500/20 rounded-full blur-xl"
            animate={{
              scale: [1.3, 1, 1.3],
              rotate: [360, 180, 0],
            }}
            transition={{
              duration: 6,
              repeat: Infinity,
              ease: 'linear',
            }}
          />
        </div>
      </motion.div>
    </div>
  )
}

export default NotFound