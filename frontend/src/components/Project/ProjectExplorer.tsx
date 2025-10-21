/**
 * 📁 项目浏览器组件
 */

import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { motion } from 'framer-motion';
import {
  FolderIcon,
  PlusIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { FileTreeView } from './FileTreeView';
import { projectService } from '../../services/projectService';
import type { Project, FileNode } from '../../types/project';

interface ProjectExplorerProps {
  projectId?: number;
  onFileSelect?: (file: FileNode) => void;
  onProjectChange?: (project: Project) => void;
}

export const ProjectExplorer: React.FC<ProjectExplorerProps> = ({
  projectId,
  onFileSelect,
  onProjectChange,
}) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [fileTree, setFileTree] = useState<FileNode | null>(null);
  const [selectedPath, setSelectedPath] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [showNewFileDialog, setShowNewFileDialog] = useState(false);
  const [newFileName, setNewFileName] = useState('');

  // 使用 ref 跟踪是否已经加载过
  const hasLoadedRef = React.useRef(false);

  // 加载项目列表
  useEffect(() => {
    // 防止重复加载
    if (!hasLoadedRef.current) {
      hasLoadedRef.current = true;
      loadProjects();
    }
  }, []);

  // 当projectId变化时，加载对应项目
  useEffect(() => {
    if (projectId) {
      loadProject(projectId);
    }
  }, [projectId]);

  const loadProjects = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await projectService.getProjects();
      setProjects(data.projects);
      
      // 如果有项目且没有选中项目，选中第一个
      if (data.projects.length > 0 && !selectedProject) {
        await loadProject(data.projects[0].id);
      } else if (data.projects.length === 0) {
        setError('暂无项目，请先创建一个项目');
      }
    } catch (err: any) {
      console.error('加载项目列表失败:', err);
      setError(err.response?.data?.detail || '加载项目列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadProject = async (id: number) => {
    // 防止重复加载同一个项目
    if (selectedProject?.id === id && fileTree) {
      return;
    }

    try {
      setLoading(true);
      setError('');
      
      // 加载项目详情
      const project = await projectService.getProject(id);
      setSelectedProject(project);
      
      if (onProjectChange) {
        onProjectChange(project);
      }
      
      // 加载文件树
      const structure = await projectService.getProjectFiles(id);
      setFileTree(structure.structure);
    } catch (err: any) {
      console.error('加载项目失败:', err);
      const errorMsg = err.response?.data?.detail || err.message || '加载项目失败';
      setError(errorMsg);
      // 清空文件树
      setFileTree(null);
    } finally {
      setLoading(false);
    }
  };

  const handleProjectSelect = async (project: Project) => {
    await loadProject(project.id);
  };

  const handleFileClick = (node: FileNode) => {
    setSelectedPath(node.path);
    
    if (node.type === 'file' && onFileSelect) {
      onFileSelect(node);
    }
  };

  const handleRefresh = async () => {
    if (selectedProject) {
      await loadProject(selectedProject.id);
    }
  };

  const handleNewFile = () => {
    if (!selectedProject) {
      alert('请先选择一个项目');
      return;
    }
    setShowNewFileDialog(true);
  };

  const handleCreateFile = async () => {
    if (!selectedProject || !newFileName.trim()) {
      return;
    }

    try {
      setLoading(true);
      
      // 创建新文件（空内容）
      await projectService.writeFile(selectedProject.id, newFileName.trim(), '');
      
      // 刷新文件树
      await loadProject(selectedProject.id);
      
      // 重置状态
      setShowNewFileDialog(false);
      setNewFileName('');
    } catch (err: any) {
      alert(err.response?.data?.detail || '创建文件失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-white/10 backdrop-blur-md rounded-2xl border border-white/20">
      {/* 头部 */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <div className="flex items-center gap-2">
          <FolderIcon className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">项目浏览器</h3>
        </div>
        
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleRefresh}
            className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
            title="刷新"
          >
            <ArrowPathIcon className="w-4 h-4 text-white" />
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleNewFile}
            className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
            title="新建文件"
            disabled={!selectedProject}
          >
            <PlusIcon className="w-4 h-4 text-white" />
          </motion.button>
        </div>
      </div>

      {/* 项目选择器 */}
      <div className="p-4 border-b border-white/10">
        <select
          value={selectedProject?.id || ''}
          onChange={(e) => {
            const project = projects.find((p) => p.id === Number(e.target.value));
            if (project) {
              handleProjectSelect(project);
            }
          }}
          className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white
                     focus:outline-none focus:ring-2 focus:ring-blue-400/50"
        >
          <option value="" disabled>
            选择项目
          </option>
          {projects.map((project) => (
            <option key={project.id} value={project.id} className="bg-gray-800">
              {project.display_name || project.name}
            </option>
          ))}
        </select>
      </div>

      {/* 文件树 */}
      <div className="flex-1 overflow-y-auto p-2">
        {loading && (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-500/20 border border-red-500/30 rounded-lg">
            <p className="text-red-200 text-sm">{error}</p>
          </div>
        )}

        {!loading && !error && fileTree && (
          <FileTreeView
            node={fileTree}
            onNodeClick={handleFileClick}
            selectedPath={selectedPath}
          />
        )}

        {!loading && !error && !fileTree && (
          <div className="flex flex-col items-center justify-center h-32 text-gray-400">
            <FolderIcon className="w-12 h-12 mb-2" />
            <p className="text-sm">选择一个项目开始</p>
          </div>
        )}
      </div>

      {/* 新建文件对话框 - 使用 Portal 渲染到 body */}
      {showNewFileDialog && createPortal(
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[9999]"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setShowNewFileDialog(false);
              setNewFileName('');
            }
          }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-6 w-96 max-w-[90vw]"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-xl font-semibold text-white mb-4">📄 新建文件</h3>
            
            <div className="mb-4">
              <label className="block text-sm text-gray-300 mb-2">
                文件路径（相对于项目根目录）
              </label>
              <input
                type="text"
                value={newFileName}
                onChange={(e) => setNewFileName(e.target.value)}
                placeholder="例如: playbooks/site.yml"
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white
                         placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-400/50"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleCreateFile();
                  } else if (e.key === 'Escape') {
                    setShowNewFileDialog(false);
                    setNewFileName('');
                  }
                }}
                autoFocus
              />
              <p className="text-xs text-gray-400 mt-1">
                💡 提示：可以包含目录路径，系统会自动创建所需目录
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleCreateFile}
                disabled={!newFileName.trim() || loading}
                className="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500
                         rounded-lg text-white font-medium transition-colors"
              >
                {loading ? '创建中...' : '创建'}
              </button>
              <button
                onClick={() => {
                  setShowNewFileDialog(false);
                  setNewFileName('');
                }}
                className="flex-1 px-4 py-2 bg-white/10 hover:bg-white/20
                         rounded-lg text-white font-medium transition-colors"
              >
                取消
              </button>
            </div>
          </motion.div>
        </div>,
        document.body
      )}
    </div>
  );
};
