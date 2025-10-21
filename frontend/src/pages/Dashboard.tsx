import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { 
  ChartBarIcon, 
  ServerIcon, 
  DocumentTextIcon, 
  PlayIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  CpuChipIcon,
  ArrowPathIcon,
  EyeIcon
} from '@heroicons/react/24/outline'
import { useChineseFormat } from '../hooks/useChineseFormat'
import { useNotification } from '../contexts/NotificationContext'
import DashboardService, { 
  DashboardStats, 
  SystemResources, 
  RecentTask, 
  QuickAction,
  SystemAlert,
  TrendData
} from '../services/dashboardService'

/**
 * 🏠 玻璃态主控制台组件
 * 
 * 功能：
 * - 实时系统统计信息和数据可视化
 * - 玻璃态卡片网格布局
 * - 实时系统状态监控面板
 * - 快速操作入口和最近任务展示
 * - 中文数据格式化和状态描述
 * - 自动刷新和实时更新
 */
const Dashboard: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { formatDate, formatDuration, formatFileSize } = useChineseFormat()
  const { addNotification } = useNotification()

  // 🔄 状态管理
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [systemResources, setSystemResources] = useState<SystemResources | null>(null)
  const [recentTasks, setRecentTasks] = useState<RecentTask[]>([])
  const [quickActions, setQuickActions] = useState<QuickAction[]>([])
  const [systemAlerts, setSystemAlerts] = useState<SystemAlert[]>([])
  const [trends, setTrends] = useState<TrendData[]>([])
  const [lastUpdated, setLastUpdated] = useState<string>('')

  // 🔄 自动刷新定时器
  useEffect(() => {
    let refreshInterval: NodeJS.Timeout

    const startAutoRefresh = () => {
      refreshInterval = setInterval(() => {
        refreshData(true)
      }, 30000) // 每30秒刷新一次
    }

    // 初始加载
    loadDashboardData()
    startAutoRefresh()

    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
      }
    }
  }, [])

  /**
   * 📊 加载Dashboard数据
   */
  const loadDashboardData = async () => {
    try {
      setLoading(true)
      
      const [
        statsData,
        resourcesData,
        tasksData,
        actionsData,
        alertsData,
        trendsData
      ] = await Promise.all([
        DashboardService.getStats(),
        DashboardService.getSystemResources(),
        DashboardService.getRecentTasks(8),
        DashboardService.getQuickActions(),
        DashboardService.getSystemAlerts(5),
        DashboardService.getExecutionTrends(7)
      ])

      setStats(statsData)
      setSystemResources(resourcesData)
      setRecentTasks(tasksData)
      setQuickActions(actionsData)
      setSystemAlerts(alertsData)
      setTrends(trendsData)
      setLastUpdated(new Date().toISOString())
      
    } catch (error) {
      console.error('加载Dashboard数据失败:', error)
      addNotification({
        type: 'error',
        title: '加载数据失败',
        message: '请稍后重试'
      })
    } finally {
      setLoading(false)
    }
  }

  /**
   * 🔄 刷新数据
   */
  const refreshData = async (silent: boolean = false) => {
    try {
      if (!silent) {
        setRefreshing(true)
      }
      
      const realtimeData = await DashboardService.getRealtimeStatus()
      
      setStats(realtimeData.stats)
      setSystemResources(realtimeData.resources)
      setSystemAlerts(realtimeData.alerts)
      setLastUpdated(realtimeData.timestamp)
      
      if (!silent) {
        addNotification({
          type: 'success',
          title: '数据已更新'
        })
      }
      
    } catch (error) {
      console.error('刷新数据失败:', error)
      if (!silent) {
        addNotification({
          type: 'error',
          title: '刷新失败',
          message: '请稍后重试'
        })
      }
    } finally {
      if (!silent) {
        setRefreshing(false)
      }
    }
  }

  // 🎨 页面动画配置
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  }

  const cardVariants = {
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

  // 📊 统计卡片配置
  const getStatsCards = () => {
    if (!stats) return []
    
    return [
      {
        title: t('dashboard.totalHosts'),
        value: stats.totalHosts.toString(),
        icon: ServerIcon,
        color: 'text-blue-600',
        bgColor: 'bg-blue-500/20',
        trend: '+2 本周',
        onClick: () => navigate('/inventory')
      },
      {
        title: t('dashboard.totalPlaybooks'),
        value: stats.totalPlaybooks.toString(),
        icon: DocumentTextIcon,
        color: 'text-green-600',
        bgColor: 'bg-green-500/20',
        trend: '+1 本月',
        onClick: () => navigate('/playbooks')
      },
      {
        title: t('dashboard.runningTasks'),
        value: stats.runningTasks.toString(),
        icon: PlayIcon,
        color: 'text-orange-600',
        bgColor: 'bg-orange-500/20',
        trend: stats.runningTasks > 0 ? '活跃' : '空闲',
        onClick: () => navigate('/execution')
      },
      {
        title: t('dashboard.successRate'),
        value: `${stats.successRate}%`,
        icon: CheckCircleIcon,
        color: stats.successRate >= 90 ? 'text-emerald-600' : stats.successRate >= 70 ? 'text-yellow-600' : 'text-red-600',
        bgColor: stats.successRate >= 90 ? 'bg-emerald-500/20' : stats.successRate >= 70 ? 'bg-yellow-500/20' : 'bg-red-500/20',
        trend: '24小时',
        onClick: () => navigate('/history')
      },
    ]
  }

  // 🎨 状态样式和文本处理
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'text-green-600 bg-green-500/20'
      case 'running':
        return 'text-blue-600 bg-blue-500/20 animate-pulse'
      case 'failed':
        return 'text-red-600 bg-red-500/20'
      case 'pending':
        return 'text-yellow-600 bg-yellow-500/20'
      case 'cancelled':
        return 'text-gray-600 bg-gray-500/20'
      default:
        return 'text-gray-600 bg-gray-500/20'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'success':
        return '✅ 成功'
      case 'running':
        return '🔄 运行中'
      case 'failed':
        return '❌ 失败'
      case 'pending':
        return '⏳ 等待中'
      case 'cancelled':
        return '🚫 已取消'
      default:
        return '❓ 未知'
    }
  }

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'critical':
        return '🚨'
      case 'error':
        return '❌'
      case 'warning':
        return '⚠️'
      case 'info':
        return 'ℹ️'
      default:
        return '📢'
    }
  }

  const getAlertColor = (type: string) => {
    switch (type) {
      case 'critical':
        return 'border-red-500/50 bg-red-500/10 text-red-600'
      case 'error':
        return 'border-red-500/50 bg-red-500/10 text-red-600'
      case 'warning':
        return 'border-yellow-500/50 bg-yellow-500/10 text-yellow-600'
      case 'info':
        return 'border-blue-500/50 bg-blue-500/10 text-blue-600'
      default:
        return 'border-gray-500/50 bg-gray-500/10 text-gray-600'
    }
  }

  // 🎯 快速操作处理
  const handleQuickAction = (action: QuickAction) => {
    if (!action.enabled) {
      addNotification({
        type: 'warning',
        title: '此功能暂时不可用'
      })
      return
    }
    
    if (action.action.startsWith('/')) {
      navigate(action.action)
    } else {
      // 处理其他类型的操作
      console.log('执行操作:', action.action)
    }
  }

  // 📊 渲染系统资源圆环图
  const renderResourceCircle = (label: string, percentage: number, color: string) => (
    <div className="text-center">
      <p className="text-glass-text-secondary text-sm mb-2">{label}</p>
      <div className="relative w-20 h-20 mx-auto">
        <svg className="w-20 h-20 transform -rotate-90" viewBox="0 0 36 36">
          <path
            className="text-white/20"
            stroke="currentColor"
            strokeWidth="3"
            fill="none"
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          />
          <path
            className={color}
            stroke="currentColor"
            strokeWidth="3"
            strokeDasharray={`${percentage}, 100`}
            strokeLinecap="round"
            fill="none"
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-lg font-bold text-glass-text-primary">
            {Math.round(percentage)}%
          </span>
        </div>
      </div>
    </div>
  )

  // 🔄 加载状态
  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="glass-container p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-glass-primary mx-auto mb-4"></div>
          <p className="text-glass-text-secondary">正在加载控制台数据...</p>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      className="p-6 space-y-6"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* 🎨 页面标题和刷新按钮 */}
      <motion.div variants={cardVariants} className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-glass-text-primary mb-2">
            {t('dashboard.title')} 🏠
          </h1>
          <p className="glass-text-contrast">
            {t('dashboard.welcome')}
          </p>
          {lastUpdated && (
            <p className="glass-text-contrast-subtle text-xs mt-1">
              最后更新: {formatDate(lastUpdated, { includeTime: true })}
            </p>
          )}
        </div>
        <motion.button
          className="glass-btn-secondary p-3"
          onClick={() => refreshData()}
          disabled={refreshing}
          whileHover={{ rotate: 180 }}
          whileTap={{ rotate: 0 }}
        >
          <ArrowPathIcon className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
        </motion.button>
      </motion.div>

      {/* 🚨 系统警告横幅 */}
      {systemAlerts.length > 0 && (
        <motion.div variants={cardVariants}>
          <div className="glass-container p-4 border-l-4 border-yellow-500">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-semibold text-glass-text-primary flex items-center">
                <ExclamationTriangleIcon className="w-5 h-5 mr-2 text-yellow-500" />
                系统警告 ({systemAlerts.length})
              </h3>
              <button 
                className="text-glass-text-secondary hover:text-glass-text-primary text-sm"
                onClick={() => navigate('/monitoring')}
              >
                查看全部 →
              </button>
            </div>
            <div className="space-y-2">
              {systemAlerts.slice(0, 2).map((alert) => (
                <div key={alert.id} className={`p-3 rounded-glass-sm border ${getAlertColor(alert.type)}`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-medium">
                        {getAlertIcon(alert.type)} {alert.title}
                      </p>
                      <p className="text-sm opacity-80 mt-1">{alert.message}</p>
                    </div>
                    <span className="text-xs opacity-60">
                      {formatDate(alert.timestamp, { includeTime: true, relative: true })}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {/* 📊 统计卡片网格 */}
      <motion.div 
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        variants={cardVariants}
      >
        {getStatsCards().map((stat, index) => (
          <motion.div
            key={stat.title}
            className="glass-container p-6 glass-hover cursor-pointer"
            whileHover={{ y: -4 }}
            whileTap={{ y: 0 }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            onClick={stat.onClick}
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-glass-text-secondary text-sm font-medium">
                  {stat.title}
                </p>
                <p className="text-2xl font-bold text-glass-text-primary mt-1">
                  {stat.value}
                </p>
                <p className="text-xs text-glass-text-secondary mt-1">
                  {stat.trend}
                </p>
              </div>
              <div className={`p-3 rounded-glass ${stat.bgColor}`}>
                <stat.icon className={`w-6 h-6 ${stat.color}`} />
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* 📋 最近任务和快速操作 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 📋 最近任务 */}
        <motion.div 
          className="glass-container p-6"
          variants={cardVariants}
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-glass-text-primary flex items-center">
              <ClockIcon className="w-5 h-5 mr-2" />
              {t('dashboard.recentTasks')} ({recentTasks.length})
            </h2>
            <button 
              className="glass-btn-primary text-sm px-3 py-1"
              onClick={() => navigate('/history')}
            >
              查看全部
            </button>
          </div>
          
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {recentTasks.length > 0 ? recentTasks.map((task, index) => (
              <motion.div
                key={task.id}
                className="flex items-center justify-between p-3 rounded-glass-sm bg-white/10 hover:bg-white/20 transition-all duration-200 cursor-pointer"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                onClick={() => navigate(`/history/${task.id}`)}
              >
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-glass-text-primary truncate">
                    {task.playbook_name}
                  </p>
                  <p className="text-sm text-glass-text-secondary">
                    {formatDate(task.start_time, { includeTime: true, relative: true })} • 
                    {task.user_name} • 
                    {task.inventory_targets.length > 0 ? `${task.inventory_targets.length}台主机` : '无目标'}
                  </p>
                  {task.duration && (
                    <p className="text-xs text-glass-text-secondary">
                      持续时间: {formatDuration(task.duration)}
                    </p>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                    {getStatusText(task.status)}
                  </span>
                  <EyeIcon className="w-4 h-4 text-glass-text-secondary" />
                </div>
              </motion.div>
            )) : (
              <div className="text-center py-8 text-glass-text-secondary">
                <ClockIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>暂无最近任务</p>
              </div>
            )}
          </div>
        </motion.div>

        {/* 🚀 快速操作 */}
        <motion.div 
          className="glass-container p-6"
          variants={cardVariants}
        >
          <h2 className="text-xl font-semibold text-glass-text-primary mb-4 flex items-center">
            <ArrowTrendingUpIcon className="w-5 h-5 mr-2" />
            {t('dashboard.quickActions')}
          </h2>
          
          <div className="grid grid-cols-2 gap-3">
            {quickActions.map((action, index) => (
              <motion.button
                key={action.id}
                className={`p-4 rounded-glass text-center transition-all duration-200 ${action.color} ${!action.enabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                whileHover={action.enabled ? { y: -2 } : {}}
                whileTap={action.enabled ? { y: 0 } : {}}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                onClick={() => handleQuickAction(action)}
                disabled={!action.enabled}
              >
                <div className="w-6 h-6 mx-auto mb-2">
                  {action.icon === 'PlayIcon' && <PlayIcon className="w-6 h-6 text-glass-text-primary" />}
                  {action.icon === 'ServerIcon' && <ServerIcon className="w-6 h-6 text-glass-text-primary" />}
                  {action.icon === 'DocumentTextIcon' && <DocumentTextIcon className="w-6 h-6 text-glass-text-primary" />}
                  {action.icon === 'ChartBarIcon' && <ChartBarIcon className="w-6 h-6 text-glass-text-primary" />}
                </div>
                <p className="text-sm font-medium text-glass-text-primary">
                  {action.title}
                </p>
                <p className="text-xs text-glass-text-secondary mt-1">
                  {action.description}
                </p>
              </motion.button>
            ))}
          </div>
        </motion.div>
      </div>

      {/* 📊 系统资源监控和执行趋势 */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* 🖥️ 系统资源状态 */}
        <motion.div 
          className="glass-container p-6"
          variants={cardVariants}
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-glass-text-primary flex items-center">
              <CpuChipIcon className="w-5 h-5 mr-2" />
              {t('dashboard.systemStatus')} 💻
            </h2>
            <button 
              className="text-glass-text-secondary hover:text-glass-text-primary text-sm"
              onClick={() => navigate('/monitoring')}
            >
              详细监控 →
            </button>
          </div>
          
          {systemResources ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {renderResourceCircle(
                'CPU使用率', 
                systemResources.cpu.usage_percent, 
                systemResources.cpu.usage_percent > 80 ? 'text-red-500' : 
                systemResources.cpu.usage_percent > 60 ? 'text-yellow-500' : 'text-green-500'
              )}
              {renderResourceCircle(
                '内存使用率', 
                systemResources.memory.usage_percent,
                systemResources.memory.usage_percent > 85 ? 'text-red-500' : 
                systemResources.memory.usage_percent > 70 ? 'text-yellow-500' : 'text-blue-500'
              )}
              {renderResourceCircle(
                '磁盘使用率', 
                systemResources.disk.usage_percent,
                systemResources.disk.usage_percent > 90 ? 'text-red-500' : 
                systemResources.disk.usage_percent > 75 ? 'text-yellow-500' : 'text-orange-500'
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-glass-text-secondary">
              <CpuChipIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>正在加载系统资源信息...</p>
            </div>
          )}

          {/* 📊 详细资源信息 */}
          {systemResources && (
            <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-glass-text-secondary">CPU负载:</span>
                  <span className="text-glass-text-primary">
                    {systemResources.cpu.load_average?.join(', ') || 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-glass-text-secondary">内存总量:</span>
                  <span className="text-glass-text-primary">
                    {formatFileSize(systemResources.memory.total_gb * 1024 * 1024 * 1024)}
                  </span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-glass-text-secondary">磁盘总量:</span>
                  <span className="text-glass-text-primary">
                    {formatFileSize(systemResources.disk.total_gb * 1024 * 1024 * 1024)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-glass-text-secondary">可用空间:</span>
                  <span className="text-glass-text-primary">
                    {formatFileSize(systemResources.disk.free_gb * 1024 * 1024 * 1024)}
                  </span>
                </div>
              </div>
            </div>
          )}
        </motion.div>

        {/* 📈 执行趋势图表 */}
        <motion.div 
          className="glass-container p-6"
          variants={cardVariants}
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-glass-text-primary flex items-center">
              <ArrowTrendingUpIcon className="w-5 h-5 mr-2" />
              执行趋势 📈
            </h2>
            <button 
              className="text-glass-text-secondary hover:text-glass-text-primary text-sm"
              onClick={() => navigate('/history')}
            >
              查看历史 →
            </button>
          </div>
          
          {trends.length > 0 ? (
            <div className="space-y-4">
              {/* 简化的趋势图表 */}
              <div className="h-32 flex items-end justify-between space-x-1">
                {trends.map((trend) => (
                  <div key={trend.date} className="flex-1 flex flex-col items-center">
                    <div className="w-full bg-white/10 rounded-t-sm relative overflow-hidden">
                      <div 
                        className="bg-green-500/60 transition-all duration-500 rounded-t-sm"
                        style={{ 
                          height: `${Math.max(trend.success_rate, 5)}%`,
                          minHeight: '4px'
                        }}
                      />
                      {trend.failed_count > 0 && (
                        <div 
                          className="bg-red-500/60 absolute bottom-0 w-full"
                          style={{ 
                            height: `${Math.min((trend.failed_count / trend.total_count) * 100, 20)}%`,
                            minHeight: '2px'
                          }}
                        />
                      )}
                    </div>
                    <span className="text-xs text-glass-text-secondary mt-1">
                      {new Date(trend.date).getDate()}日
                    </span>
                  </div>
                ))}
              </div>
              
              {/* 趋势统计 */}
              <div className="grid grid-cols-3 gap-4 text-center text-sm">
                <div>
                  <p className="text-glass-text-secondary">总执行</p>
                  <p className="text-lg font-bold text-glass-text-primary">
                    {trends.reduce((sum, t) => sum + t.total_count, 0)}
                  </p>
                </div>
                <div>
                  <p className="text-glass-text-secondary">成功率</p>
                  <p className="text-lg font-bold text-green-600">
                    {Math.round(trends.reduce((sum, t) => sum + t.success_rate, 0) / trends.length)}%
                  </p>
                </div>
                <div>
                  <p className="text-glass-text-secondary">失败次数</p>
                  <p className="text-lg font-bold text-red-600">
                    {trends.reduce((sum, t) => sum + t.failed_count, 0)}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-glass-text-secondary">
              <ArrowTrendingUpIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>暂无趋势数据</p>
            </div>
          )}
        </motion.div>
      </div>
    </motion.div>
  )
}

export default Dashboard
