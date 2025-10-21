import React from 'react'
import { motion } from 'framer-motion'
import AnsibleConfigPanel from '../../components/Settings/AnsibleConfigPanel'

/**
 * 🛡️ Ansible配置页面
 * 
 * 功能：
 * - Ansible相关配置
 * - 连接设置
 * - 执行参数配置
 */
const AnsibleConfig: React.FC = () => {
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
            <span className="text-2xl">🛡️</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-glass-text-primary">
              Ansible配置
            </h1>
            <p className="text-sm text-glass-text-secondary mt-1">
              配置Ansible执行环境和参数
            </p>
          </div>
        </div>
      </div>

      {/* 🛡️ Ansible配置面板 */}
      <AnsibleConfigPanel />
    </motion.div>
  )
}

export default AnsibleConfig
