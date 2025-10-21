/**
 * 🚀 任务执行页面
 * 
 * 提供Ansible任务执行的完整界面，包括：
 * - 任务配置表单
 * - 实时执行状态显示
 * - 任务控制按钮
 * - 执行日志查看
 */

import React, { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import {
  PlayIcon,
  StopIcon,
  ClockIcon,
  CogIcon,
  DocumentTextIcon,
  EyeIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'

import GlassCard from '../components/UI/GlassCard'
import GlassButton from '../components/UI/GlassButton'
import GlassInput from '../components/UI/GlassInput'
import { useNotification } from '../contexts/NotificationContext'

import { executionService, ExecutePlaybookRequest, TaskStatus, WebSocketMessage } from '../services/executionService'
import PlaybookService from '../services/playbookService'
import { inventoryService, Host } from '../services/inventoryService'

interface PlaybookOption {
  value: string
  label: string
}

interface HostOption {
  value: string
  label: string
  group?: string
}

/**
 * 🚀 任务执行页面组件
 */
export const Execution: React.FC = () => {
  const { addNotification } = useNotification()
  const showNotification = (message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info') => {
    addNotification({ 
      title: type === 'success' ? '成功' : type === 'error' ? '错误' : type === 'warning' ? '警告' : '信息',
      message, 
      type 
    })
  }

  // 📋 状态管理
  const [playbooks, setPlaybooks] = useState<PlaybookOption[]>([])
  const [hosts, setHosts] = useState<HostOption[]>([])
  const [loading, setLoading] = useState(false)
  const [executing, setExecuting] = useState(false)

  // 🎯 表单状态
  const [selectedPlaybook, setSelectedPlaybook] = useState('')
  const [selectedHosts, setSelectedHosts] = useState<string[]>([])
  const [executionOptions, setExecutionOptions] = useState({
    forks: 5,
    verbose: 0,
    check: false,
    diff: false,
    become: false,
    timeout: 30,
    extra_vars: ''
  })

  // 📊 任务状态
  const [currentTask, setCurrentTask] = useState<TaskStatus | null>(null)
  const [taskLogs, setTaskLogs] = useState<string[]>([])
  const [showLogs, setShowLogs] = useState(false)

  // 🔗 WebSocket连接
  const wsRef = useRef<WebSocket | null>(null)
  const logsEndRef = useRef<HTMLDivElement>(null)

  /**
   * 🔄 初始化数据
   */
  useEffect(() => {
    loadInitialData()
  }, [])

  /**
   * 📜 自动滚动到日志底部
   */
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [taskLogs])

  /**
   * 🧹 清理WebSocket连接
   */
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [])

  /**
   * 🔄 加载初始数据
   */
  const loadInitialData = async () => {
    setLoading(true)
    try {
      // 并行加载Playbook和主机列表
      const [playbooksData, hostsData] = await Promise.all([
        PlaybookService.getPlaybooks(),
        inventoryService.getHosts({ page_size: 1000, active_only: true })
      ])

      // 转换Playbook数据
      const playbookOptions = (playbooksData.items || [])
        .map((pb) => ({
          value: pb.filename,
          label: `📄 ${pb.display_name || pb.filename}`
        }))
      setPlaybooks(playbookOptions)

      // 转换主机数据
      const hostOptions = (hostsData.hosts || []).map((host: Host) => ({
        value: host.hostname,
        label: `🖥️ ${(host.display_name || host.hostname)} (${host.ansible_host || '未配置地址'})`,
        group: host.group_name
      }))
      setHosts(hostOptions)

    } catch (error) {
      console.error('加载初始数据失败:', error)
      showNotification('加载数据失败，请刷新页面重试', 'error')
    } finally {
      setLoading(false)
    }
  }

  /**
   * 🚀 执行Playbook
   */
  const handleExecutePlaybook = async () => {
    if (!selectedPlaybook) {
      showNotification('请选择要执行的Playbook', 'warning')
      return
    }

    if (selectedHosts.length === 0) {
      showNotification('请选择目标主机', 'warning')
      return
    }

    setExecuting(true)
    setTaskLogs([])
    setShowLogs(true)

    try {
      // 准备执行参数
      const request: ExecutePlaybookRequest = {
        playbook_name: selectedPlaybook,
        inventory_targets: selectedHosts,
        execution_options: {
          forks: executionOptions.forks,
          verbose: executionOptions.verbose,
          check: executionOptions.check,
          diff: executionOptions.diff,
          become: executionOptions.become,
          timeout: executionOptions.timeout,
          extra_vars: executionOptions.extra_vars ? JSON.parse(executionOptions.extra_vars) : undefined
        }
      }

      // 启动任务
      const taskStatus = await executionService.executePlaybook(request)
      setCurrentTask(taskStatus)

      // 建立WebSocket连接
      setupWebSocketConnection(taskStatus.task_id)

      showNotification(`任务已启动: ${taskStatus.task_name}`, 'success')

    } catch (error: any) {
      console.error('执行Playbook失败:', error)
      showNotification(error.message || '执行失败，请检查配置', 'error')
      setExecuting(false)
    }
  }

  /**
   * 🔗 建立WebSocket连接
   */
  const setupWebSocketConnection = (taskId: string) => {
    if (!taskId) {
      console.warn('⚠️ taskId为空，无法建立WebSocket连接')
      return
    }

    console.log('🔗 准备建立WebSocket连接，taskId:', taskId)

    // 关闭已存在的连接
    if (wsRef.current) {
      console.log('🔌 关闭现有WebSocket连接')
      wsRef.current.close()
      wsRef.current = null
    }

    try {
      // 建立新的连接
      console.log('🚀 开始建立WebSocket连接...')
      wsRef.current = executionService.createWebSocketConnection(
        taskId,
        handleWebSocketMessage,
        handleWebSocketError,
        handleWebSocketClose
      )
      console.log('✅ WebSocket连接对象已创建')
    } catch (error) {
      console.error('❌ 建立WebSocket连接失败:', error)
      wsRef.current = null
      setExecuting(false)
      const message = error instanceof Error ? error.message : '实时日志连接建立失败，请重新登录后重试'
      showNotification(message, 'error')
    }
  }

  /**
   * 📨 处理WebSocket消息
   */
  const handleWebSocketMessage = (message: WebSocketMessage) => {
    switch (message.type) {
      case 'log':
        setTaskLogs(prev => [...prev, message.data.message])
        break
      
      case 'status':
        setCurrentTask(prev => prev ? {
          ...prev,
          status: message.data.status,
          progress: message.data.progress,
          current_step: message.data.current_step
        } : null)
        
        // 任务完成时停止执行状态
        if (['SUCCESS', 'FAILURE', 'REVOKED'].includes(message.data.status)) {
          setExecuting(false)
        }
        break
      
      case 'connected':
        console.log('WebSocket连接成功')
        break
      
      case 'pong':
        // 心跳响应，无需处理
        break
    }
  }

  /**
   * ❌ 处理WebSocket错误
   */
  const handleWebSocketError = (error: Event) => {
    console.error('WebSocket连接错误:', error)
    showNotification('实时日志连接中断', 'warning')
  }

  /**
   * 🔌 处理WebSocket关闭
   */
  const handleWebSocketClose = (event: CloseEvent) => {
    console.log('WebSocket连接关闭:', event.code, event.reason)
    wsRef.current = null

    if (event.code === 4401 || event.code === 4403) {
      showNotification('实时日志连接已失效，请重新登录', 'error')
      setExecuting(false)
      return
    }

    // 如果是异常关闭且仍在执行中，则尝试重连
    if (event.code !== 1000 && executing && currentTask) {
      setTimeout(() => {
        setupWebSocketConnection(currentTask.task_id)
      }, 3000)
    }
  }

  /**
   * 🛑 取消任务
   */
  const handleCancelTask = async () => {
    if (!currentTask) return

    try {
      const result = await executionService.cancelTask(currentTask.task_id)
      
      if (result.success) {
        showNotification('任务已取消', 'success')
        setExecuting(false)
        
        // 关闭WebSocket连接
        if (wsRef.current) {
          wsRef.current.close()
          wsRef.current = null
        }
      } else {
        showNotification(result.message, 'warning')
      }
    } catch (error: any) {
      console.error('取消任务失败:', error)
      showNotification(error.message || '取消任务失败', 'error')
    }
  }

  /**
   * 🎨 渲染任务状态卡片
   */
  const renderTaskStatusCard = () => {
    if (!currentTask) return null

    const statusIcon = executionService.getStatusIcon(currentTask.status)
    const statusColor = executionService.getStatusColor(currentTask.status)
    const statusText = executionService.formatTaskStatus(currentTask.status)

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <GlassCard className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">{statusIcon}</span>
              <div>
                <h3 className="text-lg font-semibold text-gray-800">
                  {currentTask.task_name}
                </h3>
                <p className={`text-sm font-medium ${statusColor}`}>
                  {statusText}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {executing && (
                <GlassButton
                  variant="danger"
                  size="sm"
                  onClick={handleCancelTask}
                  className="flex items-center space-x-1"
                >
                  <StopIcon className="w-4 h-4" />
                  <span>取消</span>
                </GlassButton>
              )}
              
              <GlassButton
                variant="secondary"
                size="sm"
                onClick={() => setShowLogs(!showLogs)}
                className="flex items-center space-x-1"
              >
                <EyeIcon className="w-4 h-4" />
                <span>{showLogs ? '隐藏日志' : '查看日志'}</span>
              </GlassButton>
            </div>
          </div>

          {/* 进度条 */}
          <div className="mb-4">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>执行进度</span>
              <span>{currentTask.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <motion.div
                className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${currentTask.progress}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>

          {/* 当前步骤 */}
          {currentTask.current_step && (
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-1">当前步骤</p>
              <p className="text-gray-800">{currentTask.current_step}</p>
            </div>
          )}

          {/* 时间信息 */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-600">开始时间</p>
              <p className="text-gray-800">
                {currentTask.start_time ? new Date(currentTask.start_time).toLocaleString('zh-CN') : '--'}
              </p>
            </div>
            <div>
              <p className="text-gray-600">执行时长</p>
              <p className="text-gray-800">
                {executionService.formatDuration(currentTask.duration)}
              </p>
            </div>
          </div>

          {/* 错误信息 */}
          {currentTask.error_message && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800">{currentTask.error_message}</p>
            </div>
          )}
        </GlassCard>
      </motion.div>
    )
  }

  /**
   * 📜 渲染日志面板
   */
  const renderLogsPanel = () => {
    if (!showLogs) return null

    return (
      <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{ opacity: 1, height: 'auto' }}
        exit={{ opacity: 0, height: 0 }}
        className="mb-6"
      >
        <GlassCard className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-lg font-semibold text-gray-800 flex items-center space-x-2">
              <DocumentTextIcon className="w-5 h-5" />
              <span>执行日志</span>
            </h4>
            <GlassButton
              variant="ghost"
              size="sm"
              onClick={() => setShowLogs(false)}
            >
              <XMarkIcon className="w-4 h-4" />
            </GlassButton>
          </div>
          
          <div className="bg-gray-900 rounded-lg p-4 h-64 overflow-y-auto font-mono text-sm">
            {taskLogs.length === 0 ? (
              <p className="text-gray-400">等待日志输出...</p>
            ) : (
              taskLogs.map((log, index) => (
                <div key={index} className="text-green-400 mb-1">
                  {log}
                </div>
              ))
            )}
            <div ref={logsEndRef} />
          </div>
        </GlassCard>
      </motion.div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-3">
            <PlayIcon className="w-8 h-8 text-blue-600" />
            <span>任务执行</span>
          </h1>
          <p className="text-gray-600 mt-1">配置并执行Ansible Playbook任务</p>
        </div>
      </div>

      {/* 任务状态卡片 */}
      {renderTaskStatusCard()}

      {/* 日志面板 */}
      {renderLogsPanel()}

      {/* 配置表单 */}
      <GlassCard className="p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-6 flex items-center space-x-2">
          <CogIcon className="w-6 h-6" />
          <span>任务配置</span>
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Playbook选择 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              📄 选择Playbook
            </label>
            <select
              value={selectedPlaybook}
              onChange={(e) => setSelectedPlaybook(e.target.value)}
              disabled={executing}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/80 backdrop-blur-sm"
            >
              <option value="">请选择要执行的Playbook</option>
              {playbooks.map(pb => (
                <option key={pb.value} value={pb.value}>{pb.label}</option>
              ))}
            </select>
          </div>

          {/* 目标主机选择 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              🖥️ 目标主机
            </label>
            <select
              multiple
              value={selectedHosts}
              onChange={(e) => {
                const values = Array.from(e.target.selectedOptions, option => option.value)
                setSelectedHosts(values)
              }}
              disabled={executing}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/80 backdrop-blur-sm h-32"
            >
              {hosts.map((host, index) => (
                <option key={`${host.value}-${index}`} value={host.value}>{host.label}</option>
              ))}
            </select>
          </div>

          {/* 并发数 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ⚡ 并发执行数
            </label>
            <GlassInput
              type="number"
              value={executionOptions.forks}
              onChange={(e) => setExecutionOptions(prev => ({
                ...prev,
                forks: parseInt(e.target.value) || 5
              }))}
              min={1}
              max={50}
              disabled={executing}
            />
          </div>

          {/* 详细级别 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              📊 详细输出级别
            </label>
            <select
              value={executionOptions.verbose}
              onChange={(e) => setExecutionOptions(prev => ({
                ...prev,
                verbose: parseInt(e.target.value)
              }))}
              disabled={executing}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/80 backdrop-blur-sm"
            >
              <option value={0}>0 - 基本输出</option>
              <option value={1}>1 - 详细输出</option>
              <option value={2}>2 - 更详细输出</option>
              <option value={3}>3 - 调试输出</option>
              <option value={4}>4 - 完整调试</option>
            </select>
          </div>

          {/* 超时时间 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ⏱️ 连接超时(秒)
            </label>
            <GlassInput
              type="number"
              value={executionOptions.timeout}
              onChange={(e) => setExecutionOptions(prev => ({
                ...prev,
                timeout: parseInt(e.target.value) || 30
              }))}
              min={5}
              max={300}
              disabled={executing}
            />
          </div>

          {/* 额外变量 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              🔧 额外变量 (JSON格式)
            </label>
            <GlassInput
              value={executionOptions.extra_vars}
              onChange={(e) => setExecutionOptions(prev => ({
                ...prev,
                extra_vars: e.target.value
              }))}
              placeholder='{"key": "value"}'
              disabled={executing}
            />
          </div>
        </div>

        {/* 选项开关 */}
        <div className="mt-6 grid grid-cols-2 lg:grid-cols-4 gap-4">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={executionOptions.check}
              onChange={(e) => setExecutionOptions(prev => ({
                ...prev,
                check: e.target.checked
              }))}
              disabled={executing}
              className="rounded border-gray-300"
            />
            <span className="text-sm text-gray-700">🔍 检查模式</span>
          </label>

          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={executionOptions.diff}
              onChange={(e) => setExecutionOptions(prev => ({
                ...prev,
                diff: e.target.checked
              }))}
              disabled={executing}
              className="rounded border-gray-300"
            />
            <span className="text-sm text-gray-700">📋 显示差异</span>
          </label>

          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={executionOptions.become}
              onChange={(e) => setExecutionOptions(prev => ({
                ...prev,
                become: e.target.checked
              }))}
              disabled={executing}
              className="rounded border-gray-300"
            />
            <span className="text-sm text-gray-700">🔐 使用sudo</span>
          </label>
        </div>

        {/* 执行按钮 */}
        <div className="mt-8 flex justify-center">
          <GlassButton
            variant="primary"
            size="lg"
            onClick={handleExecutePlaybook}
            disabled={executing || loading || !selectedPlaybook || selectedHosts.length === 0}
            className="flex items-center space-x-2 px-8"
          >
            {executing ? (
              <>
                <ClockIcon className="w-5 h-5 animate-spin" />
                <span>执行中...</span>
              </>
            ) : (
              <>
                <PlayIcon className="w-5 h-5" />
                <span>开始执行</span>
              </>
            )}
          </GlassButton>
        </div>
      </GlassCard>
    </div>
  )
}

export default Execution
