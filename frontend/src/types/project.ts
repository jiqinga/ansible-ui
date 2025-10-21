/**
 * 📦 项目相关类型定义
 */

export interface Project {
  id: number;
  name: string;
  display_name?: string;
  description?: string;
  project_type: 'standard' | 'simple' | 'custom' | 'role-based';
  ansible_cfg_relative_path: string;
  created_at: string;
  updated_at: string;
  created_by?: number;
}

export interface ProjectCreate {
  name: string;
  display_name?: string;
  description?: string;
  project_type: 'standard' | 'simple' | 'custom' | 'role-based';
  ansible_cfg_relative_path?: string;
  template?: string;
}

export interface ProjectUpdate {
  display_name?: string;
  description?: string;
  ansible_cfg_relative_path?: string;
}

export interface FileNode {
  name: string;
  type: 'file' | 'directory';
  path: string;
  size?: number;
  children?: FileNode[];
}

export interface ProjectStructure {
  project: Project;
  structure: FileNode;
}

export interface ProjectValidation {
  is_valid: boolean;
  project_type: string;
  missing_directories: string[];
  missing_files: string[];
  warnings: string[];
  structure: Record<string, any>;
}

export interface Role {
  id: number;
  project_id: number;
  name: string;
  description?: string;
  relative_path: string;
  structure_metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface RoleCreate {
  project_id: number;
  name: string;
  description?: string;
  template?: 'basic' | 'full' | 'minimal';
}

export interface RoleUpdate {
  description?: string;
}

export interface RoleDirectory {
  name: string;
  exists: boolean;
  files: string[];
}

export interface RoleStructure {
  role_name: string;
  directories: Record<string, RoleDirectory>;
}

export interface EditorTab {
  id: string;
  title: string;
  path: string;
  content: string;
  isDirty: boolean;
  language?: string;
}
