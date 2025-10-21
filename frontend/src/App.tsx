import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { AuthProvider } from './contexts/AuthContext'
import { NotificationProvider } from './contexts/NotificationContext'
import ProtectedRoute from './components/Auth/ProtectedRoute'
import Layout from './components/Layout/Layout'
import Dashboard from './pages/Dashboard'
import Inventory from './pages/Inventory'
import Playbooks from './pages/Playbooks'
import { Projects } from './pages/Projects'
import Execution from './pages/Execution'
import History from './pages/History'
import Monitoring from './pages/Monitoring'
import Settings from './pages/Settings'
import Login from './pages/Login'
import NotFound from './pages/NotFound'
import UserManagement from './pages/settings/UserManagement'
import SystemConfig from './pages/settings/SystemConfig'
import AnsibleConfig from './pages/settings/AnsibleConfig'
import AnimationTest from './pages/AnimationTest'
import { useTokenRefresh, useVisibilityRefresh, useNetworkRefresh } from './hooks/useTokenRefresh'
import './styles/App.css'

/**
 * 🔄 Token刷新管理组件
 * 在认证上下文内部使用Token刷新Hook
 */
const TokenRefreshManager: React.FC = () => {
  useTokenRefresh()
  useVisibilityRefresh()
  useNetworkRefresh()
  return null
}

/**
 * 🎨 主应用组件
 * 
 * 功能：
 * - 路由配置和管理
 * - 认证状态管理
 * - 全局布局和样式
 * - 国际化支持
 * - 玻璃态动画效果
 */
function App() {
  const { ready } = useTranslation()

  // 🔄 等待国际化资源加载完成
  if (!ready) {
    return (
      <div className="min-h-screen gradient-bg-primary flex items-center justify-center">
        <motion.div
          className="glass-container p-8 text-center"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
        >
          <div className="w-10 h-10 border-3 border-white/30 border-t-white rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-glass-text-primary font-medium">🚀 正在初始化应用...</p>
        </motion.div>
      </div>
    )
  }

  return (
    <NotificationProvider>
      <AuthProvider>
        <TokenRefreshManager />
        <div className="App min-h-screen gradient-bg-primary">
          <Routes>
            {/* 🔐 登录页面 - 无需认证 */}
            <Route path="/login" element={<Login />} />
            
            {/* 🏠 主应用页面 - 需要认证和布局 */}
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="inventory" element={<Inventory />} />
              <Route path="playbooks" element={<Playbooks />} />
              <Route path="projects" element={<Projects />} />
              <Route path="execution" element={<Execution />} />
              <Route path="history" element={<History />} />
              <Route path="monitoring" element={<Monitoring />} />
              <Route path="settings" element={<Settings />} />
              <Route path="settings/system" element={<SystemConfig />} />
              <Route path="settings/users" element={<UserManagement />} />
              <Route path="settings/ansible" element={<AnsibleConfig />} />
              {/* 🧪 动画测试页面 - 用于验证修复效果 */}
              <Route path="animation-test" element={<AnimationTest />} />
            </Route>
            
            {/* 🔍 404页面 */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </div>
      </AuthProvider>
    </NotificationProvider>
  )
}

export default App