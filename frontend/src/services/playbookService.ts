import { apiClient } from './apiClient'

/**
 * 📝 Playbook文件信息接口
 */
export interface PlaybookFile {
  id: number
  filename: string
  display_name?: string
  description?: string
  project_id?: number
  file_path?: string
  file_size: number
  file_hash?: string
  is_valid: boolean
  validation_error?: string
  created_at: string
  updated_at: string
  created_by?: number
}

/**
 * 📁 文件浏览器项目接口
 */
export interface FileItem {
  name: string
  path: string
  is_directory: boolean
  size?: number
  modified_time: string
  children?: FileItem[]
}

/**
 * ✅ Playbook验证结果接口
 */
export interface ValidationResult {
  is_valid: boolean
  errors: ValidationError[]
  warnings: ValidationWarning[]
}

/**
 * ❌ 验证错误接口
 */
export interface ValidationError {
  line: number
  column: number
  message: string
  severity: 'error' | 'warning'
  code?: string
}

/**
 * ⚠️ 验证警告接口
 */
export interface ValidationWarning {
  line: number
  column: number
  message: string
  suggestion?: string
}

/**
 * 📝 Playbook创建请求接口
 */
export interface CreatePlaybookRequest {
  filename: string  // 修改为 filename 以匹配后端 API
  content: string
  path?: string
}

/**
 * 📝 Playbook更新请求接口
 */
export interface UpdatePlaybookRequest {
  content: string
}

/**
 * 🎯 Playbook服务类
 * 
 * 提供Playbook文件管理的所有功能：
 * - 文件浏览和导航
 * - 文件内容读取和保存
 * - YAML语法验证
 * - 文件上传和下载
 */
export class PlaybookService {
  /**
   * 📂 获取Playbook列表（从数据库）
   */
  static async getPlaybooks(page: number = 1, size: number = 100, search?: string): Promise<{ items: PlaybookFile[]; total: number }> {
    try {
      const response = await apiClient.get(`/api/v1/playbooks/`, {
        params: { page, size, search }
      })
      return {
        items: response.data.items || [],
        total: response.data.total || 0
      }
    } catch (error) {
      console.error('❌ 获取Playbook列表失败:', error)
      throw error
    }
  }

  /**
   * 📂 浏览文件系统中的Playbook文件
   */
  static async browsePlaybookFiles(path: string = ''): Promise<FileItem[]> {
    try {
      const response = await apiClient.get(`/api/v1/playbooks/files`, {
        params: { path }
      })
      return response.data.files || []
    } catch (error) {
      console.error('❌ 浏览文件失败:', error)
      throw error
    }
  }

  /**
   * 📄 获取Playbook文件内容（通过ID）
   */
  static async getPlaybookContent(playbookId: number): Promise<{ content: string; filename: string; file_size: number }> {
    try {
      const response = await apiClient.get(`/api/v1/playbooks/${playbookId}/content`)
      return response.data
    } catch (error) {
      console.error('❌ 获取Playbook内容失败:', error)
      throw error
    }
  }

  /**
   * 📄 获取文件内容（通过路径）
   */
  static async getFileContent(path: string): Promise<string> {
    try {
      const response = await apiClient.get(`/api/v1/playbooks/content`, {
        params: { path }
      })
      return response.data.content || ''
    } catch (error) {
      console.error('❌ 获取文件内容失败:', error)
      throw error
    }
  }

  /**
   * 💾 保存Playbook文件内容
   */
  static async savePlaybookContent(path: string, content: string): Promise<void> {
    try {
      await apiClient.put(`/api/v1/playbooks/content`, {
        path,
        content
      })
    } catch (error) {
      console.error('❌ 保存Playbook内容失败:', error)
      throw new Error('保存文件失败，请检查网络连接或文件权限')
    }
  }

  /**
   * 📝 创建新的Playbook文件
   */
  static async createPlaybook(request: CreatePlaybookRequest): Promise<PlaybookFile> {
    try {
      const response = await apiClient.post('/playbooks/', request)
      return response.data
    } catch (error: any) {
      console.error('❌ 创建Playbook失败:', error)
      // 🔄 直接抛出原始错误，让调用方处理具体的错误信息
      throw error
    }
  }

  /**
   * 🗑️ 删除Playbook文件
   */
  static async deletePlaybook(path: string): Promise<void> {
    try {
      await apiClient.delete(`/api/v1/playbooks`, {
        params: { path }
      })
    } catch (error) {
      console.error('❌ 删除Playbook失败:', error)
      throw new Error('删除文件失败，请检查文件是否存在或权限')
    }
  }

  /**
   * ✅ 验证Playbook语法
   */
  static async validatePlaybook(content: string): Promise<ValidationResult> {
    try {
      const response = await apiClient.post('/playbooks/validate-content', {
        content
      })
      return response.data
    } catch (error) {
      console.error('❌ 验证Playbook失败:', error)
      // 🔄 返回基本的YAML语法检查结果
      return this.basicYamlValidation(content)
    }
  }

  /**
   * 🔍 基本YAML语法验证（客户端）
   */
  private static basicYamlValidation(content: string): ValidationResult {
    const errors: ValidationError[] = []
    const warnings: ValidationWarning[] = []
    
    const lines = content.split('\n')
    
    lines.forEach((line, index) => {
      const lineNumber = index + 1
      
      // 检查缩进
      if (line.trim() && line.match(/^\s*\t/)) {
        errors.push({
          line: lineNumber,
          column: 1,
          message: '不应使用Tab字符进行缩进，请使用空格',
          severity: 'error',
          code: 'yaml.indentation'
        })
      }
      
      // 检查冒号后的空格
      if (line.includes(':') && !line.match(/:\s/) && !line.match(/:$/)) {
        warnings.push({
          line: lineNumber,
          column: line.indexOf(':') + 1,
          message: '冒号后应该有空格',
          suggestion: '在冒号后添加空格'
        })
      }
    })
    
    return {
      is_valid: errors.length === 0,
      errors,
      warnings
    }
  }

  /**
   * 📊 获取Playbook统计信息
   */
  static async getPlaybookStats(): Promise<{ total: number; recent: number }> {
    try {
      const response = await apiClient.get('/playbooks/stats')
      return response.data
    } catch (error) {
      console.error('❌ 获取Playbook统计失败:', error)
      return { total: 0, recent: 0 }
    }
  }
}

export default PlaybookService
