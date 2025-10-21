/**
 * 🏠 Dashboard数据服务
 * 
 * 提供Dashboard页面所需的各种数据获取功能：
 * - 系统统计信息
 * - 实时监控数据
 * - 最近任务记录
 * - 快速操作数据
 */

import { apiClient } from './apiClient'

// 📊 统计数据接口
export interface DashboardStats {
  totalHosts: number
  totalPlaybooks: number
  runningTasks: number
  successRate: number
  totalExecutions: number
  activeUsers: number
}

// 🖥️ 系统资源接口
export interface SystemResources {
  cpu: {
    usage_percent: number
    load_average: number[]
  }
  memory: {
    usage_percent: number
    total_gb: number
    used_gb: number
    available_gb: number
  }
  disk: {
    usage_percent: number
    total_gb: number
    used_gb: number
    free_gb: number
  }
  network: {
    bytes_sent: number
    bytes_recv: number
    packets_sent: number
    packets_recv: number
  }
}

// 📋 最近任务接口
export interface RecentTask {
  id: string
  task_id: string
  name: string
  playbook_name: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled'
  start_time: string
  end_time?: string
  duration?: number
  user_name: string
  inventory_targets: string[]
}

// 🎯 快速操作接口
export interface QuickAction {
  id: string
  title: string
  description: string
  icon: string
  color: string
  action: string
  enabled: boolean
}

// 📈 趋势数据接口
export interface TrendData {
  date: string
  success_count: number
  failed_count: number
  total_count: number
  success_rate: number
}

// 🚨 系统警告接口
export interface SystemAlert {
  id: string
  type: 'info' | 'warning' | 'error' | 'critical'
  title: string
  message: string
  timestamp: string
  resolved: boolean
}

/**
 * Dashboard数据服务类
 */
export class DashboardService {
  /**
   * 🔢 获取Dashboard统计数据
   */
  static async getStats(): Promise<DashboardStats> {
    try {
      const [
        inventoryResponse,
        playbooksResponse,
        executionsResponse,
        monitoringResponse
      ] = await Promise.all([
        apiClient.get('/inventory/hosts/count'),
        apiClient.get('/playbooks/count'),
        apiClient.get('/history/statistics?period=today'),
        apiClient.get('/monitoring/status/summary')
      ])

      return {
        totalHosts: inventoryResponse.data.total_count || 0,
        totalPlaybooks: playbooksResponse.data.total || 0,
        runningTasks: monitoringResponse.data.running_tasks || 0,
        successRate: Math.round(monitoringResponse.data.success_rate_24h || 0),
        totalExecutions: executionsResponse.data.total_executions || 0,
        activeUsers: executionsResponse.data.active_users || 0
      }
    } catch (error) {
      console.error('获取统计数据失败:', error)
      throw error
    }
  }

  /**
   * 🖥️ 获取系统资源信息
   */
  static async getSystemResources(): Promise<SystemResources> {
    try {
      const response = await apiClient.get('/monitoring/system/resources')
      return response.data
    } catch (error) {
      console.error('获取系统资源信息失败:', error)
      throw error
    }
  }

  /**
   * 📋 获取最近任务记录
   */
  static async getRecentTasks(limit: number = 10): Promise<RecentTask[]> {
    try {
      const response = await apiClient.get(`/api/v1/history/executions?limit=${limit}&sort_by=created_at&sort_order=desc`)
      
      return response.data.items.map((item: any) => ({
        id: item.id,
        task_id: item.task_id,
        name: item.playbook_name,
        playbook_name: item.playbook_name,
        status: item.status,
        start_time: item.start_time,
        end_time: item.end_time,
        duration: item.duration,
        user_name: item.username || '未知用户',
        inventory_targets: item.inventory_targets || []
      }))
    } catch (error) {
      console.error('获取最近任务失败:', error)
      throw error
    }
  }

  /**
   * 🎯 获取快速操作配置
   */
  static async getQuickActions(): Promise<QuickAction[]> {
    // 这里可以从配置API获取，目前返回默认配置
    return [
      {
        id: 'run-task',
        title: '运行任务',
        description: '快速执行Ansible任务',
        icon: 'PlayIcon',
        color: 'bg-blue-500/20 hover:bg-blue-500/30 text-blue-600',
        action: '/execution/new',
        enabled: true
      },
      {
        id: 'add-host',
        title: '添加主机',
        description: '添加新的主机到清单',
        icon: 'ServerIcon',
        color: 'bg-green-500/20 hover:bg-green-500/30 text-green-600',
        action: '/inventory/hosts/new',
        enabled: true
      },
      {
        id: 'create-playbook',
        title: '创建Playbook',
        description: '创建新的Ansible Playbook',
        icon: 'DocumentTextIcon',
        color: 'bg-purple-500/20 hover:bg-purple-500/30 text-purple-600',
        action: '/playbooks/new',
        enabled: true
      },
      {
        id: 'view-monitoring',
        title: '查看监控',
        description: '查看系统监控信息',
        icon: 'ChartBarIcon',
        color: 'bg-orange-500/20 hover:bg-orange-500/30 text-orange-600',
        action: '/monitoring',
        enabled: true
      }
    ]
  }

  /**
   * 📈 获取执行趋势数据
   */
  static async getExecutionTrends(days: number = 7): Promise<TrendData[]> {
    try {
      const response = await apiClient.get(`/api/v1/history/trends?days=${days}`)
      const trendsData = response.data.trends
      
      // 转换后端返回的 daily_trends 格式为前端期望的格式
      if (trendsData && trendsData.daily_trends) {
        return trendsData.daily_trends.map((item: any) => ({
          date: item.date || item.period,
          success_count: item.success_tasks || 0,
          failed_count: item.failed_tasks || 0,
          total_count: item.total_tasks || 0,
          success_rate: item.success_rate || 0
        }))
      }
      
      return []
    } catch (error) {
      console.error('获取趋势数据失败:', error)
      throw error
    }
  }

  /**
   * 🚨 获取系统警告信息
   */
  static async getSystemAlerts(limit: number = 5): Promise<SystemAlert[]> {
    try {
      const response = await apiClient.get(`/api/v1/monitoring/alerts?limit=${limit}`)
      return response.data.alerts || []
    } catch (error) {
      console.error('获取系统警告失败:', error)
      throw error
    }
  }

  /**
   * 🔄 获取实时状态更新
   */
  static async getRealtimeStatus(): Promise<{
    timestamp: string
    stats: DashboardStats
    resources: SystemResources
    alerts: SystemAlert[]
  }> {
    const [stats, resources, alerts] = await Promise.all([
      this.getStats(),
      this.getSystemResources(),
      this.getSystemAlerts()
    ])

    return {
      timestamp: new Date().toISOString(),
      stats,
      resources,
      alerts
    }
  }
}

export default DashboardService
