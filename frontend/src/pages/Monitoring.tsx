/**
 * 📊 系统监控页面
 * 
 * 提供系统监控和性能分析功能，包括：
 * - 系统健康状态
 * - 资源使用监控
 * - 性能报告和趋势
 * - 任务统计分析
 */

import React, { useState, useEffect } from 'react'
// import { motion } from 'framer-motion'
import {
  ServerIcon,
  CpuChipIcon,
  ExclamationCircleIcon,
  ArrowTrendingUpIcon,
  CalendarDaysIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline'

import GlassCard from '../components/UI/GlassCard'
import GlassButton from '../components/UI/GlassButton'
import GlassChart from '../components/UI/GlassChart'
import { useNotification } from '../contexts/NotificationContext'

import { monitoringService, PerformanceReport, HealthStatus, SystemResources } from '../services/monitoringService'

/**
 * 📊 系统监控页面组件
 */
export const Monitoring: React.FC = () => {
  const { addNotification } = useNotification()
  const showNotification = (message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info') => {
    addNotification({ 
      title: type === 'success' ? '成功' : type === 'error' ? '错误' : type === 'warning' ? '警告' : '信息',
      message, 
      type 
    })
  }

  const formatDateTime = (date: string) => new Date(date).toLocaleString('zh-CN')

  // 📊 监控数据状态
  const [performanceReport, setPerformanceReport] = useState<PerformanceReport | null>(null)
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null)
  const [systemResources, setSystemResources] = useState<SystemResources | null>(null)
  const [loading, setLoading] = useState(false)
  const [reportDays, setReportDays] = useState(7)

  /**
   * 🔄 初始化数据
   */
  useEffect(() => {
    loadMonitoringData()
  }, [reportDays])

  /**
   * 📊 加载监控数据
   */
  const loadMonitoringData = async () => {
    setLoading(true)
    try {
      // 并行加载监控数据
      const [reportData, healthData, resourcesData] = await Promise.all([
        monitoringService.getPerformanceReport(reportDays),
        monitoringService.getHealthStatus(),
        monitoringService.getSystemResources()
      ])
      
      setPerformanceReport(reportData)
      setHealthStatus(healthData)
      setSystemResources(resourcesData)
    } catch (error: any) {
      console.error('加载监控数据失败:', error)
      showNotification(error.message || '加载监控数据失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-3">
            <ServerIcon className="w-8 h-8 text-purple-600" />
            <span>系统监控</span>
          </h1>
          <p className="text-gray-600 mt-1">查看系统健康状态和性能监控数据</p>
        </div>
      </div>

      {/* 监控控制面板 */}
      <GlassCard className="p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0 lg:space-x-4">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <CalendarDaysIcon className="w-5 h-5 text-gray-500" />
              <span className="text-sm text-gray-700">报告周期:</span>
            </div>
            <select
              value={reportDays}
              onChange={(e) => setReportDays(Number(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/80 backdrop-blur-sm"
            >
              <option value={1}>最近1天</option>
              <option value={3}>最近3天</option>
              <option value={7}>最近7天</option>
              <option value={14}>最近14天</option>
              <option value={30}>最近30天</option>
            </select>
          </div>
          
          <GlassButton
            onClick={loadMonitoringData}
            disabled={loading}
            className="flex items-center space-x-2"
          >
            <ArrowTrendingUpIcon className="w-4 h-4" />
            <span>{loading ? '刷新中...' : '刷新数据'}</span>
          </GlassButton>
        </div>
      </GlassCard>

      {loading ? (
        <GlassCard className="p-8">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600">正在加载监控数据...</p>
          </div>
        </GlassCard>
      ) : (
        <>
          {/* 系统健康状态 */}
          {healthStatus && (
            <GlassCard className="p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center space-x-2">
                <ExclamationCircleIcon className="w-5 h-5" />
                <span>系统健康状态</span>
              </h3>
              
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* 总体状态 */}
                <div className="text-center">
                  <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium border ${monitoringService.getHealthStatusColor(healthStatus.overall_status)}`}>
                    {monitoringService.formatHealthStatus(healthStatus.overall_status)}
                  </div>
                  <p className="text-xs text-gray-600 mt-2">总体状态</p>
                </div>
                
                {/* 警告数量 */}
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-600">
                    {healthStatus.warnings.length}
                  </div>
                  <p className="text-xs text-gray-600">警告</p>
                </div>
                
                {/* 错误数量 */}
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {healthStatus.errors.length}
                  </div>
                  <p className="text-xs text-gray-600">错误</p>
                </div>
              </div>

              {/* 最近警告 */}
              {(healthStatus.warnings.length > 0 || healthStatus.errors.length > 0) && (
                <div className="mt-6">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">最近警告</h4>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {[...healthStatus.errors, ...healthStatus.warnings].slice(0, 5).map((alert, index) => (
                      <div
                        key={index}
                        className={`p-3 rounded-lg border text-sm ${monitoringService.getAlertSeverityColor(alert.severity)}`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{alert.message}</span>
                          <span className="text-xs opacity-75">
                            {monitoringService.formatAlertSeverity(alert.severity)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </GlassCard>
          )}

          {/* 系统资源监控 */}
          {systemResources && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* CPU使用率 */}
              <GlassCard className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-800 flex items-center space-x-2">
                    <CpuChipIcon className="w-5 h-5" />
                    <span>CPU使用率</span>
                  </h3>
                  <span className="text-2xl font-bold text-blue-600">
                    {monitoringService.formatPercentage(systemResources.cpu.usage_percent)}
                  </span>
                </div>
                
                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex justify-between">
                    <span>核心数:</span>
                    <span>{systemResources.cpu.count}</span>
                  </div>
                  {systemResources.cpu.frequency_mhz && (
                    <div className="flex justify-between">
                      <span>频率:</span>
                      <span>{systemResources.cpu.frequency_mhz.toFixed(0)} MHz</span>
                    </div>
                  )}
                  {systemResources.cpu.load_average && (
                    <div className="flex justify-between">
                      <span>负载:</span>
                      <span>{systemResources.cpu.load_average.map(l => l.toFixed(2)).join(', ')}</span>
                    </div>
                  )}
                </div>
                
                {/* CPU使用率进度条 */}
                <div className="mt-4">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${systemResources.cpu.usage_percent}%` }}
                    />
                  </div>
                </div>
              </GlassCard>

              {/* 内存使用率 */}
              <GlassCard className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-800 flex items-center space-x-2">
                    <ServerIcon className="w-5 h-5" />
                    <span>内存使用率</span>
                  </h3>
                  <span className="text-2xl font-bold text-green-600">
                    {monitoringService.formatPercentage(systemResources.memory.usage_percent)}
                  </span>
                </div>
                
                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex justify-between">
                    <span>总内存:</span>
                    <span>{systemResources.memory.total_gb.toFixed(1)} GB</span>
                  </div>
                  <div className="flex justify-between">
                    <span>已使用:</span>
                    <span>{systemResources.memory.used_gb.toFixed(1)} GB</span>
                  </div>
                  <div className="flex justify-between">
                    <span>可用:</span>
                    <span>{systemResources.memory.available_gb.toFixed(1)} GB</span>
                  </div>
                </div>
                
                {/* 内存使用率进度条 */}
                <div className="mt-4">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${systemResources.memory.usage_percent}%` }}
                    />
                  </div>
                </div>
              </GlassCard>

              {/* 磁盘使用率 */}
              <GlassCard className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-800 flex items-center space-x-2">
                    <DocumentTextIcon className="w-5 h-5" />
                    <span>磁盘使用率</span>
                  </h3>
                  <span className="text-2xl font-bold text-purple-600">
                    {monitoringService.formatPercentage(systemResources.disk.usage_percent)}
                  </span>
                </div>
                
                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex justify-between">
                    <span>总容量:</span>
                    <span>{systemResources.disk.total_gb.toFixed(1)} GB</span>
                  </div>
                  <div className="flex justify-between">
                    <span>已使用:</span>
                    <span>{systemResources.disk.used_gb.toFixed(1)} GB</span>
                  </div>
                  <div className="flex justify-between">
                    <span>可用:</span>
                    <span>{systemResources.disk.free_gb.toFixed(1)} GB</span>
                  </div>
                </div>
                
                {/* 磁盘使用率进度条 */}
                <div className="mt-4">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${systemResources.disk.usage_percent}%` }}
                    />
                  </div>
                </div>
              </GlassCard>
            </div>
          )}

          {/* 💾 磁盘分区详细信息 */}
          {systemResources?.disk_partitions && systemResources.disk_partitions.length > 0 && (
            <GlassCard className="p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center space-x-2">
                <DocumentTextIcon className="w-5 h-5" />
                <span>💾 磁盘分区详情</span>
              </h3>
              
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-2 font-medium text-gray-700">挂载点</th>
                      <th className="text-left py-3 px-2 font-medium text-gray-700">设备</th>
                      <th className="text-left py-3 px-2 font-medium text-gray-700">文件系统</th>
                      <th className="text-right py-3 px-2 font-medium text-gray-700">总容量</th>
                      <th className="text-right py-3 px-2 font-medium text-gray-700">已使用</th>
                      <th className="text-right py-3 px-2 font-medium text-gray-700">可用</th>
                      <th className="text-right py-3 px-2 font-medium text-gray-700">使用率</th>
                      <th className="text-left py-3 px-2 font-medium text-gray-700">进度</th>
                    </tr>
                  </thead>
                  <tbody>
                    {systemResources.disk_partitions.map((partition, index) => (
                      <tr key={index} className="border-b border-gray-100 hover:bg-white/50 transition-colors">
                        <td className="py-3 px-2 font-mono text-xs">{partition.mountpoint}</td>
                        <td className="py-3 px-2 font-mono text-xs text-gray-600">{partition.device}</td>
                        <td className="py-3 px-2">
                          <span className="inline-flex items-center px-2 py-1 rounded-md bg-blue-50 text-blue-700 text-xs font-medium">
                            {partition.fstype || 'unknown'}
                          </span>
                        </td>
                        <td className="py-3 px-2 text-right text-gray-700">{partition.total_gb.toFixed(1)} GB</td>
                        <td className="py-3 px-2 text-right text-gray-700">{partition.used_gb.toFixed(1)} GB</td>
                        <td className="py-3 px-2 text-right text-gray-700">{partition.free_gb.toFixed(1)} GB</td>
                        <td className="py-3 px-2 text-right">
                          <span className={`font-semibold ${
                            partition.usage_percent > 90 ? 'text-red-600' :
                            partition.usage_percent > 80 ? 'text-yellow-600' :
                            'text-green-600'
                          }`}>
                            {partition.usage_percent.toFixed(1)}%
                          </span>
                        </td>
                        <td className="py-3 px-2">
                          <div className="w-24 bg-gray-200 rounded-full h-2">
                            <div 
                              className={`h-2 rounded-full transition-all duration-300 ${
                                partition.usage_percent > 90 ? 'bg-red-600' :
                                partition.usage_percent > 80 ? 'bg-yellow-600' :
                                'bg-green-600'
                              }`}
                              style={{ width: `${partition.usage_percent}%` }}
                            />
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </GlassCard>
          )}

          {/* 🌐 网络接口详细信息 */}
          {systemResources?.network_interfaces && systemResources.network_interfaces.length > 0 && (
            <GlassCard className="p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center space-x-2">
                <ServerIcon className="w-5 h-5" />
                <span>🌐 网络接口详情</span>
              </h3>
              
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-2 font-medium text-gray-700">接口名</th>
                      <th className="text-center py-3 px-2 font-medium text-gray-700">状态</th>
                      <th className="text-left py-3 px-2 font-medium text-gray-700">IPv4地址</th>
                      <th className="text-left py-3 px-2 font-medium text-gray-700">MAC地址</th>
                      <th className="text-right py-3 px-2 font-medium text-gray-700">速度</th>
                      <th className="text-right py-3 px-2 font-medium text-gray-700">发送</th>
                      <th className="text-right py-3 px-2 font-medium text-gray-700">接收</th>
                      <th className="text-right py-3 px-2 font-medium text-gray-700">错误</th>
                    </tr>
                  </thead>
                  <tbody>
                    {systemResources.network_interfaces.map((iface, index) => (
                      <tr key={index} className="border-b border-gray-100 hover:bg-white/50 transition-colors">
                        <td className="py-3 px-2 font-medium text-gray-800">{iface.name}</td>
                        <td className="py-3 px-2 text-center">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            iface.status === 'up' 
                              ? 'bg-green-50 text-green-700 border border-green-200' 
                              : 'bg-gray-50 text-gray-600 border border-gray-200'
                          }`}>
                            {iface.status === 'up' ? '🟢 UP' : '⚫ DOWN'}
                          </span>
                        </td>
                        <td className="py-3 px-2 font-mono text-xs text-gray-700">
                          {iface.ipv4 || <span className="text-gray-400">N/A</span>}
                        </td>
                        <td className="py-3 px-2 font-mono text-xs text-gray-600">
                          {iface.mac || <span className="text-gray-400">N/A</span>}
                        </td>
                        <td className="py-3 px-2 text-right text-gray-700">
                          {iface.speed_mbps ? `${iface.speed_mbps} Mbps` : <span className="text-gray-400">N/A</span>}
                        </td>
                        <td className="py-3 px-2 text-right text-gray-700">
                          {monitoringService.formatBytes(iface.bytes_sent)}
                        </td>
                        <td className="py-3 px-2 text-right text-gray-700">
                          {monitoringService.formatBytes(iface.bytes_recv)}
                        </td>
                        <td className="py-3 px-2 text-right">
                          {iface.errors_in + iface.errors_out > 0 ? (
                            <span className="text-red-600 font-semibold">
                              {iface.errors_in + iface.errors_out}
                            </span>
                          ) : (
                            <span className="text-green-600">0</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {/* 网络统计摘要 */}
              <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div className="text-center p-3 bg-white/30 rounded-lg">
                  <div className="text-gray-600">总接口数</div>
                  <div className="text-lg font-semibold text-blue-600">
                    {systemResources.network_interfaces.length}
                  </div>
                </div>
                <div className="text-center p-3 bg-white/30 rounded-lg">
                  <div className="text-gray-600">活跃接口</div>
                  <div className="text-lg font-semibold text-green-600">
                    {systemResources.network_interfaces.filter(i => i.status === 'up').length}
                  </div>
                </div>
                <div className="text-center p-3 bg-white/30 rounded-lg">
                  <div className="text-gray-600">总发送</div>
                  <div className="text-lg font-semibold text-purple-600">
                    {monitoringService.formatBytes(
                      systemResources.network_interfaces.reduce((sum, i) => sum + i.bytes_sent, 0)
                    )}
                  </div>
                </div>
                <div className="text-center p-3 bg-white/30 rounded-lg">
                  <div className="text-gray-600">总接收</div>
                  <div className="text-lg font-semibold text-indigo-600">
                    {monitoringService.formatBytes(
                      systemResources.network_interfaces.reduce((sum, i) => sum + i.bytes_recv, 0)
                    )}
                  </div>
                </div>
              </div>
            </GlassCard>
          )}

          {/* 性能报告图表 */}
          {performanceReport && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* 任务执行趋势 */}
              <GlassChart
                type="line"
                title="📈 任务执行趋势"
                data={{
                  datasets: [{
                    label: '每日任务数',
                    data: performanceReport.daily_trends.map(trend => ({
                      label: trend.date,
                      value: trend.task_count
                    })),
                    color: '#3B82F6',
                    fillColor: '#3B82F6'
                  }]
                }}
                height={300}
                showGrid={true}
                animated={true}
              />

              {/* 任务状态分布 */}
              <GlassChart
                type="doughnut"
                title="📊 任务状态分布"
                data={{
                  data: [
                    {
                      label: '成功',
                      value: performanceReport.task_performance.success_tasks,
                      color: '#10B981'
                    },
                    {
                      label: '失败',
                      value: performanceReport.task_performance.failed_tasks,
                      color: '#EF4444'
                    }
                  ],
                  centerText: `${performanceReport.task_performance.success_rate.toFixed(1)}%`
                }}
                height={300}
                animated={true}
              />

              {/* 执行时长分布 */}
              <GlassChart
                type="bar"
                title="⏱️ 最慢任务执行时长"
                data={{
                  labels: performanceReport.slowest_tasks.slice(0, 5).map(task => 
                    task.playbook_name.length > 10 
                      ? task.playbook_name.substring(0, 10) + '...' 
                      : task.playbook_name
                  ),
                  datasets: [{
                    label: '执行时长(秒)',
                    data: performanceReport.slowest_tasks.slice(0, 5).map(task => task.duration),
                    backgroundColor: ['#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#10B981']
                  }]
                }}
                height={300}
                animated={true}
              />

              {/* 系统运行时间 */}
              <GlassCard className="p-6 flex items-center justify-center">
                <div className="text-center">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4">🕐 系统运行时间</h3>
                  <div className="text-3xl font-bold text-blue-600 mb-2">
                    {systemResources ? monitoringService.formatUptime(systemResources.system.uptime_seconds) : '--'}
                  </div>
                  <p className="text-sm text-gray-600">
                    启动时间: {systemResources ? formatDateTime(systemResources.system.boot_time) : '--'}
                  </p>
                  
                  {/* 性能摘要 */}
                  <div className="mt-6 grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="text-lg font-semibold text-green-600">
                        {performanceReport.task_performance.total_tasks}
                      </div>
                      <div className="text-gray-600">总任务数</div>
                    </div>
                    <div>
                      <div className="text-lg font-semibold text-blue-600">
                        {monitoringService.formatDuration(performanceReport.task_performance.average_duration)}
                      </div>
                      <div className="text-gray-600">平均时长</div>
                    </div>
                  </div>
                </div>
              </GlassCard>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default Monitoring
