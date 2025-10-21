import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { useLocation, useNavigate } from 'react-router-dom'
import { 
  HomeIcon,
  ServerIcon,
  DocumentTextIcon,
  FolderIcon,
  PlayIcon,
  ClockIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  ArrowRightStartOnRectangleIcon,
  XMarkIcon,
  ChevronDownIcon,
  UserGroupIcon,
  WrenchScrewdriverIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

interface MenuItem {
  key: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  path?: string
  color: string
  bgColor: string
  children?: MenuItem[]
}

/**
 * 🎨 侧边栏组件
 * 
 * 功能：
 * - 玻璃态侧边导航
 * - 响应式折叠
 * - 路由导航
 * - 动画效果
 */
const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { t } = useTranslation()
  const location = useLocation()
  const navigate = useNavigate()
  const [expandedMenus, setExpandedMenus] = useState<string[]>([])

  // 🎨 导航菜单项
  const menuItems: MenuItem[] = [
    {
      key: 'dashboard',
      label: t('navigation.dashboard'),
      icon: HomeIcon,
      path: '/dashboard',
      color: 'text-blue-600',
      bgColor: 'bg-blue-500/20',
    },
    {
      key: 'inventory',
      label: t('navigation.inventory'),
      icon: ServerIcon,
      path: '/inventory',
      color: 'text-green-600',
      bgColor: 'bg-green-500/20',
    },
    {
      key: 'playbooks',
      label: t('navigation.playbooks'),
      icon: DocumentTextIcon,
      path: '/playbooks',
      color: 'text-purple-600',
      bgColor: 'bg-purple-500/20',
    },
    {
      key: 'projects',
      label: '项目管理',
      icon: FolderIcon,
      path: '/projects',
      color: 'text-pink-600',
      bgColor: 'bg-pink-500/20',
    },
    {
      key: 'execution',
      label: t('navigation.execution'),
      icon: PlayIcon,
      path: '/execution',
      color: 'text-orange-600',
      bgColor: 'bg-orange-500/20',
    },
    {
      key: 'history',
      label: t('navigation.history'),
      icon: ClockIcon,
      path: '/history',
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-500/20',
    },
    {
      key: 'monitoring',
      label: t('navigation.monitoring'),
      icon: ChartBarIcon,
      path: '/monitoring',
      color: 'text-cyan-600',
      bgColor: 'bg-cyan-500/20',
    },
    {
      key: 'settings',
      label: t('navigation.settings'),
      icon: Cog6ToothIcon,
      color: 'text-gray-600',
      bgColor: 'bg-gray-500/20',
      children: [
        {
          key: 'settings-system',
          label: '系统配置',
          icon: WrenchScrewdriverIcon,
          path: '/settings/system',
          color: 'text-gray-600',
          bgColor: 'bg-gray-500/20',
        },
        {
          key: 'settings-users',
          label: '用户管理',
          icon: UserGroupIcon,
          path: '/settings/users',
          color: 'text-blue-600',
          bgColor: 'bg-blue-500/20',
        },
        {
          key: 'settings-ansible',
          label: 'Ansible配置',
          icon: ShieldCheckIcon,
          path: '/settings/ansible',
          color: 'text-purple-600',
          bgColor: 'bg-purple-500/20',
        },
      ],
    },
  ]

  // 🎯 切换子菜单展开状态
  const toggleMenu = (key: string) => {
    setExpandedMenus(prev => 
      prev.includes(key) 
        ? prev.filter(k => k !== key)
        : [...prev, key]
    )
  }

  // 🎨 侧边栏动画配置
  const sidebarVariants = {
    open: {
      x: 0,
      transition: {
        type: 'spring',
        stiffness: 300,
        damping: 30,
      },
    },
    closed: {
      x: '-100%',
      transition: {
        type: 'spring',
        stiffness: 300,
        damping: 30,
      },
    },
  }

  const menuItemVariants = {
    open: {
      opacity: 1,
      x: 0,
      transition: {
        type: 'spring',
        stiffness: 300,
        damping: 30,
      },
    },
    closed: {
      opacity: 0,
      x: -20,
    },
  }

  // 🎯 检查当前路由是否激活
  const isActive = (path?: string) => {
    if (!path) return false
    return location.pathname === path || (path === '/dashboard' && location.pathname === '/')
  }

  // 🎯 检查父菜单是否有激活的子项
  const hasActiveChild = (item: MenuItem) => {
    if (!item.children) return false
    return item.children.some(child => isActive(child.path))
  }

  // 🚀 导航处理
  const handleNavigation = (path?: string) => {
    if (path) {
      navigate(path)
      onClose() // 移动端关闭侧边栏
    }
  }

  // 🎨 渲染菜单项
  const renderMenuItem = (item: MenuItem, index: number, isChild = false) => {
    const hasChildren = item.children && item.children.length > 0
    const isExpanded = expandedMenus.includes(item.key)
    const active = isActive(item.path) || hasActiveChild(item)

    return (
      <div key={item.key}>
        <motion.button
          onClick={() => {
            if (hasChildren) {
              toggleMenu(item.key)
            } else {
              handleNavigation(item.path)
            }
          }}
          className={`w-full flex items-center justify-between p-3 rounded-glass transition-all duration-200 group ${
            isChild ? 'pl-12' : ''
          } ${
            active
              ? `${item.bgColor} ${item.color}`
              : 'hover:bg-white/10 text-glass-text-secondary hover:text-glass-text-primary'
          }`}
          whileHover={{ x: 2 }}
          whileTap={{ x: 0 }}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.1 }}
        >
          <div className="flex items-center space-x-3">
            <item.icon className="w-5 h-5 flex-shrink-0" />
            <AnimatePresence>
              {isOpen && (
                <motion.span
                  className="font-medium truncate"
                  initial={{ opacity: 0, width: 0 }}
                  animate={{ opacity: 1, width: 'auto' }}
                  exit={{ opacity: 0, width: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  {item.label}
                </motion.span>
              )}
            </AnimatePresence>
          </div>
          
          {/* 🎯 展开/收起图标 */}
          {hasChildren && isOpen && (
            <motion.div
              animate={{ rotate: isExpanded ? 180 : 0 }}
              transition={{ duration: 0.2 }}
            >
              <ChevronDownIcon className="w-4 h-4" />
            </motion.div>
          )}
          
          {/* 🎯 激活指示器 */}
          {active && !hasChildren && (
            <motion.div
              className="absolute right-0 w-1 h-8 bg-gradient-to-b from-transparent via-current to-transparent rounded-l-full"
              layoutId="activeIndicator"
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            />
          )}
        </motion.button>

        {/* 🎨 子菜单 */}
        <AnimatePresence>
          {hasChildren && isExpanded && isOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden space-y-1 mt-1"
            >
              {item.children!.map((child, childIndex) => (
                <motion.button
                  key={child.key}
                  onClick={() => handleNavigation(child.path)}
                  className={`w-full flex items-center space-x-3 pl-12 pr-3 py-2 rounded-glass transition-all duration-200 ${
                    isActive(child.path)
                      ? `${child.bgColor} ${child.color}`
                      : 'hover:bg-white/10 text-glass-text-secondary hover:text-glass-text-primary'
                  }`}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: childIndex * 0.05 }}
                  whileHover={{ x: 4 }}
                  whileTap={{ x: 2 }}
                >
                  <child.icon className="w-4 h-4 flex-shrink-0" />
                  <span className="text-sm font-medium truncate">{child.label}</span>
                  
                  {/* 🎯 子项激活指示器 */}
                  {isActive(child.path) && (
                    <motion.div
                      className="absolute right-0 w-1 h-6 bg-gradient-to-b from-transparent via-current to-transparent rounded-l-full"
                      layoutId="activeChildIndicator"
                      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                    />
                  )}
                </motion.button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    )
  }

  // 🚪 退出登录
  const handleLogout = () => {
    // 实际项目中这里会调用登出API
    console.log('退出登录')
    navigate('/login')
  }

  return (
    <>
      {/* 🎨 桌面端侧边栏 */}
      <motion.aside
        className={`fixed left-0 top-[7rem] bottom-0 z-40 glass-nav-primary border-r border-white/10 transition-all duration-300 ${
          isOpen ? 'w-64' : 'w-16'
        } hidden lg:block`}
        initial={false}
      >
        <div className="flex flex-col h-full p-4">
          {/* 🎨 导航菜单 */}
          <nav className="flex-1 space-y-2 overflow-y-auto">
            {menuItems.map((item, index) => renderMenuItem(item, index))}
          </nav>

          {/* 🚪 退出按钮 */}
          <motion.button
            onClick={handleLogout}
            className="flex items-center space-x-3 p-3 rounded-glass text-red-400 hover:bg-red-500/20 transition-all duration-200"
            whileHover={{ x: 2 }}
            whileTap={{ x: 0 }}
          >
            <ArrowRightStartOnRectangleIcon className="w-5 h-5 flex-shrink-0" />
            <AnimatePresence>
              {isOpen && (
                <motion.span
                  className="font-medium"
                  initial={{ opacity: 0, width: 0 }}
                  animate={{ opacity: 1, width: 'auto' }}
                  exit={{ opacity: 0, width: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  {t('navigation.logout')}
                </motion.span>
              )}
            </AnimatePresence>
          </motion.button>
        </div>
      </motion.aside>

      {/* 🎨 移动端侧边栏 */}
      <AnimatePresence>
        {isOpen && (
          <motion.aside
            className="fixed left-0 top-0 bottom-0 w-64 glass-nav-primary z-50 lg:hidden"
            variants={sidebarVariants}
            initial="closed"
            animate="open"
            exit="closed"
          >
            <div className="flex flex-col h-full">
              {/* 🎨 移动端头部 */}
              <div className="flex items-center justify-between p-4 border-b border-white/10">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 glass-container rounded-lg flex items-center justify-center">
                    <span className="text-lg">🚀</span>
                  </div>
                  <div>
                    <h2 className="font-bold text-glass-text-primary">
                      Ansible Web UI
                    </h2>
                    <p className="text-xs text-glass-text-secondary">
                      自动化管理平台
                    </p>
                  </div>
                </div>
                <motion.button
                  onClick={onClose}
                  className="glass-button p-2"
                  whileHover={{ opacity: 0.8 }}
                  whileTap={{ opacity: 0.6 }}
                >
                  <XMarkIcon className="w-5 h-5 text-glass-text-primary" />
                </motion.button>
              </div>

              {/* 🎨 移动端导航菜单 */}
              <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
                {menuItems.map((item, index) => {
                  const hasChildren = item.children && item.children.length > 0
                  const isExpanded = expandedMenus.includes(item.key)
                  const active = isActive(item.path) || hasActiveChild(item)

                  return (
                    <div key={item.key}>
                      <motion.button
                        onClick={() => {
                          if (hasChildren) {
                            toggleMenu(item.key)
                          } else {
                            handleNavigation(item.path)
                          }
                        }}
                        className={`w-full flex items-center justify-between p-3 rounded-glass transition-all duration-200 ${
                          active
                            ? `${item.bgColor} ${item.color}`
                            : 'hover:bg-white/10 text-glass-text-secondary hover:text-glass-text-primary'
                        }`}
                        variants={menuItemVariants}
                        initial="closed"
                        animate="open"
                        transition={{ delay: index * 0.05 }}
                        whileHover={{ x: 2 }}
                        whileTap={{ x: 0 }}
                      >
                        <div className="flex items-center space-x-3">
                          <item.icon className="w-5 h-5" />
                          <span className="font-medium">{item.label}</span>
                        </div>
                        {hasChildren && (
                          <motion.div
                            animate={{ rotate: isExpanded ? 180 : 0 }}
                            transition={{ duration: 0.2 }}
                          >
                            <ChevronDownIcon className="w-4 h-4" />
                          </motion.div>
                        )}
                      </motion.button>

                      {/* 🎨 移动端子菜单 */}
                      <AnimatePresence>
                        {hasChildren && isExpanded && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="overflow-hidden space-y-1 mt-1"
                          >
                            {item.children!.map((child, childIndex) => (
                              <motion.button
                                key={child.key}
                                onClick={() => handleNavigation(child.path)}
                                className={`w-full flex items-center space-x-3 pl-12 pr-3 py-2 rounded-glass transition-all duration-200 ${
                                  isActive(child.path)
                                    ? `${child.bgColor} ${child.color}`
                                    : 'hover:bg-white/10 text-glass-text-secondary hover:text-glass-text-primary'
                                }`}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: childIndex * 0.05 }}
                                whileHover={{ x: 4 }}
                                whileTap={{ x: 2 }}
                              >
                                <child.icon className="w-4 h-4 flex-shrink-0" />
                                <span className="text-sm font-medium truncate">{child.label}</span>
                              </motion.button>
                            ))}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  )
                })}
              </nav>

              {/* 🚪 移动端退出按钮 */}
              <div className="p-4 border-t border-white/10">
                <motion.button
                  onClick={handleLogout}
                  className="w-full flex items-center space-x-3 p-3 rounded-glass text-red-400 hover:bg-red-500/20 transition-all duration-200"
                  whileHover={{ x: 2 }}
                  whileTap={{ x: 0 }}
                >
                  <ArrowRightStartOnRectangleIcon className="w-5 h-5" />
                  <span className="font-medium">{t('navigation.logout')}</span>
                </motion.button>
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>
    </>
  )
}

export default Sidebar
