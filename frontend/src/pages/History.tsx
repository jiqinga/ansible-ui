/**
 * 📋 执行历史页面
 * 
 * 提供任务执行历史记录的查看和管理功能，包括：
 * - 历史任务列表
 * - 任务详情查看
 * - 筛选和搜索
 * - 分页浏览
 */

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  ClockIcon,
  EyeIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  PlayIcon
} from '@heroicons/react/24/outline'

import GlassCard from '../components/UI/GlassCard'
import GlassButton from '../components/UI/GlassButton'
import GlassInput from '../components/UI/GlassInput'
import GlassModal from '../components/UI/GlassModal'
import { useNotification } from '../contexts/NotificationContext'

import { executionService, TaskStatus } from '../services/executionService'

/**
 * 📋 执行历史页面组件
 */
export const History: React.FC = () => {
  const { addNotification } = useNotification()
  const showNotification = (message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info') => {
    addNotification({ 
      title: type === 'success' ? '成功' : type === 'error' ? '错误' : type === 'warning' ? '警告' : '信息',
      message, 
      type 
    })
  }

  const formatDateTime = (date: string) => new Date(date).toLocaleString('zh-CN')

  // 📋 状态管理
  const [tasks, setTasks] = useState<TaskStatus[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedTask, setSelectedTask] = useState<TaskStatus | null>(null)
  const [showTaskDetail, setShowTaskDetail] = useState(false)

  // 🔍 筛选和搜索
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const pageSize = 20

  /**
   * 🔄 初始化数据
   */
  useEffect(() => {
    loadTasks()
  }, [currentPage, statusFilter])

  /**
   * 📋 加载任务列表
   */
  const loadTasks = async () => {
    setLoading(true)
    try {
      const response = await executionService.getTaskList(
        statusFilter || undefined,
        currentPage,
        pageSize
      )
      
      setTasks(response.tasks)
      setTotalCount(response.total_count)
    } catch (error: any) {
      console.error('加载任务列表失败:', error)
      showNotification(error.message || '加载任务列表失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  /**
   * 🔍 搜索过滤
   */
  const filteredTasks = tasks.filter(task =>
    task.task_name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  /**
   * 👁️ 查看任务详情
   */
  const handleViewTask = (task: TaskStatus) => {
    setSelectedTask(task)
    setShowTaskDetail(true)
  }

  /**
   * 🎨 获取状态图标
   */
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return <CheckCircleIcon className="w-5 h-5 text-green-600" />
      case 'FAILURE':
        return <XCircleIcon className="w-5 h-5 text-red-600" />
      case 'PENDING':
        return <ClockIcon className="w-5 h-5 text-yellow-600" />
      case 'STARTED':
        return <PlayIcon className="w-5 h-5 text-blue-600" />
      default:
        return <ExclamationTriangleIcon className="w-5 h-5 text-gray-600" />
    }
  }

  /**
   * 🎨 获取状态颜色
   */
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return 'text-green-600 bg-green-50 border-green-200'
      case 'FAILURE':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'PENDING':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'STARTED':
        return 'text-blue-600 bg-blue-50 border-blue-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  /**
   * 📄 分页控制
   */
  const totalPages = Math.ceil(totalCount / pageSize)
  const canGoPrevious = currentPage > 1
  const canGoNext = currentPage < totalPages

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-3">
            <ClockIcon className="w-8 h-8 text-indigo-600" />
            <span>执行历史</span>
          </h1>
          <p className="text-gray-600 mt-1">查看和管理任务执行历史记录</p>
        </div>
      </div>

      {/* 搜索和筛选 */}
      <GlassCard className="p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0 lg:space-x-4">
          {/* 搜索框 */}
          <div className="flex-1 max-w-md">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <GlassInput
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="搜索任务名称..."
                className="pl-10"
              />
            </div>
          </div>

          {/* 状态筛选 */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <FunnelIcon className="w-5 h-5 text-gray-500" />
              <span className="text-sm text-gray-700">状态筛选:</span>
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-40 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/80 backdrop-blur-sm"
            >
              <option value="">全部状态</option>
              <option value="SUCCESS">✅ 成功</option>
              <option value="FAILURE">❌ 失败</option>
              <option value="PENDING">⏳ 等待中</option>
              <option value="STARTED">🚀 执行中</option>
              <option value="REVOKED">🛑 已取消</option>
            </select>
          </div>
        </div>
      </GlassCard>

      {/* 任务列表 */}
      <GlassCard className="overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600">正在加载任务历史...</p>
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="p-8 text-center">
            <ClockIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">暂无任务历史记录</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {filteredTasks.map((task, index) => (
              <motion.div
                key={task.task_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="p-6 hover:bg-white/50 transition-colors duration-200"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      {getStatusIcon(task.status)}
                      <h3 className="text-lg font-semibold text-gray-800">
                        {task.task_name}
                      </h3>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(task.status)}`}>
                        {executionService.formatTaskStatus(task.status)}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm text-gray-600">
                      <div>
                        <span className="font-medium">任务ID:</span>
                        <span className="ml-1 font-mono">{task.task_id.slice(0, 8)}...</span>
                      </div>
                      <div>
                        <span className="font-medium">开始时间:</span>
                        <span className="ml-1">
                          {task.start_time ? formatDateTime(task.start_time) : '--'}
                        </span>
                      </div>
                      <div>
                        <span className="font-medium">执行时长:</span>
                        <span className="ml-1">
                          {executionService.formatDuration(task.duration)}
                        </span>
                      </div>
                      <div>
                        <span className="font-medium">进度:</span>
                        <span className="ml-1">{task.progress}%</span>
                      </div>
                    </div>

                    {task.current_step && (
                      <div className="mt-2 text-sm text-gray-600">
                        <span className="font-medium">当前步骤:</span>
                        <span className="ml-1">{task.current_step}</span>
                      </div>
                    )}

                    {task.error_message && (
                      <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-800">
                        {task.error_message}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    <GlassButton
                      variant="secondary"
                      size="sm"
                      onClick={() => handleViewTask(task)}
                      className="flex items-center space-x-1"
                    >
                      <EyeIcon className="w-4 h-4" />
                      <span>查看详情</span>
                    </GlassButton>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {/* 分页控制 */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
            <div className="text-sm text-gray-600">
              显示 {(currentPage - 1) * pageSize + 1} - {Math.min(currentPage * pageSize, totalCount)} 条，
              共 {totalCount} 条记录
            </div>
            
            <div className="flex items-center space-x-2">
              <GlassButton
                variant="secondary"
                size="sm"
                onClick={() => setCurrentPage(prev => prev - 1)}
                disabled={!canGoPrevious}
              >
                上一页
              </GlassButton>
              
              <span className="text-sm text-gray-600">
                第 {currentPage} 页，共 {totalPages} 页
              </span>
              
              <GlassButton
                variant="secondary"
                size="sm"
                onClick={() => setCurrentPage(prev => prev + 1)}
                disabled={!canGoNext}
              >
                下一页
              </GlassButton>
            </div>
          </div>
        )}
      </GlassCard>

      {/* 任务详情弹窗 */}
      <GlassModal
        isOpen={showTaskDetail}
        onClose={() => setShowTaskDetail(false)}
        title="📋 任务详情"
        size="lg"
      >
        {selectedTask && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">任务ID</p>
                <p className="font-mono text-sm">{selectedTask.task_id}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">状态</p>
                <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(selectedTask.status)}`}>
                  {executionService.formatTaskStatus(selectedTask.status)}
                </span>
              </div>
              <div>
                <p className="text-sm text-gray-600">开始时间</p>
                <p className="text-sm">{selectedTask.start_time ? formatDateTime(selectedTask.start_time) : '--'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">执行时长</p>
                <p className="text-sm">{executionService.formatDuration(selectedTask.duration)}</p>
              </div>
            </div>
            
            {selectedTask.error_message && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm font-medium text-red-800 mb-1">错误信息</p>
                <p className="text-sm text-red-700">{selectedTask.error_message}</p>
              </div>
            )}
          </div>
        )}
      </GlassModal>
    </div>
  )
}

export default History
