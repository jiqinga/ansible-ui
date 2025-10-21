/**
 * 📦 Inventory管理服务
 * 
 * 提供主机和主机组管理的API接口封装
 */

import { apiClient } from './apiClient';

// 🏠 主机相关类型定义
export interface Host {
  id: number;
  hostname: string;
  display_name?: string;
  description?: string;
  group_name: string;
  ansible_host: string;
  ansible_port: number;
  ansible_user?: string;
  ansible_ssh_private_key_file?: string;
  ansible_ssh_pass?: string;
  ansible_become: boolean;
  ansible_become_user: string;
  ansible_become_method: string;
  variables: Record<string, any>;
  tags: string[];
  is_active: boolean;
  ping_status?: string;
  last_ping?: string;
  connection_string: string;
  is_reachable: boolean;
  extra_data?: {
    system_info?: {
      os?: {
        distribution?: string;
        distribution_version?: string;
        distribution_release?: string;
        system?: string;
      };
      kernel?: {
        kernel?: string;
        kernel_version?: string;
      };
      hardware?: {
        architecture?: string;
        machine?: string;
        processor?: string[];
        processor_cores?: number;
        processor_count?: number;
        processor_threads_per_core?: number;
        processor_vcpus?: number;
      };
      memory?: {
        memtotal_mb?: number;
        memfree_mb?: number;
        swaptotal_mb?: number;
        swapfree_mb?: number;
      };
      // 💿 磁盘信息
      disks?: Array<{
        mount: string;          // 挂载点
        device: string;         // 设备名
        fstype: string;         // 文件系统类型
        total_mb: number;       // 总容量（MB）
        used_mb: number;        // 已用容量（MB）
        free_mb: number;        // 可用容量（MB）
        percentage: number;     // 使用百分比
      }>;
      // 🌐 网络接口信息
      network?: {
        hostname?: string;
        fqdn?: string;
        domain?: string;
        default_ipv4?: any;
        default_ipv6?: any;
        interfaces?: Array<{
          name: string;         // 接口名
          status: string;       // 状态（up/down）
          ipv4?: string;        // IPv4地址
          ipv6?: string;        // IPv6地址
          mac?: string;         // MAC地址
          speed?: string;       // 速度
        }>;
      };
      // ⏱️ 系统运行时间
      uptime?: {
        boot_time: string;      // 启动时间（ISO格式）
        uptime_seconds: number; // 运行秒数
        days: number;           // 运行天数
        hours: number;          // 小时
        minutes: number;        // 分钟
      };
      python?: {
        version?: string;
        executable?: string;
      };
      collected_at?: string;
    };
  };
  created_at: string;
  updated_at: string;
}

export interface HostCreate {
  hostname: string;
  display_name?: string;
  description?: string;
  group_name?: string;
  ansible_host: string;
  ansible_port?: number;
  ansible_user?: string;
  ansible_ssh_private_key_file?: string;
  ansible_ssh_pass?: string;
  ansible_become?: boolean;
  ansible_become_user?: string;
  ansible_become_method?: string;
  variables?: Record<string, any>;
  tags?: string[];
  is_active?: boolean;
}

export interface HostUpdate {
  hostname?: string;
  display_name?: string;
  description?: string;
  group_name?: string;
  ansible_host?: string;
  ansible_port?: number;
  ansible_user?: string;
  ansible_ssh_private_key_file?: string;
  ansible_ssh_pass?: string;
  ansible_become?: boolean;
  ansible_become_user?: string;
  ansible_become_method?: string;
  variables?: Record<string, any>;
  tags?: string[];
  is_active?: boolean;
}

export interface HostListResponse {
  hosts: Host[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// 🏢 主机组相关类型定义
export interface HostGroup {
  id: number;
  name: string;
  display_name?: string;
  description?: string;
  parent_group?: string;
  variables: Record<string, any>;
  tags: string[];
  is_active: boolean;
  sort_order: number;
  is_root_group: boolean;
  full_path: string;
  host_count?: number;
  created_at: string;
  updated_at: string;
}

export interface HostGroupCreate {
  name: string;
  display_name?: string;
  description?: string;
  parent_group?: string;
  variables?: Record<string, any>;
  tags?: string[];
  is_active?: boolean;
  sort_order?: number;
}

// 📜 执行历史相关类型定义
export interface ExecutionHistory {
  id: number;
  task_id: string;
  playbook_name: string;
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled' | 'timeout';
  start_time?: string;
  end_time?: string;
  duration?: number;
  created_at: string;
  user?: {
    id: number;
    username: string;
  };
}

export interface ExecutionHistoryListResponse {
  executions: ExecutionHistory[];
  total: number;
  page: number;
  page_size: number;
}

export interface HostGroupUpdate {
  name?: string;
  display_name?: string;
  description?: string;
  parent_group?: string;
  variables?: Record<string, any>;
  tags?: string[];
  is_active?: boolean;
  sort_order?: number;
}

export interface HostGroupTreeNode {
  id: number;
  name: string;
  display_name?: string;
  description?: string;
  host_count: number;
  children: HostGroupTreeNode[];
  variables: Record<string, any>;
  tags: string[];
  is_active: boolean;
}

export interface HostGroupListResponse {
  groups: HostGroup[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// 📊 统计信息类型
export interface InventoryStats {
  total_hosts: number;
  active_hosts: number;
  inactive_hosts: number;
  reachable_hosts: number;
  unreachable_hosts: number;
  unknown_status_hosts: number;
  total_groups: number;
  group_stats: Record<string, number>;
}

// 🔍 搜索请求类型
export interface HostSearchRequest {
  query?: string;
  group_name?: string;
  tags?: string[];
  is_active?: boolean;
  ping_status?: string;
  page?: number;
  page_size?: number;
}

// 🎯 Ping结果类型
export interface PingResult {
  host_id: number;
  hostname: string;
  ansible_host: string;
  ansible_port: number;
  ansible_user: string;
  success: boolean;
  status: string;
  message: string;
  error_type?: string;
  details?: string;
}

export interface GroupPingResult {
  group_name: string;
  results: Record<string, boolean>;
  total_hosts: number;
  successful_hosts: number;
  failed_hosts: number;
}

/**
 * 📦 Inventory管理服务类
 */
export class InventoryService {
  private readonly baseUrl = '/inventory';

  // 🏠 主机管理方法
  
  /**
   * 📋 获取主机列表
   */
  async getHosts(params?: {
    group_name?: string;
    active_only?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<HostListResponse> {
    const response = await apiClient.get(`${this.baseUrl}/hosts`, { params });
    return response.data;
  }

  /**
   * 🔍 搜索主机
   */
  async searchHosts(searchRequest: HostSearchRequest): Promise<HostListResponse> {
    const response = await apiClient.post(`${this.baseUrl}/search/hosts`, searchRequest);
    return response.data;
  }

  /**
   * 📄 获取主机详情
   */
  async getHost(hostId: number): Promise<Host> {
    const response = await apiClient.get(`${this.baseUrl}/hosts/${hostId}`);
    return response.data;
  }

  /**
   * ➕ 创建主机
   */
  async createHost(hostData: HostCreate): Promise<Host> {
    const response = await apiClient.post(`${this.baseUrl}/hosts`, hostData);
    return response.data;
  }

  /**
   * ✏️ 更新主机
   */
  async updateHost(hostId: number, hostData: HostUpdate): Promise<Host> {
    const response = await apiClient.put(`${this.baseUrl}/hosts/${hostId}`, hostData);
    return response.data;
  }

  /**
   * 🗑️ 删除主机
   */
  async deleteHost(hostId: number): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/hosts/${hostId}`);
  }

  /**
   * 🔧 更新主机变量
   */
  async updateHostVariables(hostId: number, variables: Record<string, any>): Promise<Host> {
    const response = await apiClient.put(`${this.baseUrl}/hosts/${hostId}/variables`, { variables });
    return response.data;
  }

  /**
   * 🏷️ 更新主机标签
   */
  async updateHostTags(hostId: number, tags: string[]): Promise<Host> {
    const response = await apiClient.put(`${this.baseUrl}/hosts/${hostId}/tags`, { tags });
    return response.data;
  }

  /**
   * 🏓 测试主机连接
   */
  async pingHost(hostId: number): Promise<PingResult> {
    const response = await apiClient.post(`${this.baseUrl}/hosts/${hostId}/ping`);
    return response.data;
  }

  /**
   * 📊 收集主机系统信息
   */
  async gatherHostFacts(hostId: number): Promise<{
    success: boolean;
    message: string;
    facts?: any;
    error?: string;
  }> {
    const response = await apiClient.post(`${this.baseUrl}/hosts/${hostId}/gather-facts`);
    return response.data;
  }

  // 🏢 主机组管理方法

  /**
   * 📋 获取主机组列表
   */
  async getGroups(params?: {
    page?: number;
    page_size?: number;
  }): Promise<HostGroupListResponse> {
    const response = await apiClient.get(`${this.baseUrl}/groups`, { params });
    return response.data;
  }

  /**
   * 🌳 获取主机组树形结构
   */
  async getGroupTree(): Promise<HostGroupTreeNode[]> {
    const response = await apiClient.get(`${this.baseUrl}/groups/tree`);
    return response.data;
  }

  /**
   * 📄 获取主机组详情
   */
  async getGroup(groupId: number): Promise<HostGroup> {
    const response = await apiClient.get(`${this.baseUrl}/groups/${groupId}`);
    return response.data;
  }

  /**
   * ➕ 创建主机组
   */
  async createGroup(groupData: HostGroupCreate): Promise<HostGroup> {
    const response = await apiClient.post(`${this.baseUrl}/groups`, groupData);
    return response.data;
  }

  /**
   * ✏️ 更新主机组
   */
  async updateGroup(groupId: number, groupData: HostGroupUpdate): Promise<HostGroup> {
    const response = await apiClient.put(`${this.baseUrl}/groups/${groupId}`, groupData);
    return response.data;
  }

  /**
   * 🗑️ 删除主机组
   */
  async deleteGroup(groupId: number, force: boolean = false): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/groups/${groupId}`, { 
      params: { force } 
    });
  }

  /**
   * 🔧 更新主机组变量
   */
  async updateGroupVariables(groupId: number, variables: Record<string, any>): Promise<HostGroup> {
    const response = await apiClient.put(`${this.baseUrl}/groups/${groupId}/variables`, { variables });
    return response.data;
  }

  /**
   * 🏓 测试主机组连接
   */
  async pingGroup(groupName: string): Promise<GroupPingResult> {
    const response = await apiClient.post(`${this.baseUrl}/groups/${groupName}/ping`);
    return response.data;
  }

  // 📊 统计和管理方法

  /**
   * 📊 获取Inventory统计信息
   */
  async getStats(): Promise<InventoryStats> {
    const response = await apiClient.get(`${this.baseUrl}/stats`);
    return response.data;
  }

  /**
   * 📤 生成Inventory数据
   */
  async generateInventory(format: 'json' | 'yaml' | 'ini' = 'json'): Promise<any> {
    const response = await apiClient.get(`${this.baseUrl}/generate`, {
      params: { format_type: format }
    });
    return response.data;
  }

  /**
   * 📥 导出Inventory
   */
  async exportInventory(format: 'ini' | 'yaml' | 'json' = 'ini'): Promise<string> {
    const response = await apiClient.post(`${this.baseUrl}/export`, { format });
    return response.data;
  }

  /**
   * 📤 导入Inventory
   */
  async importInventory(content: string, format: 'ini' | 'yaml' | 'json' = 'ini', mergeMode: 'replace' | 'merge' | 'append' = 'replace'): Promise<{
    success: boolean;
    imported_hosts: number;
    imported_groups: number;
    message: string;
  }> {
    const response = await apiClient.post(`${this.baseUrl}/import`, {
      content,
      format,
      merge_mode: mergeMode
    });
    return response.data;
  }

  /**
   * 📁 通过文件导入Inventory
   */
  async importInventoryFile(file: File, format: 'ini' | 'yaml' | 'json' = 'ini', mergeMode: 'replace' | 'merge' | 'append' = 'replace'): Promise<{
    success: boolean;
    filename: string;
    imported_hosts: number;
    imported_groups: number;
    message: string;
  }> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post(`${this.baseUrl}/import/file`, formData, {
      params: { format_type: format, merge_mode: mergeMode },
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  /**
   * 📜 获取主机的执行历史
   */
  async getHostExecutionHistory(hostname: string, limit: number = 5): Promise<ExecutionHistory[]> {
    try {
      const response = await apiClient.get(`/execution/host/${hostname}/history`, {
        params: { limit }
      });
      return response.data.executions || [];
    } catch (error) {
      console.error('获取主机执行历史失败:', error);
      return [];
    }
  }
}

// 🎯 导出服务实例
export const inventoryService = new InventoryService();