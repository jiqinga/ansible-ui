/**
 * 📦 项目管理服务
 */

import apiClient from './apiClient';
import type {
  Project,
  ProjectCreate,
  ProjectUpdate,
  ProjectStructure,
  ProjectValidation,
  Role,
  RoleCreate,
  RoleUpdate,
  RoleStructure,
} from '../types/project';

// ==================== 项目管理 ====================

export const projectService = {
  /**
   * 获取项目列表
   */
  async getProjects(skip = 0, limit = 100): Promise<{ projects: Project[]; total: number }> {
    const response = await apiClient.get('/projects', { params: { skip, limit } });
    return response.data;
  },

  /**
   * 创建项目
   */
  async createProject(data: ProjectCreate): Promise<Project> {
    const response = await apiClient.post('/projects', data);
    return response.data;
  },

  /**
   * 获取项目详情
   */
  async getProject(projectId: number): Promise<Project> {
    const response = await apiClient.get(`/projects/${projectId}`);
    return response.data;
  },

  /**
   * 更新项目
   */
  async updateProject(projectId: number, data: ProjectUpdate): Promise<Project> {
    const response = await apiClient.put(`/projects/${projectId}`, data);
    return response.data;
  },

  /**
   * 删除项目
   */
  async deleteProject(projectId: number, deleteFiles = false): Promise<void> {
    await apiClient.delete(`/projects/${projectId}`, { params: { delete_files: deleteFiles } });
  },

  /**
   * 获取项目文件树
   */
  async getProjectFiles(projectId: number, path = '', maxDepth = 10): Promise<ProjectStructure> {
    const response = await apiClient.get(`/projects/${projectId}/files`, {
      params: { path, max_depth: maxDepth },
    });
    return response.data;
  },

  /**
   * 读取文件内容
   */
  async readFile(projectId: number, path: string): Promise<string> {
    const response = await apiClient.get(`/projects/${projectId}/files/content`, { params: { path } });
    return response.data.content;
  },

  /**
   * 写入文件内容
   */
  async writeFile(projectId: number, path: string, content: string): Promise<void> {
    await apiClient.post(`/projects/${projectId}/files/content`, { path, content });
  },

  /**
   * 创建目录
   */
  async createDirectory(projectId: number, path: string): Promise<void> {
    await apiClient.post(`/projects/${projectId}/files/directory`, { path });
  },

  /**
   * 移动文件
   */
  async moveFile(projectId: number, source: string, destination: string): Promise<void> {
    await apiClient.post(`/projects/${projectId}/files/move`, { source, destination });
  },

  /**
   * 删除文件
   */
  async deleteFile(projectId: number, path: string): Promise<void> {
    await apiClient.delete(`/projects/${projectId}/files`, { params: { path } });
  },

  /**
   * 验证项目结构
   */
  async validateProject(projectId: number): Promise<ProjectValidation> {
    const response = await apiClient.post(`/projects/${projectId}/validate`);
    return response.data;
  },
};

// ==================== Role管理 ====================

export const roleService = {
  /**
   * 获取Role列表
   */
  async getRoles(projectId?: number, skip = 0, limit = 100): Promise<{ roles: Role[]; total: number }> {
    const response = await apiClient.get('/roles', {
      params: { project_id: projectId, skip, limit },
    });
    return response.data;
  },

  /**
   * 创建Role
   */
  async createRole(data: RoleCreate): Promise<Role> {
    const response = await apiClient.post('/roles', data);
    return response.data;
  },

  /**
   * 获取Role详情
   */
  async getRole(roleId: number): Promise<Role> {
    const response = await apiClient.get(`/roles/${roleId}`);
    return response.data;
  },

  /**
   * 更新Role
   */
  async updateRole(roleId: number, data: RoleUpdate): Promise<Role> {
    const response = await apiClient.put(`/roles/${roleId}`, data);
    return response.data;
  },

  /**
   * 删除Role
   */
  async deleteRole(roleId: number, deleteFiles = false): Promise<void> {
    await apiClient.delete(`/roles/${roleId}`, { params: { delete_files: deleteFiles } });
  },

  /**
   * 获取Role结构
   */
  async getRoleStructure(roleId: number): Promise<RoleStructure> {
    const response = await apiClient.get(`/roles/${roleId}/structure`);
    return response.data;
  },

  /**
   * 获取Role文件列表
   */
  async getRoleFiles(roleId: number): Promise<{ role_name: string; files: any[] }> {
    const response = await apiClient.get(`/roles/${roleId}/files`);
    return response.data;
  },
};
