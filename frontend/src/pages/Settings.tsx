import React from 'react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import {
  WrenchScrewdriverIcon,
  UserGroupIcon,
  ShieldCheckIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline'

/**
 * ⚙️ 设置页面
 * 
 * 功能：
 * - 设置模块概览
 * - 快速导航到各个设置子页面
 */
const Settings: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()

  // 🎨 设置模块配置
  const settingsModules = [
    {
      id: 'system',
      title: '系统配置',
      description: '管理系统基础配置和备份',
      icon: WrenchScrewdriverIcon,
      color: 'text-gray-600',
      bgColor: 'bg-gray-500/20',
      path: '/settings/system',
      emoji: '🔧'
    },
    {
      id: 'users',
      title: '用户管理',
      description: '管理系统用户和权限设置',
      icon: UserGroupIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-500/20',
      path: '/settings/users',
      emoji: '👥'
    },
    {
      id: 'ansible',
      title: 'Ansible配置',
      description: '配置Ansible执行环境和参数',
      icon: ShieldCheckIcon,
      color: 'text-purple-600',
      bgColor: 'bg-purple-500/20',
      path: '/settings/ansible',
      emoji: '🛡️'
    },
  ]

  return (
    <motion.div
      className="space-y-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* 📋 页面标题 */}
      <div className="glass-card p-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 glass-container rounded-lg flex items-center justify-center">
            <span className="text-2xl">⚙️</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-glass-text-primary">
              {t('settings.title')}
            </h1>
            <p className="text-sm text-glass-text-secondary mt-1">
              {t('settings.description')}
            </p>
          </div>
        </div>
      </div>

      {/* 🎨 设置模块网格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {settingsModules.map((module, index) => (
          <motion.div
            key={module.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ y: -2 }}
            whileTap={{ y: 0 }}
          >
            <button
              onClick={() => navigate(module.path)}
              className="w-full glass-card p-6 text-left hover:bg-white/10 transition-all duration-200 group"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4 flex-1">
                  {/* 🎨 图标 */}
                  <div className={`w-12 h-12 ${module.bgColor} rounded-glass flex items-center justify-center flex-shrink-0`}>
                    <module.icon className={`w-6 h-6 ${module.color}`} />
                  </div>

                  {/* 📝 内容 */}
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-xl">{module.emoji}</span>
                      <h3 className="text-lg font-semibold text-glass-text-primary">
                        {module.title}
                      </h3>
                    </div>
                    <p className="text-sm text-glass-text-secondary">
                      {module.description}
                    </p>
                  </div>
                </div>

                {/* 🎯 箭头图标 */}
                <ChevronRightIcon className="w-5 h-5 text-glass-text-secondary group-hover:text-glass-text-primary group-hover:translate-x-1 transition-all duration-200 flex-shrink-0 ml-4" />
              </div>
            </button>
          </motion.div>
        ))}
      </div>

      {/* 💡 提示信息 */}
      <motion.div
        className="glass-card p-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
      >
        <div className="flex items-start space-x-3">
          <span className="text-2xl">💡</span>
          <div>
            <h3 className="font-semibold text-glass-text-primary mb-2">
              快速提示
            </h3>
            <ul className="space-y-2 text-sm text-glass-text-secondary">
              <li className="flex items-start space-x-2">
                <span className="text-blue-500 mt-1">•</span>
                <span>点击上方任意模块卡片即可进入对应的设置页面</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-blue-500 mt-1">•</span>
                <span>也可以通过左侧导航栏的系统设置菜单快速访问</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-blue-500 mt-1">•</span>
                <span>修改配置后请记得保存，部分配置可能需要重启服务生效</span>
              </li>
            </ul>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}

export default Settings
