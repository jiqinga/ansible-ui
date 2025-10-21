import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Bars3Icon,
  BellIcon,
  UserCircleIcon,
  ChevronDownIcon,
  ArrowRightOnRectangleIcon,
  UserIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline'
import { useAuth } from '../../contexts/AuthContext'
// import { AuthStatusIndicator } from '../Auth/ProtectedRoute'

interface NavbarProps {
  onMenuClick: () => void
  sidebarOpen: boolean
}

/**
 * 🎨 导航栏组件
 * 
 * 功能：
 * - 玻璃态顶部导航
 * - 用户菜单和认证状态
 * - 通知中心
 * - 登出功能
 */
const Navbar: React.FC<NavbarProps> = ({ onMenuClick }) => {
  const { state, logout } = useAuth()
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [showNotifications, setShowNotifications] = useState(false)
  const userMenuRef = useRef<HTMLDivElement>(null)
  const notificationRef = useRef<HTMLDivElement>(null)

  // 🖱️ 点击外部关闭用户菜单和通知面板
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false)
      }
      if (notificationRef.current && !notificationRef.current.contains(event.target as Node)) {
        setShowNotifications(false)
      }
    }

    if (showUserMenu || showNotifications) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showUserMenu, showNotifications])

  return (
    <motion.nav
      className="fixed top-0 left-0 right-0 z-50 glass-nav-primary px-4 py-4"
      style={{ minHeight: '7rem' }}
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
    >
      <div className="flex items-center justify-between">
        {/* 🎨 左侧：菜单按钮和Logo */}
        <div className="flex items-center space-x-4">
          {/* 📱 菜单按钮 */}
          <motion.button
            onClick={onMenuClick}
            className="glass-button p-2 lg:hidden"
            whileHover={{ opacity: 0.8 }}
            whileTap={{ opacity: 0.6 }}
          >
            <Bars3Icon className="w-6 h-6 text-glass-text-primary" />
          </motion.button>

          {/* 🚀 Logo和标题 */}
          <div className="flex items-center space-x-3">
            <motion.div
              className="w-8 h-8 glass-container rounded-lg flex items-center justify-center"
              whileHover={{ rotate: 360 }}
              transition={{ duration: 0.5 }}
            >
              <span className="text-lg">🚀</span>
            </motion.div>
            <div className="hidden sm:block">
              <h1 className="text-lg font-bold text-glass-text-primary">
                Ansible Web UI
              </h1>
              <p className="text-xs text-glass-text-secondary">
                现代化自动化管理平台
              </p>
            </div>
          </div>
        </div>

        {/* 🎨 中间：占位保持左右布局平衡 */}
        <div className="flex-1" />

        {/* 🎨 右侧：操作按钮 */}
        <div className="flex items-center space-x-3">
          {/* 🔔 通知按钮 */}
          <div className="relative" ref={notificationRef}>
            <motion.button
              onClick={() => setShowNotifications(!showNotifications)}
              className="glass-button p-2 relative"
              whileHover={{ opacity: 0.8 }}
              whileTap={{ opacity: 0.6 }}
            >
              <BellIcon className="w-5 h-5 text-glass-text-primary" />
              {/* 🔴 通知小红点 */}
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full flex items-center justify-center">
                <span className="w-1.5 h-1.5 bg-white rounded-full"></span>
              </span>
            </motion.button>

            {/* 🎨 通知下拉面板 */}
            <AnimatePresence>
              {showNotifications && (
                <motion.div
                  className="absolute right-0 top-full mt-2 w-80 glass-container rounded-glass-md shadow-glass-lg z-50"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                >
                  {/* 📋 通知标题 */}
                  <div className="p-4 border-b border-white/10">
                    <div className="flex items-center justify-between">
                      <h3 className="text-glass-text-primary font-medium">
                        🔔 通知中心
                      </h3>
                      <span className="text-xs text-glass-text-secondary">
                        3条未读
                      </span>
                    </div>
                  </div>

                  {/* 📋 通知列表 */}
                  <div className="max-h-96 overflow-y-auto">
                    {/* 示例通知项 */}
                    <motion.div
                      className="p-4 border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer"
                      whileHover={{ x: 4 }}
                      transition={{ duration: 0.2 }}
                    >
                      <div className="flex items-start space-x-3">
                        <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                        <div className="flex-1">
                          <p className="text-glass-text-primary text-sm">
                            ✅ Playbook执行成功
                          </p>
                          <p className="text-glass-text-secondary text-xs mt-1">
                            deploy-web.yml 已成功执行完成
                          </p>
                          <p className="text-glass-text-secondary text-xs mt-1">
                            5分钟前
                          </p>
                        </div>
                      </div>
                    </motion.div>

                    <motion.div
                      className="p-4 border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer"
                      whileHover={{ x: 4 }}
                      transition={{ duration: 0.2 }}
                    >
                      <div className="flex items-start space-x-3">
                        <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2 flex-shrink-0"></div>
                        <div className="flex-1">
                          <p className="text-glass-text-primary text-sm">
                            ⚠️ 主机连接警告
                          </p>
                          <p className="text-glass-text-secondary text-xs mt-1">
                            主机 192.168.1.100 响应缓慢
                          </p>
                          <p className="text-glass-text-secondary text-xs mt-1">
                            15分钟前
                          </p>
                        </div>
                      </div>
                    </motion.div>

                    <motion.div
                      className="p-4 hover:bg-white/5 transition-colors cursor-pointer"
                      whileHover={{ x: 4 }}
                      transition={{ duration: 0.2 }}
                    >
                      <div className="flex items-start space-x-3">
                        <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                        <div className="flex-1">
                          <p className="text-glass-text-primary text-sm">
                            🎉 系统更新完成
                          </p>
                          <p className="text-glass-text-secondary text-xs mt-1">
                            Ansible Web UI 已更新到最新版本
                          </p>
                          <p className="text-glass-text-secondary text-xs mt-1">
                            1小时前
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  </div>

                  {/* 📋 底部操作 */}
                  <div className="p-3 border-t border-white/10">
                    <motion.button
                      className="w-full text-center text-glass-text-accent text-sm hover:text-glass-text-primary transition-colors"
                      whileHover={{ y: -1 }}
                      transition={{ duration: 0.2 }}
                    >
                      查看全部通知
                    </motion.button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* 👤 用户菜单 */}
          <div className="relative" ref={userMenuRef}>
            <motion.button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="glass-button p-2 flex items-center space-x-2"
              whileHover={{ y: -1 }}
              whileTap={{ y: 0 }}
            >
              <UserCircleIcon className="w-6 h-6 text-glass-text-primary" />
              <div className="hidden sm:block text-left">
                <div className="text-glass-text-primary text-sm font-medium">
                  {state.user?.username || '用户'}
                </div>
                <div className="text-glass-text-secondary text-xs">
                  {state.user?.role === 'admin' ? '🔧 管理员' : 
                   state.user?.role === 'operator' ? '⚙️ 操作员' : '👁️ 查看者'}
                </div>
              </div>
              <ChevronDownIcon 
                className={`w-4 h-4 text-glass-text-secondary transition-transform duration-200 ${
                  showUserMenu ? 'rotate-180' : ''
                }`} 
              />
            </motion.button>

            {/* 🎨 用户下拉菜单 */}
            <AnimatePresence>
              {showUserMenu && (
                <motion.div
                  className="absolute right-0 top-full mt-2 w-64 glass-container rounded-glass-md shadow-glass-lg z-50"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                >
                  {/* 👤 用户信息 */}
                  <div className="p-4 border-b border-white/10">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 glass-container rounded-full flex items-center justify-center">
                        <UserIcon className="w-5 h-5 text-glass-text-accent" />
                      </div>
                      <div>
                        <div className="text-glass-text-primary font-medium">
                          {state.user?.username}
                        </div>
                        <div className="text-glass-text-secondary text-sm">
                          {state.user?.email || 'user@example.com'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 📋 菜单项 */}
                  <div className="p-2">
                    <motion.button
                      className="w-full flex items-center space-x-3 p-3 rounded-glass-sm hover:bg-white/10 transition-colors text-left"
                      whileHover={{ x: 4 }}
                      transition={{ duration: 0.2 }}
                    >
                      <UserIcon className="w-5 h-5 text-glass-text-secondary" />
                      <span className="text-glass-text-primary">个人资料</span>
                    </motion.button>

                    <motion.button
                      className="w-full flex items-center space-x-3 p-3 rounded-glass-sm hover:bg-white/10 transition-colors text-left"
                      whileHover={{ x: 4 }}
                      transition={{ duration: 0.2 }}
                    >
                      <Cog6ToothIcon className="w-5 h-5 text-glass-text-secondary" />
                      <span className="text-glass-text-primary">系统设置</span>
                    </motion.button>

                    <div className="border-t border-white/10 my-2"></div>

                    <motion.button
                      onClick={() => {
                        setShowUserMenu(false)
                        logout()
                      }}
                      className="w-full flex items-center space-x-3 p-3 rounded-glass-sm hover:bg-red-500/20 transition-colors text-left group"
                      whileHover={{ x: 4 }}
                      transition={{ duration: 0.2 }}
                    >
                      <ArrowRightOnRectangleIcon className="w-5 h-5 text-glass-text-secondary group-hover:text-red-500" />
                      <span className="text-glass-text-primary group-hover:text-red-600">
                        退出登录
                      </span>
                    </motion.button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

    </motion.nav>
  )
}

export default Navbar
