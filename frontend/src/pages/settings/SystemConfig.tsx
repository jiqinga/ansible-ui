import React from 'react'
import { motion } from 'framer-motion'
import SystemConfigPanel from '../../components/Settings/SystemConfigPanel'
import ConfigBackupPanel from '../../components/Settings/ConfigBackupPanel'

/**
 * 🔧 系统配置页面
 * 
 * 功能：
 * - 系统基础配置
 * - 配置备份与恢复
 */
const SystemConfig: React.FC = () => {
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
            <span className="text-2xl">🔧</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-glass-text-primary">
              系统配置
            </h1>
            <p className="text-sm text-glass-text-secondary mt-1">
              管理系统基础配置和备份
            </p>
          </div>
        </div>
      </div>

      {/* 🔧 系统配置面板 */}
      <SystemConfigPanel />

      {/* 💾 配置备份面板 */}
      <ConfigBackupPanel />
    </motion.div>
  )
}

export default SystemConfig
