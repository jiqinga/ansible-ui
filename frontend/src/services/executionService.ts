/**
 * 🚀 任务执行服务
 * 
 * 提供Ansible任务执行相关的API调用功能，包括：
 * - 执行Playbook
 * - 查询任务状态和结果
 * - 获取任务日志
 * - 取消任务
 * - WebSocket实时通信
 */

import { apiClient, apiUtils } from './apiClient'

// 📋 类型定义
export interface ExecutionOptions {
  limit?: string
  tags?: string
  skip_tags?: string
  extra_vars?: Record<string, any>
  user?: string
  private_key_file?: string
  connection?: string
  timeout?: number
  forks?: number
  verbose?: number
  check?: boolean
  diff?: boolean
  become?: boolean
  become_user?: string
  become_method?: string
}

export interface ExecutePlaybookRequest {
  playbook_name: string
  inventory_targets: string[]
  execution_options?: ExecutionOptions
}

export interface TaskStatus {
  task_id: string
  task_name: string
  status: string
  progress: number
  current_step?: string
  start_time?: string
  end_time?: string
  duration?: number
  error_message?: string
}

export interface TaskResult {
  task_id: string
  playbook_name: string
  status: string
  exit_code?: number
  start_time?: string
  end_time?: string
  duration?: number
  stats?: Record<string, any>
  log_file_path?: string
  error_message?: string
  failed_tasks?: Array<Record<string, any>>
}

export interface TaskLog {
  task_id: string
  logs: string[]
  total_count: number
}

export interface TaskListResponse {
  tasks: TaskStatus[]
  total_count: number
  page: number
  page_size: number
}

export interface CancelTaskResponse {
  success: boolean
  message: string
  task_id: string
}

export interface ValidatePlaybookResponse {
  valid: boolean
  errors: string[]
  warnings: string[]
  message: string
}

export interface TestConnectionResponse {
  total_hosts: number
  successful_hosts: string[]
  failed_hosts: string[]
  success_rate: number
  message: string
}

export interface WebSocketMessage {
  type: string
  task_id: string
  data: Record<string, any>
  timestamp: string
}

/**
 * 🚀 任务执行服务类
 */
export class ExecutionService {
  private baseUrl = '/execution'

  /**
   * 📋 获取任务列表
   */
  async getTaskList(
    status?: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<TaskListResponse> {
    const params = new URLSearchParams()
    if (status) params.append('status', status)
    params.append('page', page.toString())
    params.append('page_size', pageSize.toString())

    const response = await apiClient.get<TaskListResponse>(
      `${this.baseUrl}/tasks?${params.toString()}`
    )
    return response.data
  }

  /**
   * 🔍 获取任务状态
   */
  async getTaskStatus(taskId: string): Promise<TaskStatus> {
    const response = await apiClient.get<TaskStatus>(
      `${this.baseUrl}/tasks/${taskId}/status`
    )
    return response.data
  }

  /**
   * 📊 获取任务结果
   */
  async getTaskResult(taskId: string): Promise<TaskResult> {
    const response = await apiClient.get<TaskResult>(
      `${this.baseUrl}/tasks/${taskId}/result`
    )
    return response.data
  }

  /**
   * 📝 获取任务日志
   */
  async getTaskLogs(
    taskId: string,
    offset: number = 0,
    limit: number = 100
  ): Promise<TaskLog> {
    const params = new URLSearchParams()
    params.append('offset', offset.toString())
    params.append('limit', limit.toString())

    const response = await apiClient.get<TaskLog>(
      `${this.baseUrl}/tasks/${taskId}/logs?${params.toString()}`
    )
    return response.data
  }

  /**
   * 🚀 执行Playbook
   */
  async executePlaybook(request: ExecutePlaybookRequest): Promise<TaskStatus> {
    const response = await apiClient.post<TaskStatus>(
      `${this.baseUrl}/playbook`,
      request
    )
    return response.data
  }

  /**
   * 🛑 取消任务
   */
  async cancelTask(taskId: string): Promise<CancelTaskResponse> {
    const response = await apiClient.post<CancelTaskResponse>(
      `${this.baseUrl}/tasks/${taskId}/cancel`
    )
    return response.data
  }

  /**
   * ✅ 验证Playbook
   */
  async validatePlaybook(playbookName: string): Promise<ValidatePlaybookResponse> {
    const response = await apiClient.post<ValidatePlaybookResponse>(
      `${this.baseUrl}/validate`,
      { playbook_name: playbookName }
    )
    return response.data
  }

  /**
   * 🔌 测试连接
   */
  async testConnection(inventoryTargets: string[]): Promise<TestConnectionResponse> {
    const response = await apiClient.post<TestConnectionResponse>(
      `${this.baseUrl}/test-connection`,
      { inventory_targets: inventoryTargets }
    )
    return response.data
  }

  /**
   * 建立 WebSocket 连接以获取实时日志
   */
  createWebSocketConnection(
    taskId: string,
    onMessage: (message: WebSocketMessage) => void,
    onError?: (error: Event) => void,
    onClose?: (event: CloseEvent) => void
  ): WebSocket {
    const token = this.resolveAuthToken()
    if (!token) {
      const error = new Error('Missing authentication token for WebSocket connection')
      console.error(error.message)
      throw error
    }

    const wsUrl = this.buildWebSocketUrl(taskId, token)
    const ws = new WebSocket(wsUrl)
    let heartbeatTimer: number | null = null

    const stopHeartbeat = () => {
      if (heartbeatTimer !== null) {
        window.clearInterval(heartbeatTimer)
        heartbeatTimer = null
      }
    }

    const startHeartbeat = () => {
      stopHeartbeat()
      heartbeatTimer = window.setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping')
        } else {
          stopHeartbeat()
        }
      }, 30000)
    }

    ws.onopen = () => {
      console.info(`WebSocket connected: ${taskId}`)
      startHeartbeat()
    }

    ws.onmessage = async (event) => {
      try {
        const payload = await this.parseWebSocketPayload(event)
        if (payload) {
          onMessage(payload)
        }
      } catch (error) {
        console.error('Failed to handle WebSocket message', error)
      }
    }

    ws.onerror = (event) => {
      stopHeartbeat()
      console.error('WebSocket connection error', event)
      if (onError) {
        onError(event)
      }
    }

    ws.onclose = (event) => {
      stopHeartbeat()
      console.warn(`WebSocket closed: ${taskId}`, event.code, event.reason)
      if (onClose) {
        onClose(event)
      }
    }

    return ws
  }

  private resolveAuthToken(): string | null {
    const directToken = apiUtils.getToken()
    if (directToken) {
      console.log('🔑 使用直接token')
      return directToken
    }

    const stored = localStorage.getItem('access_token')
    if (!stored) {
      console.warn('⚠️ 未找到access_token')
      return null
    }

    try {
      const parsed = JSON.parse(stored)
      console.log('🔑 使用localStorage中的token (已解析)')
      return parsed
    } catch {
      console.log('🔑 使用localStorage中的token (原始)')
      return stored
    }
  }

  private buildWebSocketUrl(taskId: string, token: string): string {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000')
    const url = new URL(`/api/v1/execution/tasks/${taskId}/logs/stream`, baseUrl)
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
    url.searchParams.set('token', token)
    url.searchParams.set('client', 'web')
    const wsUrl = url.toString()
    console.log('🔗 WebSocket URL:', wsUrl)
    return wsUrl
  }

  private async parseWebSocketPayload(event: MessageEvent): Promise<WebSocketMessage | null> {
    let rawData: string

    if (typeof event.data === 'string') {
      rawData = event.data
    } else if (event.data instanceof Blob) {
      rawData = await event.data.text()
    } else if (event.data instanceof ArrayBuffer) {
      rawData = new TextDecoder().decode(event.data)
    } else {
      console.warn('Unsupported WebSocket payload type', event.data)
      return null
    }

    if (!rawData) {
      return null
    }

    try {
      return JSON.parse(rawData) as WebSocketMessage
    } catch (error) {
      console.error('Failed to parse WebSocket payload', error)
      return null
    }
  }


  /**
   * 格式化任务状态为中文
   */
  formatTaskStatus(status: string): string {
    const statusMap: Record<string, string> = {
      'PENDING': '等待中',
      'STARTED': '执行中',
      'SUCCESS': '成功',
      'FAILURE': '失败',
      'RETRY': '重试中',
      'REVOKED': '已取消'
    }
    return statusMap[status] || status
  }

  /**
   * 格式化执行时长
   */
  formatDuration(seconds?: number): string {
    if (!seconds) return '--'
    
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    
    if (hours > 0) {
      return `${hours}小时${minutes}分钟${secs}秒`
    } else if (minutes > 0) {
      return `${minutes}分钟${secs}秒`
    } else {
      return `${secs}秒`
    }
  }

  /**
   * 获取状态对应的颜色
   */
  getStatusColor(status: string): string {
    const colorMap: Record<string, string> = {
      'PENDING': 'text-yellow-600',
      'STARTED': 'text-blue-600',
      'SUCCESS': 'text-green-600',
      'FAILURE': 'text-red-600',
      'RETRY': 'text-orange-600',
      'REVOKED': 'text-gray-600'
    }
    return colorMap[status] || 'text-gray-600'
  }

  /**
   * 获取状态对应的图标
   */
  getStatusIcon(status: string): string {
    const iconMap: Record<string, string> = {
      'PENDING': '⏳',
      'STARTED': '🚀',
      'SUCCESS': '✅',
      'FAILURE': '❌',
      'RETRY': '🔄',
      'REVOKED': '🛑'
    }
    return iconMap[status] || '❓'
  }
}

// 🌟 导出服务实例
export const executionService = new ExecutionService()
export default executionService