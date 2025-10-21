import React, { useState, useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import Navbar from './Navbar'
import Sidebar from './Sidebar'

/**
 * 🏗️ 主布局组件
 * 
 * 功能：
 * - 响应式布局管理
 * - 侧边栏和导航栏集成
 * - 玻璃态设计
 * - 移动端适配
 */
const Layout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    if (typeof window === 'undefined') {
      return
    }

    const mediaQuery = window.matchMedia('(min-width: 1024px)')

    const updateSidebar = (event: MediaQueryList | MediaQueryListEvent) => {
      setSidebarOpen(event.matches)
    }

    updateSidebar(mediaQuery)

    const handler = (event: MediaQueryListEvent) => updateSidebar(event)

    if (typeof mediaQuery.addEventListener === 'function') {
      mediaQuery.addEventListener('change', handler)
      return () => mediaQuery.removeEventListener('change', handler)
    }

    mediaQuery.addListener(handler)
    return () => mediaQuery.removeListener(handler)
  }, [])


  // 🎨 页面过渡动画
  const pageVariants = {
    initial: { opacity: 0, y: 20 },
    in: { opacity: 1, y: 0 },
    out: { opacity: 0, y: -20 },
  }

  const pageTransition = {
    type: 'tween',
    ease: 'anticipate',
    duration: 0.4,
  }

  return (
    <div className="min-h-screen gradient-bg-primary">
      {/* 🎨 导航栏 */}
      <Navbar 
        onMenuClick={() => setSidebarOpen(prev => !prev)}
        sidebarOpen={sidebarOpen}
      />

      <div className="flex">
        {/* 🎨 侧边栏 */}
        <Sidebar 
          isOpen={sidebarOpen}
          onClose={() => {
            if (typeof window !== 'undefined' && window.matchMedia('(min-width: 1024px)').matches) {
              return
            }
            setSidebarOpen(false)
          }}
        />

        {/* 🎨 主内容区域 */}
        <main className={`flex-1 transition-all duration-300 ease-in-out ${
          sidebarOpen ? 'lg:ml-64' : 'lg:ml-16'
        }`}>
          <div className="pt-[7.5rem]"> {/* 根据导航高度预留 7.5rem 空间，避免内容被遮挡 */}
            <AnimatePresence mode="wait">
              <motion.div
                key={location.pathname}
                initial="initial"
                animate="in"
                exit="out"
                variants={pageVariants}
                transition={pageTransition}
                className="min-h-[calc(100vh-7.5rem)]"
              >
                <Outlet />
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>

      {/* 🎨 移动端遮罩层 */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 lg:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

export default Layout
