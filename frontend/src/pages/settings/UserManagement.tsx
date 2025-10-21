import React from 'react'
import { motion } from 'framer-motion'
import UserManagementPanel from '../../components/Settings/UserManagementPanel'

/**
 * 👥 用户管理页面
 * 
 * 功能：
 * - 用户列表管理
 * - 添加/编辑/删除用户
 * - 角色权限管理
 */
const UserManagement: React.FC = () => {
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
            <span className="text-2xl">👥</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-glass-text-primary">
              用户管理
            </h1>
            <p className="text-sm text-glass-text-secondary mt-1">
              管理系统用户和权限设置
            </p>
          </div>
        </div>
      </div>

      {/* 👥 用户管理面板 */}
      <UserManagementPanel />
    </motion.div>
  )
}

export default UserManagement
