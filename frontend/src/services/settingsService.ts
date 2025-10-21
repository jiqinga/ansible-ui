/**
 * 🔧 系统设置服务
 * 
 * 提供系统配置管理、用户管理等设置相关的API调用功能
 */

import { apiClient } from './apiClient'

// 🏷️ 类型定义
export interface ConfigItem {
  key: string
  value: any
  description: string
  category: string
  is_sensitive: boolean
  is_readonly: boolean
  requires_restart: boolean
  validation_rule?: string
  default_value?: any
  created_at?: string
  updated_at?: string
}

export interface ConfigCategory {
  name: string
  display_name: string
  description: string
  config_count: number
  icon?: string
}

export interface SystemStatus {
  ansible_config_valid: boolean
  database_connected: boolean
  redis_connected: boolean
  disk_usage_percent: number
  memory_usage_percent: number
  active_tasks: number
  last_check_time: string
}

export interface UserInfo {
  id: number
  username: string
  email: string
  full_name?: string
  role: 'admin' | 'operator' | 'viewer'
  is_active: boolean
  is_superuser: boolean
  last_login?: string
  login_count: number
  created_at: string
  updated_at: string
}

export interface UserStats {
  total_users: number
  active_users: number
  inactive_users: number
  admin_users: number
  operator_users: number
  viewer_users: number
}

export interface ConfigBackup {
  name: string
  description: string
  created_at: string
  size: number
  config_count: number
  categories: string[]
}

export interface ConfigValidationResult {
  valid: boolean
  errors: Record<string, string>
  restart_required: string[]
  warnings: Record<string, string>
}

export interface ConfigUpdateResult {
  success: boolean
  errors: Record<string, string>
  updated: Record<string, boolean>
  restart_required: string[]
  success_count?: number
  error_count?: number
  total_count?: number
  results?: Record<string, string>
}

// 🔧 配置管理服务
export class ConfigService {
  /**
   * 📋 获取配置分类列表
   */
  static async getCategories(): Promise<ConfigCategory[]> {
    const response = await apiClient.get('/config/categories')
    return response.data.categories
  }

  /**
   * 📄 根据分类获取配置项
   */
  static async getConfigsByCategory(category: string): Promise<ConfigItem[]> {
    const response = await apiClient.get(`/api/v1/config/category/${category}`)
    return response.data.configs
  }

  /**
   * 🔍 获取单个配置项详情
   */
  static async getConfigDetail(key: string): Promise<ConfigItem> {
    const response = await apiClient.get(`/api/v1/config/${key}`)
    return response.data.config
  }

  /**
   * ✏️ 更新单个配置项
   */
  static async updateConfig(key: string, value: any): Promise<ConfigUpdateResult> {
    const response = await apiClient.put(`/api/v1/config/${key}`, { value })
    return response.data
  }

  /**
   * 📝 批量更新配置项
   */
  static async batchUpdateConfigs(configs: Record<string, any>): Promise<ConfigUpdateResult> {
    const response = await apiClient.post('/config/batch-update', { configs })
    return response.data
  }

  /**
   * ✅ 验证配置变更
   */
  static async validateConfigs(configs: Record<string, any>): Promise<ConfigValidationResult> {
    const response = await apiClient.post('/config/validate', { configs })
    return response.data
  }

  /**
   * 🔄 重置配置为默认值
   */
  static async resetConfigs(keys: string[]): Promise<ConfigUpdateResult> {
    const response = await apiClient.post('/config/reset', { keys })
    return response.data
  }

  /**
   * 📊 获取系统状态
   */
  static async getSystemStatus(): Promise<SystemStatus> {
    const response = await apiClient.get('/config/system/status')
    return response.data
  }

  /**
   * 🎯 初始化默认配置
   */
  static async initializeDefaultConfigs(): Promise<void> {
    await apiClient.post('/config/initialize')
  }
}

// 👥 用户管理服务
export class UserManagementService {
  /**
   * 📋 获取用户列表
   */
  static async getUsers(params: {
    page?: number
    page_size?: number
    role?: string
    is_active?: boolean
    search?: string
  } = {}): Promise<{
    users: UserInfo[]
    total: number
    page: number
    page_size: number
  }> {
    const response = await apiClient.get('/users', { params })
    return response.data
  }

  /**
   * 📊 获取用户统计
   */
  static async getUserStats(): Promise<UserStats> {
    const response = await apiClient.get('/users/stats')
    return response.data
  }

  /**
   * 🔍 获取用户详情
   */
  static async getUserDetail(userId: number): Promise<UserInfo> {
    const response = await apiClient.get(`/api/v1/users/${userId}`)
    return response.data
  }

  /**
   * ➕ 创建用户
   */
  static async createUser(userData: {
    username: string
    email: string
    password: string
    full_name?: string
    role?: string
    is_active?: boolean
  }): Promise<UserInfo> {
    const response = await apiClient.post('/users', userData)
    return response.data
  }

  /**
   * ✏️ 更新用户信息
   */
  static async updateUser(userId: number, userData: {
    email?: string
    full_name?: string
    role?: string
    is_active?: boolean
  }): Promise<UserInfo> {
    const response = await apiClient.put(`/api/v1/users/${userId}`, userData)
    return response.data
  }

  /**
   * 🗑️ 删除用户
   */
  static async deleteUser(userId: number): Promise<void> {
    await apiClient.delete(`/api/v1/users/${userId}`)
  }

  /**
   * ✅ 激活用户
   */
  static async activateUser(userId: number): Promise<void> {
    await apiClient.post(`/api/v1/users/${userId}/activate`)
  }

  /**
   * ❌ 停用用户
   */
  static async deactivateUser(userId: number): Promise<void> {
    await apiClient.post(`/api/v1/users/${userId}/deactivate`)
  }

  /**
   * 🔑 重置用户密码
   */
  static async resetUserPassword(userId: number, newPassword: string): Promise<void> {
    await apiClient.post(`/api/v1/users/${userId}/reset-password`, { new_password: newPassword })
  }

  /**
   * 👑 更新用户角色
   */
  static async updateUserRole(userId: number, role: string): Promise<void> {
    await apiClient.put(`/api/v1/users/${userId}/role`, null, { params: { role } })
  }

  /**
   * 🔍 按角色获取用户
   */
  static async getUsersByRole(role: string): Promise<UserInfo[]> {
    const response = await apiClient.get(`/api/v1/users/role/${role}`)
    return response.data
  }
}

// 💾 配置备份服务
export class ConfigBackupService {
  /**
   * 📋 获取备份列表
   */
  static async getBackups(): Promise<ConfigBackup[]> {
    const response = await apiClient.get('/config/backups')
    return response.data.backups
  }

  /**
   * 💾 创建配置备份
   */
  static async createBackup(data: {
    backup_name: string
    description?: string
    include_categories?: string[]
  }): Promise<void> {
    await apiClient.post('/config/backup', data)
  }

  /**
   * 🔄 恢复配置备份
   */
  static async restoreBackup(data: {
    backup_name: string
    overwrite?: boolean
    restore_categories?: string[]
  }): Promise<ConfigUpdateResult> {
    const response = await apiClient.post('/config/restore', data)
    return response.data
  }

  /**
   * 🗑️ 删除配置备份
   */
  static async deleteBackup(backupName: string): Promise<void> {
    await apiClient.delete(`/api/v1/config/backup/${backupName}`)
  }

  /**
   * 🔍 比较配置差异
   */
  static async compareWithBackup(backupName: string): Promise<{
    differences: Array<{
      key: string
      current_value: any
      new_value: any
      action: 'add' | 'update' | 'delete'
    }>
    total_differences: number
    additions: number
    updates: number
    deletions: number
  }> {
    const response = await apiClient.get(`/api/v1/config/compare/${backupName}`)
    return response.data
  }
}

// 📁 Ansible配置服务
export class AnsibleConfigService {
  /**
   * 📄 获取Ansible配置文件内容
   */
  static async getConfigFile(): Promise<{
    content: string
    is_valid: boolean
    last_modified?: string
    backup_available: boolean
  }> {
    const response = await apiClient.get('/config/ansible/file')
    return response.data
  }

  /**
   * ✏️ 更新Ansible配置文件
   */
  static async updateConfigFile(content: string): Promise<ConfigUpdateResult> {
    const response = await apiClient.put('/config/ansible/file', { content })
    return response.data
  }

  /**
   * 🔄 恢复Ansible配置备份
   */
  static async restoreBackup(): Promise<ConfigUpdateResult> {
    const response = await apiClient.post('/config/ansible/restore-backup')
    return response.data
  }
}

// 📤 配置导入导出服务
export class ConfigImportExportService {
  /**
   * 📤 导出配置
   */
  static async exportConfigs(category: string): Promise<Blob> {
    const response = await apiClient.get(`/api/v1/config/export/${category}`, {
      responseType: 'blob'
    })
    return response.data
  }

  /**
   * 📥 导入配置
   */
  static async importConfigs(file: File, overwrite: boolean = false): Promise<{
    success: boolean
    results: Record<string, string>
    total_count: number
    success_count: number
    error_count: number
  }> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('overwrite', overwrite.toString())

    const response = await apiClient.post('/config/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  }
}
