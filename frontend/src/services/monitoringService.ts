/**
 * 📊 系统监控服务
 * 
 * 提供系统资源监控、性能统计和健康检查相关的API调用功能
 */

import { apiClient } from './apiClient'

// 💾 磁盘分区信息接口
export interface DiskPartition {
  device: string
  mountpoint: string
  fstype: string
  opts: string
  total_gb: number
  used_gb: number
  free_gb: number
  usage_percent: number
}

// 🌐 网络接口信息接口
export interface NetworkInterface {
  name: string
  status: 'up' | 'down'
  speed_mbps: number | null
  mtu: number
  ipv4: string | null
  ipv6: string | null
  mac: string | null
  bytes_sent: number
  bytes_recv: number
  packets_sent: number
  packets_recv: number
  errors_in: number
  errors_out: number
  drops_in: number
  drops_out: number
}

// 📊 系统资源信息接口
export interface SystemResources {
  timestamp: string
  cpu: {
    usage_percent: number
    count: number
    frequency_mhz?: number
    load_average?: number[]
  }
  memory: {
    total_gb: number
    available_gb: number
    used_gb: number
    usage_percent: number
    swap_total_gb: number
    swap_used_gb: number
    swap_percent: number
  }
  disk: {
    total_gb: number
    used_gb: number
    free_gb: number
    usage_percent: number
  }
  disk_partitions?: DiskPartition[]  // 🆕 所有磁盘分区信息
  network: {
    bytes_sent: number
    bytes_recv: number
    packets_sent: number
    packets_recv: number
  }
  network_interfaces?: NetworkInterface[]  // 🆕 所有网络接口信息
  system: {
    boot_time: string
    uptime_seconds: number
    uptime_days: number
  }
}

// 📱 应用程序指标接口
export interface ApplicationMetrics {
  timestamp: string
  process: {
    pid: number
    memory_mb: number
    cpu_percent: number
    threads: number
    open_files: number
    connections: number
    create_time: string
  }
  database: {
    pool: Record<string, any>
    connection_active: boolean
  }
  tasks: {
    total_tasks: number
    recent_24h_tasks: number
    running_tasks: number
    success_rate_24h: number
    average_duration_24h: number
  }
  logs: {
    total_files: number
    total_size_mb: number
  }
}

// 🏥 健康状态接口
export interface HealthAlert {
  type: string
  message: string
  severity: 'info' | 'warning' | 'error' | 'critical'
  value?: number
  threshold?: number
  timestamp?: string
}

export interface HealthStatus {
  overall_status: 'healthy' | 'warning' | 'critical' | 'error'
  warnings: HealthAlert[]
  errors: HealthAlert[]
  timestamp: string
}

// 📈 性能报告接口
export interface TaskPerformanceMetrics {
  total_tasks: number
  success_tasks: number
  failed_tasks: number
  success_rate: number
  average_duration: number
  min_duration: number
  max_duration: number
}

export interface DailyTrend {
  date: string
  task_count: number
  average_duration: number
}

export interface SlowestTask {
  task_id: string
  playbook_name: string
  duration: number
  created_at: string
}

export interface PerformanceReport {
  report_period_days: number
  generated_at: string
  task_performance: TaskPerformanceMetrics
  daily_trends: DailyTrend[]
  slowest_tasks: SlowestTask[]
  current_system_resources: SystemResources
}

// 🚨 警告阈值接口
export interface AlertThreshold {
  warning: number
  critical: number
}

export interface AlertThresholds {
  cpu_usage: AlertThreshold
  memory_usage: AlertThreshold
  disk_usage: AlertThreshold
  success_rate: AlertThreshold
  running_tasks: AlertThreshold
  log_size_mb: AlertThreshold
}

// 📊 监控仪表板接口
export interface MonitoringDashboard {
  system_resources: SystemResources
  application_metrics: ApplicationMetrics
  health_status: HealthStatus
  recent_alerts: HealthAlert[]
  uptime_seconds: number
  last_updated: string
}

// 📈 指标历史数据接口
export interface MetricDataPoint {
  timestamp: string
  value: number
  label?: string
}

export interface MetricsHistory {
  metric_type: string
  data_points: MetricDataPoint[]
  start_time: string
  end_time: string
  interval_minutes: number
}

/**
 * 🔧 系统监控服务类
 */
class MonitoringService {
  /**
   * 📊 获取系统资源信息
   */
  async getSystemResources(): Promise<SystemResources> {
    const response = await apiClient.get('/api/v1/monitoring/system/resources')
    return response.data
  }

  /**
   * 📱 获取应用程序指标
   */
  async getApplicationMetrics(): Promise<ApplicationMetrics> {
    const response = await apiClient.get('/api/v1/monitoring/application/metrics')
    return response.data
  }

  /**
   * 🏥 获取系统健康状态
   */
  async getHealthStatus(): Promise<HealthStatus> {
    const response = await apiClient.get('/api/v1/monitoring/health')
    return response.data
  }

  /**
   * 📈 获取性能报告
   */
  async getPerformanceReport(days: number = 7): Promise<PerformanceReport> {
    const response = await apiClient.get('/api/v1/monitoring/performance/report', {
      params: { days }
    })
    return response.data
  }

  /**
   * 🚨 获取警告阈值
   */
  async getAlertThresholds(): Promise<AlertThresholds> {
    const response = await apiClient.get('/api/v1/monitoring/alerts/thresholds')
    return response.data
  }

  /**
   * 🔧 更新警告阈值
   */
  async updateAlertThresholds(thresholds: Partial<AlertThresholds>): Promise<void> {
    await apiClient.put('/api/v1/monitoring/alerts/thresholds', thresholds)
  }

  /**
   * 📊 获取监控仪表板数据
   */
  async getMonitoringDashboard(): Promise<MonitoringDashboard> {
    const response = await apiClient.get('/api/v1/monitoring/dashboard')
    return response.data
  }

  /**
   * 📈 获取指标历史数据
   */
  async getMetricsHistory(
    metricType: string,
    hours: number = 24,
    intervalMinutes: number = 60
  ): Promise<MetricsHistory> {
    const response = await apiClient.get('/api/v1/monitoring/metrics/history', {
      params: {
        metric_type: metricType,
        hours,
        interval_minutes: intervalMinutes
      }
    })
    return response.data
  }

  /**
   * 🎨 格式化健康状态
   */
  formatHealthStatus(status: string): string {
    const statusMap: Record<string, string> = {
      'healthy': '✅ 健康',
      'warning': '⚠️ 警告',
      'critical': '🚨 严重',
      'error': '❌ 错误'
    }
    return statusMap[status] || status
  }

  /**
   * 🎨 获取健康状态颜色
   */
  getHealthStatusColor(status: string): string {
    const colorMap: Record<string, string> = {
      'healthy': 'text-green-600 bg-green-50 border-green-200',
      'warning': 'text-yellow-600 bg-yellow-50 border-yellow-200',
      'critical': 'text-red-600 bg-red-50 border-red-200',
      'error': 'text-red-600 bg-red-50 border-red-200'
    }
    return colorMap[status] || 'text-gray-600 bg-gray-50 border-gray-200'
  }

  /**
   * 🎨 格式化警告严重程度
   */
  formatAlertSeverity(severity: string): string {
    const severityMap: Record<string, string> = {
      'info': '💡 信息',
      'warning': '⚠️ 警告',
      'error': '❌ 错误',
      'critical': '🚨 严重'
    }
    return severityMap[severity] || severity
  }

  /**
   * 🎨 获取警告严重程度颜色
   */
  getAlertSeverityColor(severity: string): string {
    const colorMap: Record<string, string> = {
      'info': 'text-blue-600 bg-blue-50 border-blue-200',
      'warning': 'text-yellow-600 bg-yellow-50 border-yellow-200',
      'error': 'text-red-600 bg-red-50 border-red-200',
      'critical': 'text-red-600 bg-red-50 border-red-200'
    }
    return colorMap[severity] || 'text-gray-600 bg-gray-50 border-gray-200'
  }

  /**
   * 📊 格式化字节大小
   */
  formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B'
    
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  /**
   * ⏱️ 格式化运行时间
   */
  formatUptime(seconds: number): string {
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    
    if (days > 0) {
      return `${days}天 ${hours}小时 ${minutes}分钟`
    } else if (hours > 0) {
      return `${hours}小时 ${minutes}分钟`
    } else {
      return `${minutes}分钟`
    }
  }

  /**
   * 📊 格式化百分比
   */
  formatPercentage(value: number): string {
    return `${value.toFixed(1)}%`
  }

  /**
   * ⏱️ 格式化持续时间
   */
  formatDuration(seconds: number): string {
    if (seconds < 60) {
      return `${seconds.toFixed(1)}秒`
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60)
      const remainingSeconds = seconds % 60
      return `${minutes}分${remainingSeconds.toFixed(0)}秒`
    } else {
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      return `${hours}小时${minutes}分钟`
    }
  }
}

// 导出服务实例
export const monitoringService = new MonitoringService()
export default monitoringService